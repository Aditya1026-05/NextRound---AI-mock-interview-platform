from typing import Any
from pydantic import BaseModel

from app.services.interview.coding_context import CodingContext

class CodingPromptContext(BaseModel):
    """Pydantic schema encapsulating structured inputs for the coding interviewer LLM context."""

    system_prompt: str
    user_prompt: str
    discussion_phase: str
    current_hint_level: str


class CodingPromptBuilder:
    """Combines active CodingContext attributes and history into structured prompts for coding interviews."""

    SYSTEM_INSTRUCTIONS = """You are a professional, elite technical interviewer for NextRound.
Your task is to conduct a structured coding interview with the candidate based on the active coding problem.

CONVERSATION RULES:
1. Ask exactly ONE question or prompt at a time. Wait for the candidate's response.
2. ALWAYS BRIDGE TURNS NATURALLY & NEUTRALLY: React/reply to the candidate's latest response in a short, natural phrase (e.g. "Got it.", "Makes sense.", "Understood.", "No worries."). Never critique or express disapproval.
3. STRICTLY NO PERFORMANCE DIAGNOSTICS OR SCORING: Do NOT output praise, grades, or evaluations regarding their answer. NEVER use phrases like "Good answer", "That is correct", etc.
4. Keep questions/messages concise (1 to 2 sentences max). Ask follow-ups naturally.
5. Guide the candidate systematically through the active discussion phase. Do not skip phases.
6. If the hint level is set, you should incorporate the hint content into your interviewer message to guide them, without saying "Here is hint level X". Frame it naturally as a hint or clue.

OUTPUT FORMAT:
You MUST respond ONLY with a valid JSON object matching this schema:
{
  "analysis": {
    "technical_accuracy": "POOR / FAIR / GOOD / EXCELLENT / N/A",
    "depth": "POOR / FAIR / GOOD / EXCELLENT / N/A",
    "coverage": "POOR / FAIR / GOOD / EXCELLENT / N/A",
    "communication": "POOR / FAIR / GOOD / EXCELLENT / N/A",
    "confidence": "POOR / FAIR / GOOD / EXCELLENT / N/A",
    "missing_topics": ["concepts missed or incorrect"],
    "strengths": ["concepts explained well"],
    "needs_followup": true or false,
    "should_transition_topic": true or false,
    "should_transition_section": true or false
  },
  "interviewer_message": "<your next interviewer question or response here>"
}
Do NOT include any other keys or text outside the JSON object.
"""

    def build_prompts(self, context: CodingContext) -> CodingPromptContext:
        """Translates a CodingContext into system and user prompts for the InterviewerAgent."""
        problem = context.active_problem
        
        # Build base system prompt injecting problem description and phase guidelines
        sys_prompt = self.SYSTEM_INSTRUCTIONS + f"\n\nACTIVE PROBLEM:\nTitle: {problem.title}\nDescription:\n{problem.description}\n"
        sys_prompt += f"Optimal Time Complexity: {problem.optimal_time_complexity}\n"
        sys_prompt += f"Optimal Space Complexity: {problem.optimal_space_complexity}\n"
        
        # Phase specific system guidelines
        phase_guidelines = ""
        if context.discussion_phase.value == "THINKING":
            phase_guidelines = (
                "CURRENT PHASE: THINKING.\n"
                "The candidate should describe their thought process, algorithmic approach, and edge cases before writing code.\n"
                "Focus on validating their high-level logic. Do not ask them to write code yet."
            )
        elif context.discussion_phase.value == "CODING":
            phase_guidelines = (
                "CURRENT PHASE: CODING.\n"
                "The candidate is expected to write or refine their code. Ask them to write out the method implementation."
            )
        elif context.discussion_phase.value == "COMPLEXITY":
            phase_guidelines = (
                "CURRENT PHASE: COMPLEXITY.\n"
                "Prompt the candidate to explain the time and space complexity of their proposed solution."
            )
        elif context.discussion_phase.value == "OPTIMIZATION":
            phase_guidelines = (
                "CURRENT PHASE: OPTIMIZATION.\n"
                "Challenge the candidate with optimization follow-ups or ask them about potential bottlenecks."
            )

        sys_prompt += f"\n{phase_guidelines}\n"

        # Inject Hint if applicable
        if context.current_hint_level.value != "NONE":
            hint_txt = ""
            for hint in problem.hints:
                # hints are CodingHint objects or raw dicts depending on serialization. Support both.
                h_level = hint.level if hasattr(hint, "level") else hint.get("level")
                h_content = hint.content if hasattr(hint, "content") else hint.get("content")
                if h_level == context.current_hint_level or h_level == context.current_hint_level.value:
                    hint_txt = h_content
                    break
            if hint_txt:
                sys_prompt += f"\nACTIVE HINT TO INJECT: {hint_txt}\n"

        # Build user prompt
        user_prompt = "CONVERSATION HISTORY:\n"
        if not context.transcript:
            user_prompt += "[No messages yet]\n"
        else:
            for msg in context.transcript:
                role = msg.get("role", "Candidate")
                content = msg.get("content", "")
                user_prompt += f"{role}: {content}\n"

        user_prompt += f"\nEvaluate response and generate next question matching the {context.discussion_phase.value} phase.\n"

        return CodingPromptContext(
            system_prompt=sys_prompt,
            user_prompt=user_prompt,
            discussion_phase=context.discussion_phase.value,
            current_hint_level=context.current_hint_level.value,
        )
