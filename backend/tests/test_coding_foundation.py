import uuid
import pytest
from unittest.mock import patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.interview.coding_problem import CodingProblem
from app.models.interview.interview_session import InterviewSession
from app.models.interview.interview_message import InterviewMessage
from app.models.interview.interview_blueprint import InterviewBlueprint
from app.models.interview.interview_question import InterviewQuestion
from app.models.identity.user import User
from app.shared.enums import (
    DiscussionPhase,
    HintLevel,
    DifficultyType,
    DifficultyLevel,
    InterviewCategory,
    SessionStatus,
    InterviewState,
    InterviewMessageRole,
    InterviewType,
)
from app.services.interview.coding_problem_service import CodingProblemService
from app.services.interview.coding_context import CodingContext
from app.services.interview.coding_prompt_builder import CodingPromptBuilder
from app.services.interview.coding_section_strategy import CodingSectionStrategy
from app.services.interview.interviewer_agent import InterviewerAgent
from app.schemas.interview.coding_problem import CodingProblemResponse, CodingHint, FollowUpQuestion

def create_mock_agent_response(data: dict):
    from app.schemas.interview.interview_analysis import InterviewerTurnResponse, InterviewAnalysis
    from app.shared.enums import AnswerQuality
    
    msg = data.get("interviewer_message", "")
    defaults = {
        "technical_accuracy": AnswerQuality.GOOD.value,
        "depth": AnswerQuality.GOOD.value,
        "coverage": AnswerQuality.GOOD.value,
        "communication": AnswerQuality.GOOD.value,
        "confidence": AnswerQuality.GOOD.value,
        "missing_topics": [],
        "strengths": [],
        "needs_followup": False,
        "should_transition_topic": False,
        "should_transition_section": False,
    }
    analysis_data = defaults | (data.get("analysis") or {})
    analysis = InterviewAnalysis(**analysis_data)
    return InterviewerTurnResponse(analysis=analysis, interviewer_message=msg)

@pytest.mark.asyncio
async def test_coding_problem_db_operations(db: AsyncSession):
    # 1. Create a coding problem
    problem = CodingProblem(
        title="Three Sum",
        description="Given an integer array nums, return all the triplets such that their sum is 0.",
        question_type=InterviewType.CODING,
        difficulty=DifficultyType.HARD,
        estimated_minutes=30,
        optimal_time_complexity="O(N^2)",
        optimal_space_complexity="O(N)",
        optimal_solutions={"python": "def threeSum(self, nums):\n    pass"},
        function_signatures={"python": "def threeSum(self, nums: List[int]) -> List[List[int]]:"},
        hints=[
            {"level": "LEVEL_1", "content": "Sort the array first.", "purpose": "Hint on order"}
        ],
        follow_ups=[
            {"question": "Can you do it in O(1) space?", "purpose": "Validate complexity", "expected_answer": "No"}
        ],
        topics=["Arrays", "TwoPointers"],
        companies=["Google"],
    )
    db.add(problem)
    await db.commit()
    await db.refresh(problem)

    assert problem.id is not None
    assert problem.optimal_time_complexity == "O(N^2)"
    assert problem.topics == ["Arrays", "TwoPointers"]

    # 2. Query via service
    service = CodingProblemService()
    fetched = await service.get_problem_by_id(db, problem.id)
    assert fetched is not None
    assert fetched.title == "Three Sum"

    by_topic = await service.get_by_topic(db, "Arrays")
    assert len(by_topic) > 0
    assert any(item.id == problem.id for item in by_topic)

    by_difficulty = await service.get_by_difficulty(db, DifficultyType.HARD)
    assert len(by_difficulty) > 0

