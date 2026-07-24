import uuid
from sqlalchemy import ForeignKey, String, Integer
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.interview.question_bank import QuestionBank
from app.shared.enums import InterviewType

class CodingProblem(QuestionBank):
    """CodingProblem model storing detailed, structured coding questions.
    Inherits from QuestionBank via SQLAlchemy Joined-Table Inheritance.
    """
    __tablename__ = "coding_problems"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("question_bank.id", ondelete="CASCADE"),
        primary_key=True
    )

    function_signatures: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    optimal_solutions: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    driver_templates: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)
    optimal_time_complexity: Mapped[str] = mapped_column(String(50), nullable=False)

    optimal_space_complexity: Mapped[str] = mapped_column(String(50), nullable=False)
    hints: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
    follow_ups: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
    estimated_duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    recommended_languages: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    learning_objectives: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    topics: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
    companies: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")

    __mapper_args__ = {
        "polymorphic_identity": InterviewType.CODING,
    }
