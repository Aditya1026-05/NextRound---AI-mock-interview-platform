from typing import Dict, List
from app.models.interview.question_test_case import QuestionTestCase
from app.schemas.interview.execution import ExecutionResultSchema, TestCaseResultSchema, ProviderExecutionResult


class ExecutionResultMapper:
    """Decoupled result mapper translating ProviderExecutionResult to standard schemas."""

    @staticmethod
    def to_schema(
        provider_result: ProviderExecutionResult,
        test_cases: List[QuestionTestCase]
    ) -> ExecutionResultSchema:
        # Create map of test cases for easy lookup
        case_map: Dict[str, QuestionTestCase] = {
            str(tc.id): tc for tc in test_cases
        }

        schema_cases = []
        for ptr in provider_result.test_cases:
            tc = case_map.get(str(ptr.test_case_id))

            schema_cases.append(TestCaseResultSchema(
                test_case_id=ptr.test_case_id,
                is_sample=ptr.is_sample,
                passed=ptr.passed,
                stdout=ptr.stdout,
                stderr=ptr.stderr,
                execution_time_ms=ptr.execution_time_ms,
                memory_kb=ptr.memory_kb,
                error_message=ptr.error_message,
                input=tc.input if tc else None,
                expected_output=tc.expected_output if tc else None,
                actual_output=ptr.actual_output
            ))

        return ExecutionResultSchema(
            status=provider_result.status.value,
            passed_tests=provider_result.passed_tests,
            total_tests=provider_result.total_tests,
            peak_time_ms=provider_result.peak_time_ms,
            peak_memory_kb=provider_result.peak_memory_kb,
            compile_output=provider_result.compile_output,
            test_cases=schema_cases
        )