@pytest.mark.asyncio
async def test_coding_prompt_builder(db: AsyncSession):
    problem_res = CodingProblemResponse(
        id=uuid.uuid4(),
        title="Mock Problem",
        description="Mock Description",
        difficulty="medium",
        function_signatures={"python": "def func(): pass"},
        optimal_solutions={"python": "pass"},
        optimal_time_complexity="O(N)",
        optimal_space_complexity="O(1)",
        hints=[CodingHint(level=HintLevel.LEVEL_1, content="Try map", purpose="Hint")],
        follow_ups=[FollowUpQuestion(question="scale?", purpose="scaling", expected_answer="yes")],
        topics=["Arrays"],
        companies=["Amazon"],
    )
    context = CodingContext(
        active_problem=problem_res,
        discussion_phase=DiscussionPhase.THINKING,
        current_hint_level=HintLevel.LEVEL_1,
        language="python",
        transcript=[{"role": "Candidate", "content": "Hello"}],
    )
    builder = CodingPromptBuilder()
    prompt_ctx = builder.build_prompts(context)

    assert "ACTIVE PROBLEM:" in prompt_ctx.system_prompt
    assert "CURRENT PHASE: THINKING" in prompt_ctx.system_prompt
    assert "ACTIVE HINT TO INJECT: Try map" in prompt_ctx.system_prompt
    assert "Candidate: Hello" in prompt_ctx.user_prompt

@pytest.mark.asyncio
async def test_coding_section_strategy_turn(db: AsyncSession):
    # Setup mock user and session
    user = User(email=f"coding_test_{uuid.uuid4().hex}@example.com", password_hash="hash", full_name="Coding Candidate")
    db.add(user)
    await db.commit()

    session = InterviewSession(
        user_id=user.id,
        interview_category=InterviewCategory.CODING,
        duration_minutes=45,
        difficulty=DifficultyType.MEDIUM,
        status=SessionStatus.IN_PROGRESS,
        interview_state=InterviewState.IN_PROGRESS,
        current_section_index=0,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    blueprint = InterviewBlueprint(
        session_id=session.id,
        title="Coding Interview Blueprint",
        estimated_duration=45,
        blueprint_json={
            "sections": [
                {"name": "Coding (DSA)", "duration": 40, "min_questions": 1, "max_questions": 1, "max_followups": 1}
            ]
        },
        generated_by_profile="test",
        generated_model="test",
    )
    db.add(blueprint)
    await db.commit()
    await db.refresh(session)

    # Prepopulate one candidate response message
    msg = InterviewMessage(
        session_id=session.id,
        role=InterviewMessageRole.CANDIDATE,
        content="I think we should use a hash map for lookups.",
        sequence_number=1,
    )
    db.add(msg)
    await db.commit()

    # Mock agent response with transition topic trigger
    mock_agent_response = create_mock_agent_response({
        "interviewer_message": "Excellent. Now please write down the code implementation.",
        "analysis": {
            "should_transition_topic": True,
            "should_transition_section": False,
        }
    })

    strategy = CodingSectionStrategy()
    with patch.object(InterviewerAgent, "generate_response", return_value=mock_agent_response):
        reply = await strategy.execute_turn(
            db=db,
            session=session,
            history=[msg],
            current_difficulty=DifficultyLevel.MEDIUM,
            active_elapsed_minutes=5.0,
            active_remaining_minutes=40.0,
        )

        assert reply == "Excellent. Now please write down the code implementation."

        # Verify InterviewQuestion was snapshotted
        stmt_q = select(InterviewQuestion).filter(InterviewQuestion.session_id == session.id)
        session_q = await db.scalar(stmt_q)
        assert session_q is not None
        assert session_q.title in ["Two Sum", "Valid Anagram", "Reverse Linked List"]

        # Verify next message is saved with DiscussionPhase.CODING question type
        stmt_m = select(InterviewMessage).filter(
            InterviewMessage.session_id == session.id,
            InterviewMessage.role == InterviewMessageRole.INTERVIEWER
        ).order_by(InterviewMessage.sequence_number.desc())
        last_interviewer_msg = await db.scalar(stmt_m)
        assert last_interviewer_msg is not None
        assert last_interviewer_msg.question_type == DiscussionPhase.CODING.value
