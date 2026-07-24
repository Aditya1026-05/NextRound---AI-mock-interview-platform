from abc import ABC, abstractmethod
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interview.interview_session import InterviewSession
from app.models.interview.interview_message import InterviewMessage
from app.shared.enums import DifficultyLevel

class BaseSectionStrategy(ABC):
    """Abstract base class defining strategy signatures for interview sections."""

    @abstractmethod
    async def execute_turn(
        self,
        db: AsyncSession,
        session: InterviewSession,
        history: list[InterviewMessage],
        current_difficulty: DifficultyLevel,
        active_elapsed_minutes: float,
        active_remaining_minutes: float,
    ) -> str:
        """Executes a single conversational turn in the interview section, returning the interviewer message."""
        pass
