import uuid
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.observability import (
    bind_context,
    log_operation,
    step_completed,
    step_failed,
)
from app.models.interview.interview_message import InterviewMessage
from app.models.interview.interview_session import InterviewSession
from app.models.interview.interview_turn_analysis import InterviewTurnAnalysis
from app.services.interview.conversation_service import ConversationService
from app.services.interview.interviewer_agent import InterviewerAgent
from app.services.interview.prompt_builder import InterviewPromptBuilder
from app.services.interview.state_machine import InterviewStateMachine
from app.services.interview.interview_decision_engine import InterviewDecisionEngine
from app.shared.enums import (
    AnswerQuality,
    DifficultyLevel,
    DifficultyType,
    InterviewMessageRole,
    InterviewState,
    QuestionType,
    SessionStatus,
)

logger = structlog.get_logger()


def clean_interviewer_message(message: str) -> str:
    """Safeguard filter to strip forbidden diagnostic/praise prefixes from LLM responses."""
    import re
    cleaned = message.strip()
    
    # 1. Clean standalone or beginning-of-message praise
    praise_pattern = r"^(that's a good start\.?|great start\.?|nice start\.?|good start\.?|that's a great start\.?|nice job\.?|excellent job\.?)\s*"
    cleaned = re.sub(praise_pattern, "", cleaned, flags=re.IGNORECASE)
    
    # 2. Clean praise that occurs immediately after a conversational bridge (e.g. "Got it. That's a great start, Aditya.")
    bridge_praise_pattern = r"^(got it|makes sense|understood|no worries|interesting|i see)\.?\s+(that's a good start|that's a great start|great start|nice start|good start|nice job|excellent job)[^.!?]*[.!?]\s*"
    cleaned = re.sub(bridge_praise_pattern, r"\1. ", cleaned, flags=re.IGNORECASE)
    
    # Capitalize the first letter of the cleaned message
    if cleaned:
        cleaned = cleaned[0].upper() + cleaned[1:]
    return cleaned


def _calculate_active_time(history: list[InterviewMessage], target_section_index: int) -> tuple[float, float]:
    """Calculates active session elapsed seconds and active section elapsed seconds.
    Caps each turn response time to 120 seconds to ignore AFK/idle gaps.
    """
    total_active_seconds = 0.0
    section_active_seconds = 0.0
    sec_idx = 0

    msg_map = {m.sequence_number: m for m in history}

    for msg in history:
        if msg.role == InterviewMessageRole.INTERVIEWER and msg.question_type == QuestionType.TRANSITION.value:
            sec_idx += 1

        if msg.role == InterviewMessageRole.CANDIDATE:
            prev = msg_map.get(msg.sequence_number - 1)
            if prev and prev.role == InterviewMessageRole.INTERVIEWER:
                delta = (msg.created_at - prev.created_at).total_seconds()
                # Cap response time to 120 seconds to ignore idle/AFK time
                capped_delta = min(max(0.0, delta), 120.0)
                
                total_active_seconds += capped_delta
                if sec_idx == target_section_index:
                    section_active_seconds += capped_delta

    return total_active_seconds, section_active_seconds


