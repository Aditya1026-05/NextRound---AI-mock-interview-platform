from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class LanguageTemplate(Base):
    """LanguageTemplate model storing generic wrappers and boilerplate per language."""
    __tablename__ = "language_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    language: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    boilerplate_wrapper: Mapped[str] = mapped_column(Text, nullable=False)
