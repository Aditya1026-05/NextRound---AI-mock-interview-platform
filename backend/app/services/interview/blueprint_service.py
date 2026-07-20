import structlog
from pydantic import BaseModel
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.observability import bind_context, log_operation, step_completed
from app.llm.orchestrator import LLMOrchestrator
from app.models.interview.interview_blueprint import InterviewBlueprint
from app.models.interview.interview_session import InterviewSession
from app.prompts.interview import BLUEPRINT_SYSTEM_PROMPT

logger = structlog.get_logger()


class BlueprintSectionSchema(BaseModel):
    """Pydantic schema representing a single section in the interview blueprint."""

    name: str
    duration: int


class BlueprintResponseSchema(BaseModel):
    """Pydantic schema representing the complete AI response for interview blueprint."""

    title: str
    estimated_duration: int
    sections: list[BlueprintSectionSchema]


class BlueprintService:
    """Service responsible for generating and persisting interview blueprints using LLM Orchestrator."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.orchestrator = LLMOrchestrator()

    @log_operation(category="LLM", name="Blueprint Generation")
    async def create_blueprint(
        self, session: InterviewSession, candidate_profile_summary: str | None
    ) -> InterviewBlueprint:
        """Construct the prompt, invoke LLM Orchestrator, validate response, persist and return the blueprint."""
        category = session.interview_category
        role = session.role
        duration = session.duration_minutes
        difficulty = session.difficulty

        # Build prompt
        user_prompt = (
            f"Interview Category: {category.value}\n"
            f"Target Role: {role.value if role else 'N/A'}\n"
            f"Requested Total Duration: {duration} minutes\n"
            f"Difficulty: {difficulty.value}\n"
        )
        if candidate_profile_summary:
            user_prompt += (
                f"\nCandidate Technical Profile Summary:\n{candidate_profile_summary}\n"
            )

        logger.info(
            "Generating Interview Blueprint\n"
            "Profile: interview_blueprint\n"
            f"Category: {category.value.capitalize()}\n"
            f"Role: {role.value.capitalize() if role else 'N/A'}\n"
            f"Duration: {duration} minutes",
            category="LLM",
        )

        # Call orchestrator
        blueprint_obj: BlueprintResponseSchema = (
            await self.orchestrator.structured_completion(
                profile="interview_blueprint",
                system_prompt=BLUEPRINT_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                response_model=BlueprintResponseSchema,
            )
        )
        step_completed("LLM", "Blueprint generated")

        # Self-correction: Adjust section durations to match the requested duration exactly
        total_sections_duration = sum(sec.duration for sec in blueprint_obj.sections)
        diff = duration - total_sections_duration
        if diff != 0 and len(blueprint_obj.sections) > 0:
            logger.warn(
                "Blueprint duration mismatch. Applying self-correction to last section.",
                total_sections_duration=total_sections_duration,
                requested_duration=duration,
                diff=diff,
            )
            blueprint_obj.sections[-1].duration += diff
            blueprint_obj.estimated_duration = duration

        # Resolve active model from the model registry metadata
        registry = self.orchestrator.registry
        try:
            profile_cfg = registry.get_profile("interview_blueprint")
            primary_model_cfg = registry.get_model(profile_cfg.primary)
            resolved_model = primary_model_cfg.model
        except Exception as e:
            logger.error("Failed to resolve model from registry", error=str(e))
            resolved_model = "unknown"

        # Make generation repeatable: delete any pre-existing blueprint for this session first
        stmt = delete(InterviewBlueprint).where(
            InterviewBlueprint.session_id == session.id
        )
        await self.db.execute(stmt)
        await self.db.flush()

        # Build blueprint dict representation
        blueprint_json_data = {
            "title": blueprint_obj.title,
            "estimated_duration": blueprint_obj.estimated_duration,
            "sections": [sec.model_dump() for sec in blueprint_obj.sections],
        }

        # Create and persist the child model record
        blueprint_db = InterviewBlueprint(
            session_id=session.id,
            title=blueprint_obj.title,
            estimated_duration=blueprint_obj.estimated_duration,
            blueprint_json=blueprint_json_data,
            generated_by_profile="interview_blueprint",
            generated_model=resolved_model,
        )

        self.db.add(blueprint_db)
        await self.db.flush()
        bind_context(blueprint_id=str(blueprint_db.id))
        step_completed("DATABASE", "Saving Interview Blueprint")
        step_completed("LLM", "Interview blueprint successfully persisted")

        return blueprint_db
