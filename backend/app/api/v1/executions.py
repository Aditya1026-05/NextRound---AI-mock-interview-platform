import uuid
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.providers import get_db
from app.shared.enums import SubmissionSource, ExecutionType
from app.models.interview.code_submission import CodeSubmission
from app.schemas.interview.execution import ExecutionResultSchema, TestCaseResultSchema
from app.services.interview.code_execution_service import CodeExecutionService

router = APIRouter()


class CodeExecutionRequest(BaseModel):
    code: str
    language: str
    coding_problem_id: uuid.UUID
    execution_type: ExecutionType
    submission_source: SubmissionSource
    session_id: Optional[uuid.UUID] = None
    is_final_submission: bool = False


class CodeSubmissionResponse(BaseModel):
    id: uuid.UUID
    session_id: Optional[uuid.UUID] = None
    coding_problem_id: uuid.UUID
    problem_version: int
    language: str
    submitted_code: str
    status: str
    attempt_number: int
    execution_type: ExecutionType
    is_final_submission: bool
    submission_source: SubmissionSource
    passed_tests: int
    total_tests: int
    execution_time_ms: float
    memory_kb: int
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    compile_output: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


def sanitize_execution_result(result: ExecutionResultSchema) -> ExecutionResultSchema:
    """Scrubs input, output, stdout, and stderr for hidden test cases to protect academic integrity."""
    sanitized_cases = []
    for case in result.test_cases:
        if case.is_sample:
            sanitized_cases.append(case)
        else:
            sanitized_cases.append(TestCaseResultSchema(
                test_case_id=case.test_case_id,
                is_sample=False,
                passed=case.passed,
                execution_time_ms=case.execution_time_ms,
                memory_kb=case.memory_kb,
                error_message=case.error_message if not case.passed else None,
                input=None,
                expected_output=None,
                actual_output=None,
                stdout=None,
                stderr=None
            ))
    return ExecutionResultSchema(
        status=result.status,
        passed_tests=result.passed_tests,
        total_tests=result.total_tests,
        peak_time_ms=result.peak_time_ms,
        peak_memory_kb=result.peak_memory_kb,
        compile_output=result.compile_output,
        test_cases=sanitized_cases
    )


@router.post("", response_model=ExecutionResultSchema, status_code=status.HTTP_201_CREATED)
async def execute_code(
    payload: CodeExecutionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Executes candidate solution code against configured problem test cases, returning sanitized results."""
    service = CodeExecutionService()
    try:
        raw_result = await service.execute_submission(
            db=db,
            code=payload.code,
            language=payload.language,
            coding_problem_id=payload.coding_problem_id,
            execution_type=payload.execution_type,
            submission_source=payload.submission_source,
            session_id=payload.session_id,
            is_final_submission=payload.is_final_submission
        )
        await db.commit()
        return sanitize_execution_result(raw_result)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during execution: {e}"
        )


@router.get("/{submission_id}", response_model=CodeSubmissionResponse)
async def get_submission(
    submission_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Retrieves a historical execution submission attempt log."""
    stmt = select(CodeSubmission).where(CodeSubmission.id == submission_id)
    submission = await db.scalar(stmt)
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Code submission log not found."
        )
    return submission
