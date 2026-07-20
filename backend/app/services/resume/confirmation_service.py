import re
import uuid
from datetime import date, datetime

from fastapi import HTTPException, status
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai.candidate_profile import CandidateProfile
from app.models.resume.education import Education
from app.models.resume.project import Project
from app.models.resume.resume import Resume
from app.models.resume.resume_skill import ResumeSkill
from app.models.resume.skill import Skill
from app.models.resume.skill_category import SkillCategory
from app.models.resume.work_experience import WorkExperience
from app.schemas.resume.ai import ResumeConfirmationRequest
from app.services.resume.profile_service import CandidateProfileService
from app.shared.enums.resume import ResumeStatus


def parse_date(date_str: str | None) -> date | None:
    if not date_str:
        return None
    if isinstance(date_str, date):
        return date_str
    
    cleaned = str(date_str).strip()
    if not cleaned or cleaned.lower() in ("present", "current", "none", "null"):
        return None

    # Try YYYY-MM-DD, YYYY-MM, YYYY
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
    
    # MM/YYYY
    match = re.search(r"(\d{1,2})/(\d{4})", cleaned)
    if match:
        try:
            return date(int(match.group(2)), int(match.group(1)), 1)
        except ValueError:
            pass
            
    return None

def parse_gpa(gpa_val) -> float | None:
    if gpa_val is None or gpa_val == "":
        return None
    try:
        return float(gpa_val)
    except (ValueError, TypeError):
        return None


class ResumeConfirmationService:
    """Orchestration service for finalizing resumes and generating Candidate Profiles."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.profile_service = CandidateProfileService()

    async def confirm_resume(
        self,
        resume_id: uuid.UUID,
        user_id: uuid.UUID,
        request: ResumeConfirmationRequest,
    ) -> Resume:
        """Atomically validate, normalize, switch primary status, generate and upsert AI candidate profile, and finalize."""
        # 1. Fetch resume and check ownership
        stmt = select(Resume).filter(
            Resume.id == resume_id, Resume.user_id == user_id
        )
        resume = await self.db.scalar(stmt)
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found",
            )

        # 2. Check Idempotency (already CONFIRMED)
        if resume.status == ResumeStatus.CONFIRMED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Resume is already confirmed",
            )

        # 3. Check status is REVIEW_PENDING
        if resume.status != ResumeStatus.REVIEW_PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Resume confirmation not allowed for status: {resume.status}",
            )

        # 4. Perform operations inside savepoint transaction
        try:
            async with self.db.begin_nested():
                # A. Clean up preexisting child tables linked to this resume
                await self.db.execute(delete(Education).where(Education.resume_id == resume_id))
                await self.db.execute(delete(WorkExperience).where(WorkExperience.resume_id == resume_id))
                await self.db.execute(delete(Project).where(Project.resume_id == resume_id))
                await self.db.execute(delete(ResumeSkill).where(ResumeSkill.resume_id == resume_id))
                await self.db.flush()

                # B. Save updated parsed_json as a snapshot
                dumped_req = request.model_dump(mode="json")
                resume.parsed_json = {
                    "full_name": resume.parsed_json.get("full_name", "") if resume.parsed_json else "",
                    "summary": request.summary,
                    "education": dumped_req.get("education", []),
                    "work_experiences": dumped_req.get("work_experiences", []),
                    "projects": dumped_req.get("projects", []),
                    "skills": dumped_req.get("skills", []),
                    "certifications": request.certifications,
                    "achievements": request.achievements,
                    "confidence_score": resume.parsed_json.get("confidence_score", 1.0) if resume.parsed_json else 1.0,
                    "parser_provider": resume.parsed_json.get("parser_provider", "manual") if resume.parsed_json else "manual",
                    "parser_model": resume.parsed_json.get("parser_model", "manual") if resume.parsed_json else "manual",
                    "parser_version": resume.parsed_json.get("parser_version", "1.0") if resume.parsed_json else "1.0",
                }

                # C. Insert normalized records
                # Education
                for edu in request.education:
                    edu_db = Education(
                        resume_id=resume_id,
                        institution=edu.institution,
                        degree=edu.degree,
                        field_of_study=edu.field_of_study,
                        start_date=parse_date(edu.start_date),
                        end_date=parse_date(edu.end_date),
                        gpa=parse_gpa(edu.gpa),
                    )
                    self.db.add(edu_db)

                # Work experiences
                for exp in request.work_experiences:
                    exp_db = WorkExperience(
                        resume_id=resume_id,
                        company=exp.company,
                        role=exp.role,
                        location=exp.location,
                        description=exp.description,
                        start_date=parse_date(exp.start_date),
                        end_date=parse_date(exp.end_date),
                        is_current=exp.is_current,
                    )
                    self.db.add(exp_db)

                # Projects
                for proj in request.projects:
                    proj_db = Project(
                        resume_id=resume_id,
                        title=proj.title,
                        description=proj.description,
                        role=proj.role,
                        url=str(proj.url) if proj.url else None,
                    )
                    self.db.add(proj_db)

                # Skill Normalization (Trim, Lowercase, Get/Create category, lookup & link)
                stmt_cat = select(SkillCategory).filter(SkillCategory.name == "General")
                category = await self.db.scalar(stmt_cat)
                if not category:
                    category = SkillCategory(name="General")
                    self.db.add(category)
                    await self.db.flush()
                category_id = category.id

                seen_skills = set()
                for skill_obj in request.skills:
                    cleaned_name = skill_obj.name.strip().lower()
                    if not cleaned_name or cleaned_name in seen_skills:
                        continue
                    seen_skills.add(cleaned_name)

                    stmt_s = select(Skill).filter(Skill.name == cleaned_name)
                    skill = await self.db.scalar(stmt_s)
                    if not skill:
                        skill = Skill(name=cleaned_name, category_id=category_id)
                        self.db.add(skill)
                        await self.db.flush()

                    # Bind using ResumeSkill
                    resume_skill = ResumeSkill(
                        resume_id=resume_id,
                        skill_id=skill.id
                    )
                    self.db.add(resume_skill)

                # D. Switch primary status
                # Unset other primary resumes
                await self.db.execute(
                    update(Resume)
                    .where(Resume.user_id == user_id, Resume.id != resume_id)
                    .values(is_primary=False)
                )
                resume.is_primary = True

                # Flush all items so profile generation can query child lists
                await self.db.flush()

                # E. Eager load relation tables
                await self.db.refresh(resume, ["education", "work_experiences", "projects", "skills"])

                # F. Generate candidate profile
                profile_response = await self.profile_service.generate_candidate_profile(resume)

                # G. Upsert Candidate Profile
                stmt_cp = select(CandidateProfile).filter(CandidateProfile.resume_id == resume_id)
                cp_rec = await self.db.scalar(stmt_cp)
                if cp_rec:
                    cp_rec.profile_json = profile_response.model_dump()
                else:
                    cp_rec = CandidateProfile(
                        resume_id=resume_id,
                        user_id=user_id,
                        profile_json=profile_response.model_dump(),
                    )
                    self.db.add(cp_rec)

                # H. Set status to CONFIRMED
                resume.status = ResumeStatus.CONFIRMED

            # Commit the entire transaction atomically
            await self.db.commit()
            await self.db.refresh(resume)
            return resume

        except Exception as e:
            # We raise the exception, and the active nested transaction will automatically rollback its savepoint
            raise e
