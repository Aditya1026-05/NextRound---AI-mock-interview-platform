import structlog

from app.core.observability import log_operation
from app.llm.orchestrator import LLMOrchestrator
from app.models.resume.resume import Resume
from app.prompts.resume import CANDIDATE_PROFILE_SYSTEM_PROMPT
from app.schemas.resume.ai import CandidateProfileResponse

logger = structlog.get_logger()


class CandidateProfileService:
    """Service responsible for generating reusable technical candidate profiles using active LLM provider."""

    def __init__(self):
        self.orchestrator = LLMOrchestrator()

    @log_operation(category="SERVICE", name="Candidate Profile Generation")
    async def generate_candidate_profile(
        self, resume: Resume
    ) -> CandidateProfileResponse:
        """Analyze a normalized Resume ORM object and generate the CandidateProfileResponse."""
        # Format the normalized details into text representation
        edu_details = []
        for edu in resume.education:
            edu_details.append(
                f"- Institution: {edu.institution}, Degree: {edu.degree or 'N/A'}, "
                f"Field of Study: {edu.field_of_study or 'N/A'}, "
                f"Dates: {edu.start_date or 'N/A'} to {edu.end_date or 'N/A'}, "
                f"GPA: {edu.gpa or 'N/A'}"
            )
        edu_str = "\n".join(edu_details)

        exp_details = []
        for exp in resume.work_experiences:
            exp_details.append(
                f"- Company: {exp.company}, Role: {exp.role}, Location: {exp.location or 'N/A'}, "
                f"Dates: {exp.start_date or 'N/A'} to {exp.end_date or 'Present'}, "
                f"Current: {exp.is_current}\n"
                f"  Description: {exp.description or 'N/A'}"
            )
        exp_str = "\n".join(exp_details)

        proj_details = []
        for proj in resume.projects:
            proj_details.append(
                f"- Title: {proj.title}, Role: {proj.role or 'N/A'}, Link: {proj.url or 'N/A'}\n"
                f"  Description: {proj.description or 'N/A'}"
            )
        proj_str = "\n".join(proj_details)

        skills_str = ", ".join([s.name for s in resume.skills if s])

        user_prompt = (
            f"Candidate Name: {resume.parsed_json.get('full_name', 'N/A') if resume.parsed_json else 'N/A'}\n\n"
            f"--- EDUCATION ---\n{edu_str}\n\n"
            f"--- WORK EXPERIENCES ---\n{exp_str}\n\n"
            f"--- PROJECTS ---\n{proj_str}\n\n"
            f"--- SKILLS ---\n{skills_str}\n\n"
            f"--- OTHER ---\n"
            f"Certifications: {', '.join(resume.parsed_json.get('certifications', [])) if resume.parsed_json else 'N/A'}\n"
            f"Achievements: {', '.join(resume.parsed_json.get('achievements', [])) if resume.parsed_json else 'N/A'}\n"
        )

        logger.info("Generating candidate profile with LLM", resume_id=resume.id)

        profile_obj = await self.orchestrator.structured_completion(
            profile="candidate_profile",
            system_prompt=CANDIDATE_PROFILE_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=CandidateProfileResponse,
        )

        return profile_obj
