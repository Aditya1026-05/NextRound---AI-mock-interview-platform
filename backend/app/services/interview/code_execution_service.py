import uuid
from typing import Optional, List
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.shared.enums import SubmissionSource, ExecutionType, ExecutionStatus
from app.models.interview.coding_problem import CodingProblem
from app.models.interview.language_template import LanguageTemplate
from app.models.interview.question_test_case import QuestionTestCase
from app.models.interview.code_submission import CodeSubmission
from app.schemas.interview.execution import ExecutionResultSchema
from app.services.interview.execution_assembler import ExecutionAssembler
from app.services.interview.judge0_language_registry import Judge0LanguageRegistry
from app.services.interview.code_execution_provider import ExecutionPayload
from app.services.interview.code_execution_provider_factory import CodeExecutionProviderFactory
from app.services.interview.execution_result_mapper import ExecutionResultMapper


class CodeExecutionService:
    """Core orchestration service coordinating assembly, execution, mapping, and persistence of code runs."""

    async def execute_submission(
        self,
        db: AsyncSession,
        code: str,
        language: str,
        coding_problem_id: uuid.UUID,
        execution_type: ExecutionType,
        submission_source: SubmissionSource,
        session_id: Optional[uuid.UUID] = None,
        is_final_submission: bool = False
    ) -> ExecutionResultSchema:
        # 1. Fetch coding problem details
        stmt_prob = select(CodingProblem).where(CodingProblem.id == coding_problem_id)
        problem = await db.scalar(stmt_prob)
        if not problem:
            raise ValueError(f"Coding Problem with ID {coding_problem_id} does not exist.")

        # 2. Fetch language templates/boilerplate
        stmt_temp = select(LanguageTemplate).where(LanguageTemplate.language == language)
        template = await db.scalar(stmt_temp)
        boilerplate = template.boilerplate_wrapper if template else None

        # Validate driver code existence for problem
        driver_template = problem.driver_templates.get(language)
        if not driver_template:
            # Fallback wrapper if no custom driver exists (helps keep basic scripts running)
            driver_template = "{CANDIDATE_CODE}"

        # 3. Fetch test cases
        stmt_cases = (
            select(QuestionTestCase)
            .where(QuestionTestCase.question_id == coding_problem_id)
            .order_by(QuestionTestCase.created_at)
        )
        result_cases = await db.execute(stmt_cases)
        test_cases: List[QuestionTestCase] = list(result_cases.scalars().all())

        if not test_cases:
            raise ValueError(f"No test cases registered for coding problem {coding_problem_id}.")

        # 4. Synthesizes runnable scripts via ExecutionAssembler (pure component)
        runnable_code = ExecutionAssembler.assemble(
            candidate_code=code,
            driver_template=driver_template,
            boilerplate_template=boilerplate
        )

        # 5. Determine attempt number
        stmt_count = (
            select(func.count(CodeSubmission.id))
            .where(CodeSubmission.coding_problem_id == coding_problem_id)
        )
        if session_id:
            stmt_count = stmt_count.where(CodeSubmission.session_id == session_id)
        attempt_count = await db.scalar(stmt_count) or 0
        attempt_number = attempt_count + 1

        # 6. Prepare provider execution payloads
        lang_id = Judge0LanguageRegistry.get_id(language)
        lang_version = Judge0LanguageRegistry.get_version(language)

        payloads = []
        for tc in test_cases:
            payloads.append(ExecutionPayload(
                test_case_id=tc.id,
                is_sample=tc.is_sample,
                source_code=runnable_code,
                language_id=lang_id,
                stdin=tc.input,
                expected_output=tc.expected_output,
                cpu_time_limit=tc.time_limit_ms / 1000.0,
                memory_limit=tc.memory_limit_kb / 1024.0
            ))

        # 7. Execute code runs via factory-resolved provider
        provider = CodeExecutionProviderFactory.get_provider(settings.CODE_EXECUTION_PROVIDER)
        provider_result = await provider.execute_batch(payloads)

        # 8. Decouple results mapping via ExecutionResultMapper
        schema_result = ExecutionResultMapper.to_schema(provider_result, test_cases)

        # 9. Handle final submission flag cleanup
        if is_final_submission and session_id:
            # Clear previous final flags for this session and problem
            await db.execute(
                update(CodeSubmission)
                .where(CodeSubmission.session_id == session_id)
                .where(CodeSubmission.coding_problem_id == coding_problem_id)
                .values(is_final_submission=False)
            )

        # 10. Record submission log in database
        # Calculate peak/first errors for logging
        logged_stdout = None
        logged_stderr = None
        if provider_result.status == ExecutionStatus.COMPILE_ERROR:
            logged_stdout = provider_result.compile_output
        elif provider_result.test_cases:
            # Log stdout/stderr of first failed test, or first general test case
            failed_cases = [c for c in provider_result.test_cases if not c.passed]
            target_case = failed_cases[0] if failed_cases else provider_result.test_cases[0]
            logged_stdout = target_case.stdout
            logged_stderr = target_case.stderr or target_case.error_message

        submission = CodeSubmission(
            session_id=session_id,
            coding_problem_id=coding_problem_id,
            problem_version=problem.version,
            language=language,
            submitted_code=code,
            status=provider_result.status.value,
            attempt_number=attempt_number,
            execution_type=execution_type,
            is_final_submission=is_final_submission,
            submission_source=submission_source,
            provider_name=settings.CODE_EXECUTION_PROVIDER,
            provider_version=provider_result.provider_version or lang_version,
            language_version=provider_result.language_version or lang_version,
            provider_submission_token=provider_result.provider_submission_token,
            passed_tests=provider_result.passed_tests,
            total_tests=provider_result.total_tests,
            execution_time_ms=provider_result.peak_time_ms,
            memory_kb=provider_result.peak_memory_kb,
            stdout=logged_stdout,
            stderr=logged_stderr,
            compile_output=provider_result.compile_output
        )
        db.add(submission)
        await db.flush()

        return schema_result
