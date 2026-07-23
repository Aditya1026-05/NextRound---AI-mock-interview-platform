from app.services.interview.evaluation_context import EvaluationContext


class EvaluationPromptBuilder:
    """Compiles evaluation inputs, transcripts, scores, and recommendations into a structured evaluation prompt."""

    SYSTEM_INSTRUCTIONS = """You are a senior technical and behavioral interview evaluator for NextRound.
Your task is to analyze the candidate's complete mock interview session and synthesize qualitative feedback.

CRITICAL INSTRUCTIONS:
1. The backend has already computed the final overall score and recommendation deterministically. You MUST accept these values as absolute truth. You are NOT allowed to override, recalculate, or contradict them.
   - Deterministic Overall Score: {overall_score}/100
   - Deterministic Recommendation: {recommendation}
2. Your primary job is to write a cohesive, professional `summary` justifying the backend-calculated performance. Do NOT include generic congratulations. Focus on a clear qualitative synthesis (3-4 sentences maximum).
3. In the "timeline_reviews" list, you MUST generate reviews ONLY for actual technical questions asked by the interviewer (types: PRIMARY, FOLLOW_UP, CLARIFICATION). Do NOT generate review items for greetings, warm-up/introductions, or closing remarks.
4. For each technical question review, you MUST be extremely concise:
   - Provide a highly brief `ideal_answer` (2 sentences maximum).
   - Evaluate the candidate's actual reply against the ideal answer (`evaluation`), keeping it brief (1-2 sentences maximum).
   - List the candidate's concrete `strengths` (maximum 2 items, very short).
   - List specific areas for `improvements` (maximum 2 items, very short).
5. Output your response strictly as a valid JSON object matching the requested schema. Do not include any other markdown formatting outside the JSON block.
"""

    def format_transcript_context(self, context: EvaluationContext) -> str:
        """Formats the transcript and corresponding turn analysis metrics for LLM evaluation."""
        result = []
        analyses_by_msg = {str(a["message_id"]): a for a in context.turn_analyses}

        # Keep track of last interviewer message to show the question-answer pairing context clearly
        last_interviewer_id = None
        
        for msg in context.transcript:
            role = msg["role"].upper()
            content = msg["content"]
            msg_id = str(msg["id"])
            q_type = msg.get("question_type") or "PRIMARY"

            if role == "INTERVIEWER":
                last_interviewer_id = msg_id
                result.append(f"[QUESTION - Type: {q_type} - Msg ID: {msg_id}]")
                result.append(content)
            elif role == "CANDIDATE":
                result.append(f"[ANSWER - Msg ID: {msg_id} - Response to Question ID: {last_interviewer_id}]")
                result.append(content)

                # Format turn observations
                if msg_id in analyses_by_msg:
                    a = analyses_by_msg[msg_id]
                    result.append(
                        f"  -> Metrics: Accuracy={a.get('technical_accuracy')}, "
                        f"Depth={a.get('depth')}, Coverage={a.get('coverage')}, "
                        f"Communication={a.get('communication')}, Confidence={a.get('confidence')}"
                    )
                    if a.get("strengths"):
                        result.append(f"  -> Strengths: {', '.join(a['strengths'])}")
                    if a.get("missing_topics"):
                        result.append(f"  -> Gaps: {', '.join(a['missing_topics'])}")
            result.append("")
        return "\n".join(result)

    def build_prompts(self, context: EvaluationContext) -> tuple[str, str]:
        """Returns the compiled (system_prompt, user_prompt) pair for the LLM call."""
        system_prompt = self.SYSTEM_INSTRUCTIONS.format(
            overall_score=context.overall_score,
            recommendation=context.recommendation,
        )

        formatted_transcript = self.format_transcript_context(context)

        user_prompt = (
            f"Please generate the qualitative evaluation report for the following session:\n"
            f"- Interview Category: {context.interview_category.upper()}\n"
            f"- Overall Score: {context.overall_score}/100\n"
            f"- Recommendation: {context.recommendation}\n"
            f"- Dimension Scores:\n"
        )
        for skill, score in context.skill_scores.items():
            user_prompt += f"  * {skill}: {score:.1f} stars\n"

        user_prompt += (
            f"\n--- INTERVIEW TRANSCRIPT WITH TURN ANALYSIS ---\n"
            f"{formatted_transcript}\n"
            f"--- END OF TRANSCRIPT ---\n\n"
            f"Please output a JSON object containing:\n"
            f"1. \"summary\": A clear qualitative justification summarizing their performance based on the score and recommendation.\n"
            f"2. \"timeline_reviews\": A JSON list of objects for each question message ID, detailing:\n"
            f"   - \"message_id\": The interviewer's question message ID.\n"
            f"   - \"ideal_answer\": The comprehensive correct reference answer.\n"
            f"   - \"evaluation\": A short qualitative critique of the candidate's reply.\n"
            f"   - \"strengths\": Strengths observed in their answer.\n"
            f"   - \"improvements\": Points of improvements.\n"
        )

        return system_prompt, user_prompt
