import uuid
import structlog
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interview.interview_session import InterviewSession
from app.models.interview.interview_message import InterviewMessage
from app.models.interview.interview_question import InterviewQuestion
from app.models.interview.interview_turn_analysis import InterviewTurnAnalysis
from app.models.interview.coding_problem import CodingProblem
from app.services.interview.section_strategy import BaseSectionStrategy
from app.services.interview.coding_context import CodingContext
from app.services.interview.coding_prompt_builder import CodingPromptBuilder
from app.services.interview.prompt_builder import PromptContext
from app.services.interview.interviewer_agent import InterviewerAgent
from app.services.interview.conversation_service import ConversationService
from app.schemas.interview.coding_problem import CodingProblemResponse, CodingHint, FollowUpQuestion
from app.shared.enums import (
    DifficultyType,
    DifficultyLevel,
    DiscussionPhase,
    HintLevel,
    InterviewType,
    InterviewMessageRole,
    QuestionType,
    AnswerQuality,
)

logger = structlog.get_logger()

class CodingSectionStrategy(BaseSectionStrategy):
    """Strategy class orchestrating conversation turns during coding blueprint sections."""

    def __init__(self):
        self.prompt_builder = CodingPromptBuilder()
        self.agent = InterviewerAgent()
        self.conversation_service = ConversationService(None) # Session database transaction passed explicitly

    async def execute_turn(
        self,
        db: AsyncSession,
        session: InterviewSession,
        history: list[InterviewMessage],
        current_difficulty: DifficultyLevel,
        active_elapsed_minutes: float,
        active_remaining_minutes: float,
    ) -> str:
        # Set database on conversation service
        self.conversation_service.db = db

        # 1. Retrieve or generate active coding problem for this session
        coding_problem = await self._get_or_create_session_problem(db, session)

        # 2. Determine active discussion phase and hint level
        active_phase, current_hint = self._determine_discussion_state(history)

        # Serialize coding problem to Response model
        problem_res = CodingProblemResponse(
            id=coding_problem.id,
            title=coding_problem.title,
            description=coding_problem.description,
            difficulty=coding_problem.difficulty.value,
            function_signatures=coding_problem.function_signatures or {},
            optimal_solutions=coding_problem.optimal_solutions or {},
            optimal_time_complexity=coding_problem.optimal_time_complexity or "O(N)",
            optimal_space_complexity=coding_problem.optimal_space_complexity or "O(1)",
            hints=[CodingHint(**h) for h in (coding_problem.hints or [])],
            follow_ups=[FollowUpQuestion(**f) for f in (coding_problem.follow_ups or [])],
            estimated_duration_minutes=coding_problem.estimated_duration_minutes,
            recommended_languages=coding_problem.recommended_languages or [],
            learning_objectives=coding_problem.learning_objectives or [],
            topics=coding_problem.topics or [],
            companies=coding_problem.companies or [],
        )

        # Build context
        transcript_data = [
            {"role": "Interviewer" if msg.role == InterviewMessageRole.INTERVIEWER else "Candidate", "content": msg.content}
            for msg in history
        ]
        context = CodingContext(
            active_problem=problem_res,
            discussion_phase=active_phase,
            current_hint_level=current_hint,
            language="python",
            transcript=transcript_data,
            blueprint=session.blueprint.blueprint_json if session.blueprint else None,
        )

        # 3. Build prompts and generate LLM agent response
        coding_prompts = self.prompt_builder.build_prompts(context)
        prompt_ctx = PromptContext(
            system_prompt=coding_prompts.system_prompt,
            user_prompt=coding_prompts.user_prompt,
            current_state=session.interview_state,
            current_section=None,
            memory_context=None,
            blueprint_reference=None,
        )

        agent_response = await self.agent.generate_response(prompt_ctx)
        analysis = agent_response.analysis

        # 4. Resolve next discussion phase based on transitions
        next_phase = active_phase
        
        # Calculate thinking turn count
        thinking_turns = sum(
            1 for m in history 
            if m.role == InterviewMessageRole.INTERVIEWER and m.question_type == DiscussionPhase.THINKING.value
        )
        
        # Force transition to CODING if the candidate has already answered the initial problem description question
        force_coding_transition = (active_phase == DiscussionPhase.THINKING and thinking_turns >= 1)

        if force_coding_transition or analysis.should_transition_topic or analysis.should_transition_section:
            if active_phase == DiscussionPhase.THINKING:
                next_phase = DiscussionPhase.CODING
            elif active_phase == DiscussionPhase.CODING:
                # Do not transition out of CODING phase if the candidate sent a trivial/conversational confirmation
                candidate_text = history[-1].content.strip().lower() if history else ""
                if len(candidate_text) < 15 or candidate_text in ["yes", "sure", "ok", "ready", "yup", "no", "indeed"]:
                    next_phase = DiscussionPhase.CODING
                else:
                    next_phase = DiscussionPhase.COMPLEXITY
            elif active_phase == DiscussionPhase.COMPLEXITY:
                next_phase = DiscussionPhase.OPTIMIZATION
            elif active_phase == DiscussionPhase.OPTIMIZATION:
                # Signal transition to next section in blueprint
                pass

        # 5. Persist turn analysis and response message
        candidate_msg = history[-1] if history else None
        if candidate_msg:
            turn_analysis = InterviewTurnAnalysis(
                message_id=candidate_msg.id,
                technical_accuracy=analysis.technical_accuracy.value,
                depth=analysis.depth.value,
                coverage=analysis.coverage.value,
                communication=analysis.communication.value,
                confidence=analysis.confidence.value,
                missing_topics=analysis.missing_topics,
                strengths=analysis.strengths,
                difficulty_level=current_difficulty.value,
                blueprint_section="Coding (DSA)",
                analysis_version="v1",
            )
            db.add(turn_analysis)

        # Save interviewer response message
        await self.conversation_service.save_message(
            session_id=session.id,
            role=InterviewMessageRole.INTERVIEWER,
            content=agent_response.interviewer_message,
            question_type=next_phase.value,
        )

        return agent_response.interviewer_message

    async def _get_or_create_session_problem(self, db: AsyncSession, session: InterviewSession) -> CodingProblem:
        """Fetches active coding problem, creating a default one if none exists in the repository."""
        # Check if session already has an InterviewQuestion of type CODING
        stmt_q = select(InterviewQuestion).filter(
            InterviewQuestion.session_id == session.id,
            InterviewQuestion.question_type == InterviewType.CODING
        )
        session_q = await db.scalar(stmt_q)
        if session_q and session_q.original_question_bank_id:
            stmt_p = select(CodingProblem).filter(CodingProblem.id == session_q.original_question_bank_id)
            problem = await db.scalar(stmt_p)
            if problem:
                return problem

        # Otherwise, find a coding problem in the bank randomly
        stmt_p = select(CodingProblem).order_by(func.random()).limit(1)
        problem = await db.scalar(stmt_p)

        # Seed missing default problems to ensure a diverse random pool
        stmt_exists = select(CodingProblem.title)
        existing_titles = set((await db.execute(stmt_exists)).scalars().all())
        
        missing_problems = []
        if "Two Sum" not in existing_titles:
            missing_problems.append(CodingProblem(
                title="Two Sum",
                description="Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.",
                question_type=InterviewType.CODING,
                difficulty=DifficultyType.EASY,
                estimated_minutes=15,
                optimal_time_complexity="O(N)",
                optimal_space_complexity="O(N)",
                optimal_solutions={"python": "def twoSum(self, nums, target):\n    seen = {}\n    for i, num in enumerate(nums):\n        diff = target - num\n        if diff in seen:\n            return [seen[diff], i]\n        seen[num] = i\n    return []"},
                function_signatures={"python": "def twoSum(self, nums: List[int], target: int) -> List[int]:"},
                hints=[
                    {"level": "LEVEL_1", "content": "Consider using a hash map to store seen numbers.", "purpose": "Hint on lookup efficiency"}
                ],
                follow_ups=[
                    {"question": "Can you solve it in O(1) extra space if the array is sorted?", "purpose": "Validate scaling design logic", "expected_answer": "Yes, by using two pointers."}
                ],
                topics=["Arrays", "HashMap"],
                companies=["Google", "Meta"],
            ))
        if "Valid Anagram" not in existing_titles:
            missing_problems.append(CodingProblem(
                title="Valid Anagram",
                description="Given two strings s and t, return true if t is an anagram of s, and false otherwise.",
                question_type=InterviewType.CODING,
                difficulty=DifficultyType.EASY,
                estimated_minutes=10,
                optimal_time_complexity="O(N)",
                optimal_space_complexity="O(1)",
                optimal_solutions={"python": "def isAnagram(self, s: str, t: str) -> bool:\n    if len(s) != len(t): return False\n    count = {}\n    for char in s:\n        count[char] = count.get(char, 0) + 1\n    for char in t:\n        if char not in count or count[char] == 0: return False\n        count[char] -= 1\n    return True"},
                function_signatures={"python": "def isAnagram(self, s: str, t: str) -> bool:"},
                hints=[
                    {"level": "LEVEL_1", "content": "Can you count occurrences of each character?", "purpose": "Hint on counting frequencies"}
                ],
                follow_ups=[
                    {"question": "What if the inputs contain Unicode characters? How would you adapt your solution?", "purpose": "Unicode scaling handling", "expected_answer": "We would use a larger hash map or hash table to support Unicode code points."}
                ],
                topics=["Strings", "HashMap"],
                companies=["Amazon", "Uber"],
            ))
        if "Reverse Linked List" not in existing_titles:
            missing_problems.append(CodingProblem(
                title="Reverse Linked List",
                description="Given the head of a singly linked list, reverse the list, and return the reversed list.",
                question_type=InterviewType.CODING,
                difficulty=DifficultyType.EASY,
                estimated_minutes=15,
                optimal_time_complexity="O(N)",
                optimal_space_complexity="O(1)",
                optimal_solutions={"python": "def reverseList(self, head):\n    prev = None\n    curr = head\n    while curr:\n        nxt = curr.next\n        curr.next = prev\n        prev = curr\n        curr = nxt\n    return prev"},
                function_signatures={"python": "def reverseList(self, head: Optional[ListNode]) -> Optional[ListNode]:"},
                hints=[
                    {"level": "LEVEL_1", "content": "Use three pointers: prev, curr, and next to modify links in place.", "purpose": "Pointer tracking hint"}
                ],
                follow_ups=[
                    {"question": "Can you reverse the linked list iteratively and recursively?", "purpose": "Recursion vs Iteration knowledge", "expected_answer": "Yes, recursive uses stack space O(N)."}
                ],
                topics=["LinkedList"],
                companies=["Microsoft", "Meta"],
            ))

        if missing_problems:
            for p in missing_problems:
                db.add(p)
            await db.flush()
            # Re-query a random problem to ensure the newly seeded ones are eligible
            stmt_p = select(CodingProblem).order_by(func.random()).limit(1)
            problem = await db.scalar(stmt_p)

        # Link/snapshot coding problem to the session
        if not session_q:
            session_q = InterviewQuestion(
                session_id=session.id,
                original_question_bank_id=problem.id,
                title=problem.title,
                description=problem.description,
                question_type=InterviewType.CODING,
                order_index=1,
            )
            db.add(session_q)
            await db.flush()

        return problem

    def _determine_discussion_state(self, history: list[InterviewMessage]) -> tuple[DiscussionPhase, HintLevel]:
        """Infers the current DiscussionPhase and HintLevel from interviewer message history."""
        # Find latest interviewer message
        last_interviewer_msg = None
        for msg in reversed(history):
            if msg.role == InterviewMessageRole.INTERVIEWER:
                last_interviewer_msg = msg
                break

        # Check if candidate mentions feeling stuck or asking for hint
        current_hint = HintLevel.NONE
        candidate_msg_count = 0
        for msg in reversed(history):
            if msg.role == InterviewMessageRole.CANDIDATE:
                content_lower = msg.content.lower()
                if "hint" in content_lower or "stuck" in content_lower:
                    current_hint = HintLevel.LEVEL_1
                candidate_msg_count += 1
                if candidate_msg_count >= 1:
                    break

        if not last_interviewer_msg:
            return DiscussionPhase.THINKING, current_hint

        # Resolve phase from saved question type
        q_type = last_interviewer_msg.question_type
        for phase in DiscussionPhase:
            if q_type == phase.value:
                return phase, current_hint

        return DiscussionPhase.THINKING, current_hint