class InterviewEngine:
    """Orchestrates mock interview conversation flow by coordinating history fetches,
    decision evaluations, state transitions, prompt building, and structured turn analysis.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.conversation_service = ConversationService(db)
        self.state_machine = InterviewStateMachine()
        self.prompt_builder = InterviewPromptBuilder()
        self.interviewer_agent = InterviewerAgent()
        self.decision_engine = InterviewDecisionEngine()

    @log_operation(category="INTERVIEW", name="Interview Engine Turn Execution")
    async def generate_next_turn(self, session_id: uuid.UUID) -> str:
        """Advance interview states, evaluate responses, invoke LLM structured analysis, and persist turn metadata."""
        # 1. Fetch the session
        stmt = select(InterviewSession).filter(InterviewSession.id == session_id)
        session = await self.db.scalar(stmt)
        if not session:
            step_failed("VALIDATION", "Session loading", f"Session not found: {session_id}")
            raise ValueError("Session not found")

        bind_context(
            session_id=str(session.id),
            user_id=str(session.user_id),
            resume_id=str(session.resume_id) if session.resume_id else None,
        )

        # 2. Fetch conversation history
        history = await self.conversation_service.load_recent_history(session_id)
        is_first_turn = len(history) == 0

        # Resolve dynamic/effective difficulty
        current_difficulty = DifficultyLevel.MEDIUM
        if session.difficulty == DifficultyType.EASY:
            current_difficulty = DifficultyLevel.EASY
        elif session.difficulty == DifficultyType.HARD:
            current_difficulty = DifficultyLevel.HARD
        elif session.difficulty == DifficultyType.MEDIUM:
            current_difficulty = DifficultyLevel.MEDIUM
        else:  # ADAPTIVE
            # Find the most recent turn analysis to fetch its difficulty level
            stmt_ta = (
                select(InterviewTurnAnalysis)
                .join(InterviewMessage)
                .filter(InterviewMessage.session_id == session.id)
                .order_by(InterviewTurnAnalysis.created_at.desc())
                .limit(1)
            )
            ta_rec = await self.db.scalar(stmt_ta)
            if ta_rec:
                current_difficulty = DifficultyLevel(ta_rec.difficulty_level)

        # 3. Handle First Turn Initialization
        if is_first_turn:
            next_state = InterviewState.GREETING
            next_section = 0
            session.interview_state = next_state.value
            session.current_section_index = next_section
            await self.db.flush()

            # Build prompt context
            prompt_ctx = self.prompt_builder.build_prompts(
                session,
                list(history),
                current_difficulty=current_difficulty.value,
            )

            # Generate first greeting from agent
            agent_response = await self.interviewer_agent.generate_response(prompt_ctx)

            # Save interviewer message with type PRIMARY
            await self.conversation_service.save_message(
                session_id=session.id,
                role=InterviewMessageRole.INTERVIEWER,
                content=agent_response.interviewer_message,
                question_type=QuestionType.PRIMARY.value,
            )

            print(f"\n──────── TURN 1 ────────")
            print("Starting Mock Interview")
            print(f"State Machine State .... GREETING (Section: 0)")
            print(f"Difficulty ............. {current_difficulty.value}")
            print(f"Interviewer Greeting ... {agent_response.interviewer_message[:60]}...")
            print("────────────────────────\n")

            return agent_response.interviewer_message

        # Not first turn — we have a candidate response in history
        candidate_msg = history[-1]
        if candidate_msg.role != InterviewMessageRole.CANDIDATE:
            raise ValueError("Expected latest message in history to be a candidate response")

        # 4. Process deterministic pre-transitions (lag mitigation)
        is_greeting_reply = session.interview_state == InterviewState.GREETING.value
        is_intro_reply = session.interview_state == InterviewState.INTRODUCTION.value
        is_closing_reply = session.interview_state == InterviewState.CLOSING.value

        if is_greeting_reply:
            session.interview_state = InterviewState.INTRODUCTION.value
            await self.db.flush()
        elif is_intro_reply:
            session.interview_state = InterviewState.IN_PROGRESS.value
            session.current_section_index = 0
            await self.db.flush()
        elif is_closing_reply:
            session.interview_state = InterviewState.COMPLETED.value
            session.status = SessionStatus.COMPLETED
            await self.db.flush()

        # 5. Build prompt context using updated state
        memory_ctx = await self.conversation_service.load_summary(session_id)
        
        # Calculate active elapsed and remaining time
        active_elapsed_seconds, active_section_seconds = _calculate_active_time(
            list(history), session.current_section_index or 0
        )
        active_elapsed_minutes = active_elapsed_seconds / 60.0
        active_remaining_minutes = max(0.0, session.duration_minutes - active_elapsed_minutes)

        # Resolve active section strategy routing
        active_sec_name = "N/A"
        if session.blueprint and session.blueprint.blueprint_json:
            sections = session.blueprint.blueprint_json.get("sections", [])
            idx = session.current_section_index
            if idx is not None and 0 <= idx < len(sections):
                active_sec_name = sections[idx].get("name", "N/A")

        is_coding_category = session.interview_category.value.upper() == "CODING"
        if is_coding_category and active_sec_name == "Coding (DSA)" and not (is_greeting_reply or is_closing_reply):
            from app.services.interview.coding_section_strategy import CodingSectionStrategy
            strategy = CodingSectionStrategy()
            return await strategy.execute_turn(
                db=self.db,
                session=session,
                history=list(history),
                current_difficulty=current_difficulty,
                active_elapsed_minutes=active_elapsed_minutes,
                active_remaining_minutes=active_remaining_minutes,
            )

        prompt_ctx = self.prompt_builder.build_prompts(
            session,
            list(history)[-10:],
            memory_context=memory_ctx,
            current_difficulty=current_difficulty.value,
            active_elapsed_minutes=active_elapsed_minutes,
            active_remaining_minutes=active_remaining_minutes,
        )

        # 6. Generate response from LLM Agent
        agent_response = await self.interviewer_agent.generate_response(prompt_ctx)
        analysis = agent_response.analysis

        # 7. Persist Turn Metrics & Message for Deterministic/Warmup Turns
        if is_greeting_reply or is_intro_reply or is_closing_reply:
            # Observational records are N/A for these warm-up/close phases
            turn_analysis = InterviewTurnAnalysis(
                message_id=candidate_msg.id,
                technical_accuracy=AnswerQuality.NOT_APPLICABLE.value,
                depth=AnswerQuality.NOT_APPLICABLE.value,
                coverage=AnswerQuality.NOT_APPLICABLE.value,
                communication=AnswerQuality.NOT_APPLICABLE.value,
                confidence=AnswerQuality.NOT_APPLICABLE.value,
                missing_topics=[],
                strengths=[],
                difficulty_level=current_difficulty.value,
                blueprint_section="N/A",
                analysis_version="v1",
            )
            self.db.add(turn_analysis)

            # Resolve question type
            q_type = QuestionType.PRIMARY.value
            if is_greeting_reply:
                q_type = QuestionType.INTRODUCTION.value
            elif is_closing_reply:
                q_type = QuestionType.CLOSING.value

            # Save next interviewer message
            await self.conversation_service.save_message(
                session_id=session.id,
                role=InterviewMessageRole.INTERVIEWER,
                content=agent_response.interviewer_message,
                question_type=q_type,
            )

            turn_num = len(history) + 1
            print(f"\n──────── TURN {turn_num} ────────")
            print("Candidate Response Saved")
            print("Deterministic Transition (Warmup/Closing)")
            print(f"State Machine State .... {session.interview_state} (Section: {session.current_section_index})")
            print("────────────────────────\n")

            return agent_response.interviewer_message

        # 8. Main IN_PROGRESS Turn Execution
        # Run Decision Engine (rules-based transitions)
        decision = self.decision_engine.decide_next_step(
            analysis=analysis,
            current_state=InterviewState(session.interview_state),
            current_section_index=session.current_section_index or 0,
            current_difficulty=current_difficulty,
            blueprint_json=session.blueprint.blueprint_json if session.blueprint else None,
            history=history,
            section_active_seconds=active_section_seconds,
            session_active_seconds=active_elapsed_seconds,
            session_duration_minutes=session.duration_minutes,
        )

        # Apply State Machine transitions for next turn
        next_state, next_section = self.state_machine.advance_state(
            session=session,
            action=decision.action.value,
            should_transition=decision.should_transition,
            next_state_override=decision.next_state.value if decision.next_state else None,
        )

        session.interview_state = next_state.value
        session.current_section_index = next_section

        if next_state == InterviewState.COMPLETED:
            session.status = SessionStatus.COMPLETED

        await self.db.flush()

        # If the state machine transitioned to CLOSING or COMPLETED, we must regenerate
        # the interviewer message to match the new state, discarding the temporary technical question.
        if next_state in (InterviewState.CLOSING, InterviewState.COMPLETED):
            logger.info("State transitioned to CLOSING/COMPLETED. Regenerating interviewer message.", next_state=next_state.value)
            
            # Recalculate time since history or state might have advanced
            active_elapsed_seconds_regen, active_section_seconds_regen = _calculate_active_time(
                list(history), session.current_section_index or 0
            )
            active_elapsed_minutes_regen = active_elapsed_seconds_regen / 60.0
            active_remaining_minutes_regen = max(0.0, session.duration_minutes - active_elapsed_minutes_regen)
            
            # Re-build prompt using the new state
            prompt_ctx = self.prompt_builder.build_prompts(
                session,
                list(history)[-10:],
                memory_context=memory_ctx,
                current_difficulty=current_difficulty.value,
                active_elapsed_minutes=active_elapsed_minutes_regen,
                active_remaining_minutes=active_remaining_minutes_regen,
            )
            # Re-generate from LLM Agent to get correct closing/thank-you message
            regen_response = await self.interviewer_agent.generate_response(prompt_ctx)
            # Discard the temporary technical question, but keep original candidate response analysis observations
            agent_response.interviewer_message = regen_response.interviewer_message

        # Save observations linked to candidate's message
        active_sec_name = "N/A"
        if session.blueprint and session.blueprint.blueprint_json:
            sections = session.blueprint.blueprint_json.get("sections", [])
            idx = session.current_section_index
            if idx is not None and 0 <= idx < len(sections):
                active_sec_name = sections[idx].get("name", "N/A")

        turn_analysis = InterviewTurnAnalysis(
            message_id=candidate_msg.id,
            technical_accuracy=analysis.technical_accuracy.value,
            depth=analysis.depth.value,
            coverage=analysis.coverage.value,
            communication=analysis.communication.value,
            confidence=analysis.confidence.value,
            missing_topics=analysis.missing_topics,
            strengths=analysis.strengths,
            difficulty_level=decision.next_difficulty.value,
            blueprint_section=active_sec_name,
            analysis_version="v1",
        )
        self.db.add(turn_analysis)

        # Clean response message from any forbidden praise/diagnostic prefixes
        agent_response.interviewer_message = clean_interviewer_message(agent_response.interviewer_message)

        # Save interviewer response message setting its question_type
        await self.conversation_service.save_message(
            session_id=session.id,
            role=InterviewMessageRole.INTERVIEWER,
            content=agent_response.interviewer_message,
            question_type=decision.question_type.value,
        )

        # 9. Format structured logging output
        turn_num = len(history) + 1
        print(f"\n──────── TURN {turn_num} ────────")
        print("Candidate Response Saved")
        print("InterviewerAgent Completed")
        print(f"Technical Accuracy ..... {analysis.technical_accuracy.value}")
        print(f"Coverage ............... {analysis.coverage.value}")
        print(f"Depth .................. {analysis.depth.value}")
        print(f"Communication .......... {analysis.communication.value}")
        print(f"Confidence ............. {analysis.confidence.value}")
        print(f"Missing Topics ......... {', '.join(analysis.missing_topics) if analysis.missing_topics else 'None'}")
        print(f"Strengths .............. {', '.join(analysis.strengths) if analysis.strengths else 'None'}")
        print(f"Decision Engine Action . {decision.action.value}")
        print(f"Next Difficulty ........ {decision.next_difficulty.value}")
        print(f"State Machine State .... {next_state.value} (Section: {next_section})")
        print("────────────────────────\n")

        return agent_response.interviewer_message
