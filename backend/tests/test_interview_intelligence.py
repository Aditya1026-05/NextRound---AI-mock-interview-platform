from unittest.mock import patch

import pytest
from sqlalchemy import select

from app.models.ai.candidate_profile import CandidateProfile
from app.models.interview.interview_blueprint import InterviewBlueprint
from app.models.interview.interview_message import InterviewMessage
from app.models.interview.interview_session import InterviewSession
from app.models.interview.interview_turn_analysis import InterviewTurnAnalysis
from app.models.resume.resume import Resume
from app.schemas.interview.interview_analysis import (
    InterviewAnalysis,
    InterviewerTurnResponse,
)
from app.services.interview.interview_decision_engine import InterviewDecisionEngine
from app.services.interview.interview_engine import InterviewEngine
from app.shared.enums import (
    AnswerQuality,
    DifficultyLevel,
    DifficultyType,
    InterviewAction,
    InterviewCategory,
    InterviewMessageRole,
    InterviewRole,
    InterviewState,
    QuestionType,
    ResumeStatus,
    SessionStatus,
)


@pytest.fixture
async def prep_test_data(db):
    """Fixture to setup resume, profile, and session with blueprint."""
    # 1. Create User
    from app.models.identity.user import User
    user = User(
        email="test_intel@nextround.ai",
        password_hash="mocked_password",
        full_name="Intelligence Test User",
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # 2. Create Resume
    resume = Resume(
        user_id=user.id,
        file_url="https://mock_resume.pdf",
        original_filename="mock_resume.pdf",
        mime_type="application/pdf",
        file_size=1024,
        status=ResumeStatus.CONFIRMED,
    )
    db.add(resume)
    await db.flush()

    # 3. Create Candidate Profile
    profile = CandidateProfile(
        user_id=user.id,
        resume_id=resume.id,
        profile_json={"summary": "Experience building with FastAPI, Python, and SQL databases."},
    )
    db.add(profile)
    await db.flush()

    # 4. Create Session
    session = InterviewSession(
        user_id=user.id,
        resume_id=resume.id,
        candidate_profile_id=profile.id,
        interview_category=InterviewCategory.TECHNICAL,
        role=InterviewRole.BACKEND,
        difficulty=DifficultyType.ADAPTIVE,
        duration_minutes=60,
        status=SessionStatus.IN_PROGRESS,
        interview_state=InterviewState.IN_PROGRESS.value,
        current_section_index=0,
    )
    db.add(session)
    await db.flush()

    # 5. Create Blueprint with custom min/max configurations
    blueprint = InterviewBlueprint(
        session_id=session.id,
        title="Backend Engineering Test Blueprint",
        estimated_duration=60,
        blueprint_json={
            "title": "Backend Engineering Test Blueprint",
            "estimated_duration": 60,
            "sections": [
                {
                    "name": "Database Fundamentals",
                    "duration": 30,
                    "min_questions": 2,
                    "max_questions": 3,
                    "max_followups": 1,
                },
                {
                    "name": "System Integration",
                    "duration": 30,
                    "min_questions": 2,
                    "max_questions": 4,
                    "max_followups": 2,
                },
            ],
        },
        generated_by_profile="interview_blueprint",
        generated_model="gemini",
    )
    db.add(blueprint)
    await db.flush()

    return user, resume, session, blueprint


def mock_llm_observation(
    accuracy=AnswerQuality.GOOD,
    depth=AnswerQuality.GOOD,
    coverage=AnswerQuality.GOOD,
    communication=AnswerQuality.GOOD,
    confidence=AnswerQuality.GOOD,
    missing_topics=None,
    strengths=None,
    needs_followup=False,
    should_transition_topic=False,
    should_transition_section=False,
    message="AI interviewer follow-up question?",
):
    """Helper to structure mock LLM response objects."""
    obs = InterviewAnalysis(
        technical_accuracy=accuracy,
        depth=depth,
        coverage=coverage,
        communication=communication,
        confidence=confidence,
        missing_topics=missing_topics or [],
        strengths=strengths or [],
        needs_followup=needs_followup,
        should_transition_topic=should_transition_topic,
        should_transition_section=should_transition_section,
    )
    return InterviewerTurnResponse(analysis=obs, interviewer_message=message)


@pytest.mark.asyncio
async def test_decision_engine_rules():
    """Test deterministic rules in InterviewDecisionEngine for follow-up and section progression gating."""
    engine = InterviewDecisionEngine()
    
    # Mock blueprint config
    blueprint = {
        "sections": [
            {
                "name": "Database Fundamentals",
                "min_questions": 2,
                "max_questions": 4,
                "max_followups": 2,
            }
        ]
    }

    # 1. Test GREETING transition
    decision = engine.decide_next_step(
        analysis=mock_llm_observation().analysis,
        current_state=InterviewState.GREETING,
        current_section_index=0,
        current_difficulty=DifficultyLevel.MEDIUM,
        blueprint_json=blueprint,
        history=[],
    )
    assert decision.action == InterviewAction.NEXT_QUESTION
    assert decision.should_transition is True
    assert decision.next_state == InterviewState.INTRODUCTION
    assert decision.question_type == QuestionType.INTRODUCTION

    # 2. Test FOLLOW_UP when missing topics are present
    msg_primary = InterviewMessage(role=InterviewMessageRole.INTERVIEWER, content="Primary question", question_type=QuestionType.PRIMARY.value)
    msg_ans = InterviewMessage(role=InterviewMessageRole.CANDIDATE, content="My answer")
    history = [msg_primary, msg_ans] # 1 candidate response in current section

    analysis_missing = mock_llm_observation(missing_topics=["Indexes"]).analysis
    decision_fu = engine.decide_next_step(
        analysis=analysis_missing,
        current_state=InterviewState.IN_PROGRESS,
        current_section_index=0,
        current_difficulty=DifficultyLevel.MEDIUM,
        blueprint_json=blueprint,
        history=history,
    )
    assert decision_fu.action == InterviewAction.FOLLOW_UP
    assert decision_fu.should_transition is False
    assert decision_fu.question_type == QuestionType.FOLLOW_UP

    # 3. Test follow-up limits prevent extra follow-up (max_followups = 2)
    # History contains 3 candidate responses (primary answer + 2 follow-up answers)
    history_limit = [
        msg_primary,
        msg_ans,
        InterviewMessage(role=InterviewMessageRole.INTERVIEWER, content="Followup 1", question_type=QuestionType.FOLLOW_UP.value),
        InterviewMessage(role=InterviewMessageRole.CANDIDATE, content="Ans 1"),
        InterviewMessage(role=InterviewMessageRole.INTERVIEWER, content="Followup 2", question_type=QuestionType.FOLLOW_UP.value),
        InterviewMessage(role=InterviewMessageRole.CANDIDATE, content="Ans 2"),
    ]
    decision_fu_limit = engine.decide_next_step(
        analysis=analysis_missing,
        current_state=InterviewState.IN_PROGRESS,
        current_section_index=0,
        current_difficulty=DifficultyLevel.MEDIUM,
        blueprint_json=blueprint,
        history=history_limit,
    )
    # Should transition to NEXT_QUESTION (primary) or SECTION_COMPLETE rather than FOLLOW_UP because follow-up count hit limit
    assert decision_fu_limit.action != InterviewAction.FOLLOW_UP

    # 4. Test CLARIFY when communication is poor
    analysis_poor_comm = mock_llm_observation(communication=AnswerQuality.POOR).analysis
    decision_clarify = engine.decide_next_step(
        analysis=analysis_poor_comm,
        current_state=InterviewState.IN_PROGRESS,
        current_section_index=0,
        current_difficulty=DifficultyLevel.MEDIUM,
        blueprint_json=blueprint,
        history=history,
    )
    assert decision_clarify.action == InterviewAction.CLARIFY
    assert decision_clarify.question_type == QuestionType.CLARIFICATION


@pytest.mark.asyncio
async def test_decision_engine_difficulty_progression():
    """Test gradual difficulty changes (EASY <-> MEDIUM <-> HARD)."""
    engine = InterviewDecisionEngine()
    blueprint = {"sections": [{"min_questions": 2, "max_questions": 4, "max_followups": 2}]}
    history = [InterviewMessage(role=InterviewMessageRole.INTERVIEWER, content="Q", question_type=QuestionType.PRIMARY.value), InterviewMessage(role=InterviewMessageRole.CANDIDATE, content="A")]

    # 1. EASY -> MEDIUM on Excellent accuracy and depth
    obs_excellent = mock_llm_observation(accuracy=AnswerQuality.EXCELLENT, depth=AnswerQuality.EXCELLENT).analysis
    decision_up = engine.decide_next_step(
        analysis=obs_excellent,
        current_state=InterviewState.IN_PROGRESS,
        current_section_index=0,
        current_difficulty=DifficultyLevel.EASY,
        blueprint_json=blueprint,
        history=history,
    )
    assert decision_up.next_difficulty == DifficultyLevel.MEDIUM

    # 2. HARD -> MEDIUM on Poor accuracy
    obs_poor = mock_llm_observation(accuracy=AnswerQuality.POOR).analysis
    decision_down = engine.decide_next_step(
        analysis=obs_poor,
        current_state=InterviewState.IN_PROGRESS,
        current_section_index=0,
        current_difficulty=DifficultyLevel.HARD,
        blueprint_json=blueprint,
        history=history,
    )
    assert decision_down.next_difficulty == DifficultyLevel.MEDIUM


@pytest.mark.asyncio
async def test_prevent_premature_section_completion():
    """Test section completion conditions (min_questions must be met)."""
    engine = InterviewDecisionEngine()
    blueprint = {
        "sections": [
            {
                "name": "Database Fundamentals",
                "min_questions": 3,
                "max_questions": 5,
                "max_followups": 2,
            }
        ]
    }

    # Case A: Coverage is EXCELLENT, but question_count is only 1 (less than min_questions = 3)
    history_one = [
        InterviewMessage(role=InterviewMessageRole.INTERVIEWER, content="Q", question_type=QuestionType.PRIMARY.value),
        InterviewMessage(role=InterviewMessageRole.CANDIDATE, content="A"),
    ]
    obs_excellent = mock_llm_observation(coverage=AnswerQuality.EXCELLENT).analysis
    decision_one = engine.decide_next_step(
        analysis=obs_excellent,
        current_state=InterviewState.IN_PROGRESS,
        current_section_index=0,
        current_difficulty=DifficultyLevel.MEDIUM,
        blueprint_json=blueprint,
        history=history_one,
    )
    assert decision_one.action != InterviewAction.SECTION_COMPLETE
    assert decision_one.should_transition is False

    # Case B: Coverage is EXCELLENT, and question_count is 3 (matches min_questions), but should_transition_section is False -> Should CHANGE_TOPIC
    history_three = [
        InterviewMessage(role=InterviewMessageRole.INTERVIEWER, content="Q1", question_type=QuestionType.PRIMARY.value),
        InterviewMessage(role=InterviewMessageRole.CANDIDATE, content="A1"),
        InterviewMessage(role=InterviewMessageRole.INTERVIEWER, content="Q2", question_type=QuestionType.FOLLOW_UP.value),
        InterviewMessage(role=InterviewMessageRole.CANDIDATE, content="A2"),
        InterviewMessage(role=InterviewMessageRole.INTERVIEWER, content="Q3", question_type=QuestionType.FOLLOW_UP.value),
        InterviewMessage(role=InterviewMessageRole.CANDIDATE, content="A3"),
    ]
    decision_three = engine.decide_next_step(
        analysis=obs_excellent,
        current_state=InterviewState.IN_PROGRESS,
        current_section_index=0,
        current_difficulty=DifficultyLevel.MEDIUM,
        blueprint_json=blueprint,
        history=history_three,
    )
    assert decision_three.action == InterviewAction.CHANGE_TOPIC
    assert decision_three.should_transition is False

    # Case C: Coverage is EXCELLENT, question_count is 3, and should_transition_section is True -> Should SECTION_COMPLETE
    obs_tr_section = mock_llm_observation(coverage=AnswerQuality.EXCELLENT, should_transition_section=True).analysis
    decision_tr = engine.decide_next_step(
        analysis=obs_tr_section,
        current_state=InterviewState.IN_PROGRESS,
        current_section_index=0,
        current_difficulty=DifficultyLevel.MEDIUM,
        blueprint_json=blueprint,
        history=history_three,
    )
    assert decision_tr.action == InterviewAction.SECTION_COMPLETE
    assert decision_tr.should_transition is True


@pytest.mark.asyncio
async def test_end_to_end_intelligence_execution(db, prep_test_data):
    """Test full InterviewEngine execution loop: saves message, evaluates observations, triggers decision rules, transitions and persists analysis."""
    _, _, session, _ = prep_test_data
    engine = InterviewEngine(db)

    # 1. Generate First Greeting Turn
    mock_greeting = mock_llm_observation(message="Hello Aditya. Welcome to the technical interview.")
    with patch(
        "app.llm.orchestrator.LLMOrchestrator.structured_completion",
        return_value=mock_greeting,
    ):
        greeting = await engine.generate_next_turn(session.id)
        assert greeting == "Hello Aditya. Welcome to the technical interview."
        await db.commit()
        await db.refresh(session)
        assert session.interview_state == InterviewState.GREETING.value

    # 2. Candidate Responds to Greeting
    candidate_reply = InterviewMessage(
        session_id=session.id,
        role=InterviewMessageRole.CANDIDATE,
        content="I am ready, thank you.",
        sequence_number=1,
    )
    db.add(candidate_reply)
    await db.commit()
    await db.refresh(session)

    # Generate Intro Turn (Evaluation of reply to greeting -> state goes to INTRODUCTION)
    mock_intro = mock_llm_observation(message="Let's start with a brief intro of your backend engineering experience.")
    with patch(
        "app.llm.orchestrator.LLMOrchestrator.structured_completion",
        return_value=mock_intro,
    ):
        intro = await engine.generate_next_turn(session.id)
        assert intro == "Let's start with a brief intro of your backend engineering experience."
        await db.commit()
        await db.refresh(session)
        assert session.interview_state == InterviewState.INTRODUCTION.value

    # 3. Candidate Introduces Themselves
    candidate_intro = InterviewMessage(
        session_id=session.id,
        role=InterviewMessageRole.CANDIDATE,
        content="I have 3 years of FastAPI and PostgreSQL experience.",
        sequence_number=3,
    )
    db.add(candidate_intro)
    await db.commit()
    await db.refresh(session)

    # Generate First In-Progress Question (Evaluation of intro -> state goes to IN_PROGRESS, Section 0)
    mock_q1 = mock_llm_observation(message="Can you explain database indexing in PostgreSQL?")
    with patch(
        "app.llm.orchestrator.LLMOrchestrator.structured_completion",
        return_value=mock_q1,
    ):
        q1 = await engine.generate_next_turn(session.id)
        assert q1 == "Can you explain database indexing in PostgreSQL?"
        await db.commit()
        await db.refresh(session)
        assert session.interview_state == InterviewState.IN_PROGRESS.value
        assert session.current_section_index == 0

    # 4. Candidate Answers Indexing Question (Incomplete answer)
    candidate_q1_ans = InterviewMessage(
        session_id=session.id,
        role=InterviewMessageRole.CANDIDATE,
        content="Indexes make queries faster, that is all.",
        sequence_number=5,
    )
    db.add(candidate_q1_ans)
    await db.commit()
    await db.refresh(session)

    # Generate next turn - should evaluate answers and detect missing topics -> FOLLOW_UP
    mock_followup = mock_llm_observation(
        accuracy=AnswerQuality.FAIR,
        missing_topics=["B-Trees", "Index Types"],
        message="That's a start. Can you explain what data structure PostgreSQL uses for standard indexes, like B-Trees?",
    )
    with patch(
        "app.llm.orchestrator.LLMOrchestrator.structured_completion",
        return_value=mock_followup,
    ):
        next_msg = await engine.generate_next_turn(session.id)
        assert "B-Trees" in next_msg
        await db.commit()
        await db.refresh(session)
        
        # Verify state did not transition (remains in Section 0)
        assert session.interview_state == InterviewState.IN_PROGRESS.value
        assert session.current_section_index == 0

        # Assert Turn Analysis was persisted in database linked to candidate_q1_ans message
        stmt_ta = select(InterviewTurnAnalysis).filter(InterviewTurnAnalysis.message_id == candidate_q1_ans.id)
        turn_analysis = await db.scalar(stmt_ta)
        assert turn_analysis is not None
        assert turn_analysis.technical_accuracy == AnswerQuality.FAIR.value
        assert "B-Trees" in turn_analysis.missing_topics
        assert turn_analysis.analysis_version == "v1"
        assert turn_analysis.difficulty_level == DifficultyLevel.MEDIUM.value


@pytest.mark.asyncio
async def test_decision_engine_hybrid_time_gate():
    """Verify time-gating, safety rails, and dynamic semantic flags in InterviewDecisionEngine."""
    engine = InterviewDecisionEngine()
    blueprint = {
        "estimated_duration": 60,
        "sections": [
            {
                "name": "Database Fundamentals",
                "duration": 10,  # 10 minutes (600 seconds)
                "min_questions": 2,
                "max_questions": 4,
                "max_followups": 2,
            }
        ]
    }

    # Setup history with 2 candidate turns
    msg_q = InterviewMessage(role=InterviewMessageRole.INTERVIEWER, content="Q1", question_type=QuestionType.PRIMARY.value)
    msg_a = InterviewMessage(role=InterviewMessageRole.CANDIDATE, content="A1")
    history = [msg_q, msg_a]

    # Case 1: Time limit expired (section_active_seconds = 610) -> Should transition
    decision_time = engine.decide_next_step(
        analysis=mock_llm_observation().analysis,
        current_state=InterviewState.IN_PROGRESS,
        current_section_index=0,
        current_difficulty=DifficultyLevel.MEDIUM,
        blueprint_json=blueprint,
        history=history,
        section_active_seconds=610.0,
        session_duration_minutes=60,
    )
    assert decision_time.action == InterviewAction.SECTION_COMPLETE
    assert decision_time.should_transition is True

    # Case 2: LLM requests section transition but question count is below min_questions (1 < 2) -> Should NOT transition
    obs_section_tr = mock_llm_observation(should_transition_section=True).analysis
    decision_min = engine.decide_next_step(
        analysis=obs_section_tr,
        current_state=InterviewState.IN_PROGRESS,
        current_section_index=0,
        current_difficulty=DifficultyLevel.MEDIUM,
        blueprint_json=blueprint,
        history=history,
        section_active_seconds=100.0,
        session_duration_minutes=60,
    )
    assert decision_min.action != InterviewAction.SECTION_COMPLETE

    # Case 3: LLM requests section transition and question count meets min_questions (history has 2 candidate turns)
    history_two = [
        msg_q, msg_a,
        InterviewMessage(role=InterviewMessageRole.INTERVIEWER, content="Q2", question_type=QuestionType.FOLLOW_UP.value),
        InterviewMessage(role=InterviewMessageRole.CANDIDATE, content="A2"),
    ]
    decision_llm_tr = engine.decide_next_step(
        analysis=obs_section_tr,
        current_state=InterviewState.IN_PROGRESS,
        current_section_index=0,
        current_difficulty=DifficultyLevel.MEDIUM,
        blueprint_json=blueprint,
        history=history_two,
        section_active_seconds=100.0,
        session_duration_minutes=60,
    )
    assert decision_llm_tr.action == InterviewAction.SECTION_COMPLETE

    # Case 4: Hard safety override (question_count = 5) -> Should transition
    history_five = []
    for i in range(5):
        history_five.append(InterviewMessage(role=InterviewMessageRole.INTERVIEWER, content=f"Q{i}", question_type=QuestionType.PRIMARY.value if i == 0 else QuestionType.FOLLOW_UP.value))
        history_five.append(InterviewMessage(role=InterviewMessageRole.CANDIDATE, content=f"A{i}"))
    decision_safety = engine.decide_next_step(
        analysis=mock_llm_observation().analysis,
        current_state=InterviewState.IN_PROGRESS,
        current_section_index=0,
        current_difficulty=DifficultyLevel.MEDIUM,
        blueprint_json=blueprint,
        history=history_five,
        section_active_seconds=100.0,
        session_duration_minutes=60,
    )
    assert decision_safety.action == InterviewAction.SECTION_COMPLETE

    # Case 5: LLM requests topic transition -> Should return CHANGE_TOPIC
    obs_topic_tr = mock_llm_observation(should_transition_topic=True).analysis
    decision_topic = engine.decide_next_step(
        analysis=obs_topic_tr,
        current_state=InterviewState.IN_PROGRESS,
        current_section_index=0,
        current_difficulty=DifficultyLevel.MEDIUM,
        blueprint_json=blueprint,
        history=history,
        section_active_seconds=100.0,
    )
    assert decision_topic.action == InterviewAction.CHANGE_TOPIC

    # Case 6: Session time limit expired (session_active_seconds = 3610 for a 60-min session) -> Should transition to CLOSING
    decision_session_time = engine.decide_next_step(
        analysis=mock_llm_observation().analysis,
        current_state=InterviewState.IN_PROGRESS,
        current_section_index=0,
        current_difficulty=DifficultyLevel.MEDIUM,
        blueprint_json=blueprint,
        history=history,
        section_active_seconds=100.0,
        session_active_seconds=3610.0,
        session_duration_minutes=60,
    )
    assert decision_session_time.action == InterviewAction.SECTION_COMPLETE
    assert decision_session_time.should_transition is True
    assert decision_session_time.next_state == InterviewState.CLOSING


@pytest.mark.asyncio
async def test_active_time_calculation():
    """Verify active-time calculator sums response times accurately and caps idle AFK gaps."""
    from datetime import datetime, timedelta, timezone
    from app.services.interview.interview_engine import _calculate_active_time

    base_time = datetime.now(timezone.utc)

    # 1. Normal Turn: Interviewer asks, Candidate replies in 30 seconds
    m0 = InterviewMessage(sequence_number=0, role=InterviewMessageRole.INTERVIEWER, question_type=QuestionType.PRIMARY.value, created_at=base_time)
    m1 = InterviewMessage(sequence_number=1, role=InterviewMessageRole.CANDIDATE, created_at=base_time + timedelta(seconds=30))

    # 2. AFK/Idle Turn: Interviewer asks, Candidate goes AFK and replies 10 minutes later (600 seconds)
    m2 = InterviewMessage(sequence_number=2, role=InterviewMessageRole.INTERVIEWER, question_type=QuestionType.FOLLOW_UP.value, created_at=base_time + timedelta(seconds=40))
    m3 = InterviewMessage(sequence_number=3, role=InterviewMessageRole.CANDIDATE, created_at=base_time + timedelta(seconds=640))

    # 3. Transition Turn: Moves to Section 2 (sequence_number index 1)
    m4 = InterviewMessage(sequence_number=4, role=InterviewMessageRole.INTERVIEWER, question_type=QuestionType.TRANSITION.value, created_at=base_time + timedelta(seconds=650))
    m5 = InterviewMessage(sequence_number=5, role=InterviewMessageRole.CANDIDATE, created_at=base_time + timedelta(seconds=700)) # 50 seconds latency

    history = [m0, m1, m2, m3, m4, m5]

    # Calculate active time
    total_active, section_active_0 = _calculate_active_time(history, target_section_index=0)
    _, section_active_1 = _calculate_active_time(history, target_section_index=1)

    # Turn 1: 30 seconds
    # Turn 2: 600 seconds -> Capped to 120 seconds
    # Turn 3 (Section 1): 50 seconds
    # Total Active: 30 + 120 + 50 = 200 seconds
    assert total_active == 200.0

    # Section 0 Active: Turn 1 (30s) + Turn 2 (120s) = 150 seconds
    assert section_active_0 == 150.0

    # Section 1 Active: Turn 3 (50s) = 50 seconds
    assert section_active_1 == 50.0
