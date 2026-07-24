import uuid
from typing import Optional
from pydantic import BaseModel
from app.shared.enums import ExecutionStatus


class ProviderTestCaseResult(BaseModel):
    test_case_id: uuid.UUID
    is_sample: bool
    passed: bool
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    execution_time_ms: Optional[float] = None
    memory_kb: Optional[int] = None
    error_message: Optional[str] = None
    actual_output: Optional[str] = None


class ProviderExecutionResult(BaseModel):
    status: ExecutionStatus
    passed_tests: int
    total_tests: int
    peak_time_ms: float
    peak_memory_kb: int
    compile_output: Optional[str] = None
    test_cases: list[ProviderTestCaseResult]
    provider_submission_token: Optional[str] = None
    provider_version: Optional[str] = None
    language_version: Optional[str] = None


class TestCaseResultSchema(BaseModel):
    test_case_id: uuid.UUID
    is_sample: bool
    passed: bool
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    execution_time_ms: Optional[float] = None
    memory_kb: Optional[int] = None
    error_message: Optional[str] = None
    # Exposed only for visible (sample) test cases
    input: Optional[str] = None
    expected_output: Optional[str] = None
    actual_output: Optional[str] = None


class ExecutionResultSchema(BaseModel):
    status: str
    passed_tests: int
    total_tests: int
    peak_time_ms: float
    peak_memory_kb: int
    compile_output: Optional[str] = None
    test_cases: list[TestCaseResultSchema]
