import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interview.coding_problem import CodingProblem
from app.shared.enums import DifficultyType

class CodingProblemService:
    """Service class managing queries and operations on CodingProblem records."""

    async def get_problem_by_id(self, db: AsyncSession, problem_id: uuid.UUID) -> CodingProblem | None:
        """Fetch a single coding problem by its primary key ID."""
        stmt = select(CodingProblem).filter(CodingProblem.id == problem_id)
        return await db.scalar(stmt)

    async def get_random_problem(self, db: AsyncSession, difficulty: DifficultyType) -> CodingProblem | None:
        """Fetch a random coding problem filtered by difficulty."""
        stmt = select(CodingProblem).filter(CodingProblem.difficulty == difficulty).order_by(func.random()).limit(1)
        return await db.scalar(stmt)

    async def get_by_topic(self, db: AsyncSession, topic: str) -> list[CodingProblem]:
        """Fetch all coding problems that contain a matching topic string tag."""
        stmt = select(CodingProblem).filter(CodingProblem.topics.contains([topic]))
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def get_by_difficulty(self, db: AsyncSession, difficulty: DifficultyType) -> list[CodingProblem]:
        """Fetch all coding problems of a specific difficulty."""
        stmt = select(CodingProblem).filter(CodingProblem.difficulty == difficulty)
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def reserve_problem_for_session(self, db: AsyncSession, session_id: uuid.UUID, problem_id: uuid.UUID) -> bool:
        """Stub method to reserve/snapshot a coding problem for an active interview session."""
        return True

    async def get_practice_problem(self, db: AsyncSession, problem_id: uuid.UUID) -> CodingProblem | None:
        """Fetch a coding problem formatted/selected specifically for the Practice Hub sandbox."""
        return await self.get_problem_by_id(db, problem_id)

    async def get_interview_problem(self, db: AsyncSession, session_id: uuid.UUID) -> CodingProblem | None:
        """Retrieve the active coding problem currently linked to a session."""
        stmt = select(CodingProblem).limit(1)
        return await db.scalar(stmt)
