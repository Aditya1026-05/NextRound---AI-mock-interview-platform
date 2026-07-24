import pytest
import uuid
from unittest.mock import AsyncMock, patch, MagicMock

from app.shared.enums import ExecutionStatus, ExecutionType, SubmissionSource
from app.models.interview.question_test_case import QuestionTestCase
from app.schemas.interview.execution import (
    ProviderExecutionResult,
    ProviderTestCaseResult,
    ExecutionResultSchema,
    TestCaseResultSchema,
)
from app.services.interview.execution_assembler import ExecutionAssembler
from app.services.interview.judge0_language_registry import Judge0LanguageRegistry
from app.services.interview.code_execution_provider_factory import CodeExecutionProviderFactory
from app.services.interview.judge0_code_execution_provider import Judge0CodeExecutionProvider
from app.services.interview.execution_result_mapper import ExecutionResultMapper
from app.api.v1.executions import sanitize_execution_result


def test_execution_assembler_synthesis():
    candidate_code = "def add(a, b): return a + b"
    driver_template = "assert add(2, 3) == 5\n{CANDIDATE_CODE}"
    boilerplate = "import sys"

    # With boilerplate
    result = ExecutionAssembler.assemble(candidate_code, driver_template, boilerplate)
    assert "import sys" in result
    assert "def add(a, b): return a + b" in result
    assert "assert add(2, 3) == 5" in result

    # Without boilerplate
    result_nb = ExecutionAssembler.assemble(candidate_code, driver_template)
    assert "def add(a, b): return a + b" in result_nb
    assert "assert add(2, 3) == 5" in result_nb
    assert "import sys" not in result_nb


def test_language_registry_caching():
    # Verify fallback registry resolves correctly
    assert Judge0LanguageRegistry.get_id("python") == 71
    assert Judge0LanguageRegistry.get_id("cpp") == 54
    assert Judge0LanguageRegistry.get_id("java") == 62
    assert Judge0LanguageRegistry.get_id("javascript") == 63
    assert Judge0LanguageRegistry.get_version("python") == "3.8.1"

    with pytest.raises(ValueError):
        Judge0LanguageRegistry.get_id("non_existent_lang")


@pytest.mark.asyncio
async def test_language_registry_dynamic_initialize():
    mock_languages = [
        {"id": 92, "name": "Python (3.11.0)"},
        {"id": 85, "name": "C++ (GCC 11.2.0)"},
    ]

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_languages

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response

        # Trigger dynamic initialization
        await Judge0LanguageRegistry.initialize()

        assert Judge0LanguageRegistry.get_id("python") == 92
        assert Judge0LanguageRegistry.get_version("python") == "Python (3.11.0)"
        assert Judge0LanguageRegistry.get_id("cpp") == 85
        assert Judge0LanguageRegistry.get_version("cpp") == "C++ (GCC 11.2.0)"




def test_factory_registry_resolution():
    provider = CodeExecutionProviderFactory.get_provider("judge0")
    assert isinstance(provider, Judge0CodeExecutionProvider)

    # Test custom registration
    class FakeProvider:
        pass

    CodeExecutionProviderFactory.register("fake", FakeProvider)
    retrieved = CodeExecutionProviderFactory.get_provider("fake")
    assert isinstance(retrieved, FakeProvider)


def test_execution_result_mapper():
    test_case_id_1 = uuid.uuid4()
    test_case_id_2 = uuid.uuid4()

    provider_result = ProviderExecutionResult(
        status=ExecutionStatus.WRONG_ANSWER,
        passed_tests=1,
        total_tests=2,
        peak_time_ms=120.5,
        peak_memory_kb=4500,
        compile_output="Some warnings",
        test_cases=[
            ProviderTestCaseResult(
                test_case_id=test_case_id_1,
                is_sample=True,
                passed=True,
                stdout="5",
                stderr="",
                execution_time_ms=50.0,
                memory_kb=2000,
                actual_output="5",
            ),
            ProviderTestCaseResult(
                test_case_id=test_case_id_2,
                is_sample=False,
                passed=False,
                stdout="wrong",
                stderr="some error",
                execution_time_ms=120.5,
                memory_kb=4500,
                actual_output="wrong",
            )
        ]
    )

    db_test_cases = [
        QuestionTestCase(
            id=test_case_id_1,
            question_id=uuid.uuid4(),
            input="2 3",
            expected_output="5",
            is_sample=True,
            is_hidden=False
        ),
        QuestionTestCase(
            id=test_case_id_2,
            question_id=uuid.uuid4(),
            input="4 5",
            expected_output="9",
            is_sample=False,
            is_hidden=True
        )
    ]

    mapped_schema = ExecutionResultMapper.to_schema(provider_result, db_test_cases)

    assert mapped_schema.status == "Wrong Answer"
    assert mapped_schema.passed_tests == 1
    assert mapped_schema.total_tests == 2
    assert mapped_schema.peak_time_ms == 120.5
    assert mapped_schema.peak_memory_kb == 4500
    assert mapped_schema.compile_output == "Some warnings"
    
    assert len(mapped_schema.test_cases) == 2
    tc1 = mapped_schema.test_cases[0]
    assert tc1.is_sample is True
    assert tc1.passed is True
    assert tc1.input == "2 3"
    assert tc1.expected_output == "5"
    assert tc1.actual_output == "5"

    tc2 = mapped_schema.test_cases[1]
    assert tc2.is_sample is False
    assert tc2.passed is False
    assert tc2.input == "4 5"
    assert tc2.expected_output == "9"
    assert tc2.actual_output == "wrong"


def test_sanitize_execution_result():
    test_case_id_1 = uuid.uuid4()
    test_case_id_2 = uuid.uuid4()

    raw_schema = ExecutionResultSchema(
        status="Wrong Answer",
        passed_tests=1,
        total_tests=2,
        peak_time_ms=120.0,
        peak_memory_kb=4000,
        test_cases=[
            TestCaseResultSchema(
                test_case_id=test_case_id_1,
                is_sample=True,
                passed=True,
                stdout="5",
                stderr="",
                execution_time_ms=40.0,
                memory_kb=2000,
                input="2 3",
                expected_output="5",
                actual_output="5"
            ),
            TestCaseResultSchema(
                test_case_id=test_case_id_2,
                is_sample=False,
                passed=False,
                stdout="wrong",
                stderr="some error",
                execution_time_ms=120.0,
                memory_kb=4000,
                error_message="Wrong Answer",
                input="4 5",
                expected_output="9",
                actual_output="wrong"
            )
        ]
    )

    sanitized = sanitize_execution_result(raw_schema)

    # Sample cases should keep all fields
    s_tc1 = sanitized.test_cases[0]
    assert s_tc1.is_sample is True
    assert s_tc1.passed is True
    assert s_tc1.input == "2 3"
    assert s_tc1.expected_output == "5"
    assert s_tc1.actual_output == "5"
    assert s_tc1.stdout == "5"
    assert s_tc1.stderr == ""

    # Hidden cases should be scrubbed
    s_tc2 = sanitized.test_cases[1]
    assert s_tc2.is_sample is False
    assert s_tc2.passed is False
    assert s_tc2.error_message == "Wrong Answer"
    assert s_tc2.input is None
    assert s_tc2.expected_output is None
    assert s_tc2.actual_output is None
    assert s_tc2.stdout is None
    assert s_tc2.stderr is None
