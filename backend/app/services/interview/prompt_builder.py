from typing import Any

from pydantic import BaseModel

from app.models.interview.interview_message import InterviewMessage
from app.models.interview.interview_session import InterviewSession
from app.shared.enums import InterviewMessageRole, InterviewState


class PromptContext(BaseModel):
    """Pydantic schema encapsulating structured inputs for the interviewer LLM context."""

    system_prompt: str
    user_prompt: str
    current_state: str
    current_section: dict[str, Any] | None
    memory_context: str | None
    blueprint_reference: dict[str, Any] | None


class InterviewPromptBuilder:
    """Combines session configuration, candidate profile data, blueprints,
    active state variables, and history sequence turns into a structured PromptContext.
    """

    SYSTEM_INSTRUCTIONS = """You are a professional, elite technical and behavioral interviewer for NextRound.
Your task is to conduct a structured, high-quality interview with the candidate based on their resume, technical profile, and the active blueprint.

CONVERSATION RULES:
1. Greet naturally, introduce yourself, and explain the format of the interview.
2. Ask exactly ONE question at a time. Wait for the candidate's response before proceeding.
3. Ask follow-up questions naturally when appropriate to dig deeper into their answers, but do not get stuck.
4. Transition smoothly between topics as instructed by the active section details.
5. Do NOT reveal the interview blueprint, agenda sections, or future questions.
6. Do NOT give feedback, scores, or evaluation hints during the interview (e.g. do not say "That is correct" or "Good answer"). Keep your response purely conversational.
7. Maintain a professional, friendly, and objective tone.
8. CRITICAL: Never end the interview or thank the candidate for completing the interview unless you are explicitly instructed that the state is "CLOSING".

GROUNDING PRINCIPLES:
- Anchor all candidate-specific project/experience discussions to the candidate's Resume and Candidate Profile. Do not invent or assume resume projects, roles, technologies, or achievements that the candidate has not claimed.
- You are highly encouraged and expected to ask general technical, conceptual, theoretical, or system design questions relevant to the target role (e.g., ML Engineering principles, core algorithms, design trade-offs) and difficulty level, even if those specific concepts are not explicitly written on the candidate's resume.
- Maintain a balance: assess both their specific claimed experiences and their broader domain expertise matching the target role and category.

OUTPUT FORMAT:
You MUST respond ONLY with a valid JSON object in exactly this format:
{"interviewer_message": "<your interviewer response here>"}
Do NOT include any other keys, explanations, or text outside the JSON object.
"""

    def build_prompts(
        self,
        session: InterviewSession,
        history: list[InterviewMessage],
        memory_context: str | None = None,
    ) -> PromptContext:
        """Constructs the system and user prompts and packages them into a PromptContext."""
        state = InterviewState(session.interview_state)
        
        # Load blueprint information
        blueprint = session.blueprint
        blueprint_data = None
        current_sec_data = None

        if blueprint and blueprint.blueprint_json:
            blueprint_data = blueprint.blueprint_json
            sections = blueprint_data.get("sections", [])
            idx = session.current_section_index
            if idx is not None and 0 <= idx < len(sections):
                current_sec_data = sections[idx]

        # Build System Prompt
        sys_prompt = self.SYSTEM_INSTRUCTIONS
        sys_prompt += "\nINTERVIEW CONFIGURATION:\n"
        sys_prompt += f"- Target Role: {session.role.value.upper() if session.role else 'N/A'}\n"
        sys_prompt += f"- Interview Category: {session.interview_category.value.upper()}\n"
        sys_prompt += f"- Difficulty Level: {session.difficulty.value.upper()}\n"
        sys_prompt += f"- Planned Duration: {session.duration_minutes} minutes\n"

        if state == InterviewState.GREETING:
            sys_prompt += "\nCURRENT STATE: GREETING. Welcome the candidate, introduce yourself, and ask for their confirmation to begin.\n"
        elif state == InterviewState.INTRODUCTION:
            sys_prompt += "\nCURRENT STATE: INTRODUCTION. Ask the candidate to introduce themselves briefly, highlighting key technical experiences.\n"
        elif state == InterviewState.IN_PROGRESS:
            sys_prompt += "\nCURRENT STATE: IN_PROGRESS.\n"
            if current_sec_data:
                sys_prompt += (
                    f"ACTIVE BLUEPRINT SECTION:\n"
                    f"- Topic: {current_sec_data.get('name')}\n"
                    f"- Planned Duration: {current_sec_data.get('duration')} minutes\n"
                    f"Action: Guide the conversation to cover this topic. Ask questions and follow-ups. Transition only when state progresses.\n"
                )
        elif state == InterviewState.CLOSING:
            sys_prompt += "\nCURRENT STATE: CLOSING. Conclude the interview naturally, thank the candidate for their time, and tell them they can submit or close the session.\n"
        elif state == InterviewState.COMPLETED:
            sys_prompt += "\nCURRENT STATE: COMPLETED. The interview is finished. Maintain a final polite closing statement.\n"



        # Build User Prompt containing Resume & Profile context and history
        cp_summary = ""
        if session.candidate_profile and session.candidate_profile.profile_json:
            cp_summary = session.candidate_profile.profile_json.get("summary") or session.candidate_profile.profile_json.get("overall_technical_profile") or ""

        user_prompt = f"CANDIDATE TECHNICAL PROFILE SUMMARY:\n{cp_summary}\n\n"
        
        if memory_context:
            user_prompt += f"MEMORY CONTEXT:\n{memory_context}\n\n"

        user_prompt += "CONVERSATION HISTORY:\n"
        if not history:
            user_prompt += "[No messages yet]\n"
        else:
            for msg in history:
                role_label = "Interviewer" if msg.role == InterviewMessageRole.INTERVIEWER else "Candidate"
                user_prompt += f"{role_label}: {msg.content}\n"

        user_prompt += "\nGenerate the next interviewer response following all the guidelines above.\n"
        user_prompt += 'Respond ONLY as a JSON object: {"interviewer_message": "<your response>"}\n'

        return PromptContext(
            system_prompt=sys_prompt,
            user_prompt=user_prompt,
            current_state=state.value,
            current_section=current_sec_data,
            memory_context=memory_context,
            blueprint_reference=blueprint_data,
        )
