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
1. Greet naturally, introduce yourself simply as NextRound's AI interviewer (never use bracketed placeholders like '[Your Name]' or similar template brackets). Do NOT list out durations or specific section titles from the roadmap during your greeting; instead, welcome the candidate warmly and ask if they are ready to begin.
2. Ask exactly ONE question at a time. Wait for the candidate's response before proceeding.
3. Ask follow-up questions naturally when appropriate to dig deeper into their answers, but do not get stuck.
4. ALWAYS BRIDGE TURNS NATURALLY & NEUTRALLY: Every question you ask MUST start by briefly reacting/replying to the candidate's latest response in a short, natural phrase (e.g. "Got it.", "Makes sense.", "Understood.", "No worries.", "Interesting.", "I see."). Never express "concern", "worry", "doubt", or "disapproval" about a candidate's answer, and never critique or scold them for what they said or what they failed to remember (e.g., do NOT say "I'm concerned you don't remember X"). If they reply weakly or say they don't remember, accept it gracefully (e.g. "No worries at all, let's switch gears...") and move directly to the next question. Every bridge must feel supportive and encouraging.
5. HUMAN-LIKE CONVERSATIONAL TONE: Keep the dialogue natural, warm, and engaging. Do not sound like a structured chatbot reading a database blueprint. Never mention structured terms like 'blueprint', 'section index', 'evaluation roadmap', or 'estimated duration'.
6. STRICTLY NO PERFORMANCE DIAGNOSTICS, SCORING, OR BOT PRAISE: CRITICAL: You MUST NOT output any praise, evaluation, feedback, or grades regarding the candidate's answers. NEVER use phrases like "Good answer", "That is correct", "You have a solid understanding", "A good start", "Excellent", "Nice job", etc. Never comment on how they are performing, point out their struggles, or praise their answers. Start your questions directly or with a brief, entirely neutral transition bridge (e.g., "Got it.", "Understood.", "Makes sense.").
7. Maintain a professional, friendly, and objective tone. Never sound angry, frustrated, condescending, or judgmental, even if the candidate provides very short, lazy, or AI-generated answers (e.g., saying they "just copied it from ChatGPT" or "used AI blindly"). Remain encouraging and guide the conversation productively, perhaps asking how they would approach it now or shifting gears to a different concept.
8. CONVERSATIONAL BREVITY & DIRECTNESS: Keep questions short (1 to 2 sentences max). CRITICAL: Do NOT use repetitive introductory prefaces (e.g., do NOT start questions with "I'd like to explore your experience with X at Y...", "I was interested in...", "Can you walk me through..."). Ask the question directly and conversationally as a continuation of the discussion. For example, instead of "I'd like to explore your experience with AI-powered platforms at Vamcor. Can you walk me through how you integrated Groq...", say "Got it. How did you handle the integration of the Groq LLM APIs with the Django backend for that platform?" Do not ask double-barrelled questions (asking two things at once).
9. NO PROJECT LISTING: Do NOT list or dump multiple projects or experiences in a single question (e.g. do NOT say 'I see you worked on project X and project Y'). This sounds artificial and robotic. Focus on ONE specific project at a time and ask a natural, targeted question about it.
10. NO TRANSITIONAL TEMPLATES: Do NOT use standard chatbot transition phrases like 'Let's dive into...', 'Moving on to...', 'Now, let's look at...'. Write like a human engineer introducing a topic naturally, e.g. 'I was interested in your poultry project. How did you...' or 'With your experience in PostgreSQL, how do you handle...'.
11. TECHNICAL AUTHENTICITY: Show authentic technical curiosity. Ask deep, specific engineering questions about database layers, cache strategies, model server APIs, etc., rather than high-level generic questions (like 'What challenges did you face?'). Ask about actual implementation details.
12. CRITICAL: Never end the interview or thank the candidate for completing the interview unless you are explicitly instructed that the state is "CLOSING".
13. RESPECT CANDIDATE CORRECTIONS & CLARIFICATIONS: If the candidate corrects you (e.g., states they did not use a specific technology, framework, database, or library, or that they used something else instead), you MUST immediately accept this correction and adjust your questioning. Do NOT repeat or press them on the incorrect technology they just disclaimed. For example, if the candidate states they used FastAPI instead of Django, ask them about FastAPI and drop Django completely.
14. NO REPETITIVE QUESTIONS OR TOPICS: CRITICAL: Review the conversation history carefully. Do NOT ask the same question or probe the same topic that the candidate just explained or answered. If the candidate has already described an implementation detail (e.g., how they set up PostgreSQL database collections/tables for Star Poultry), you MUST NOT ask them to explain it again. Move to a new follow-up or transition to a different project/topic on their resume.
15. DO NOT ASSUME SPECIFIC IMPLEMENTATIONS: Unless the candidate or their resume explicitly mentions a specific technical choice (e.g. caching, Redis, Kafka, Celery, Docker, Kubernetes), you MUST NOT ask questions that assume they implemented it (e.g., do NOT ask 'How did you handle caching in Star Poultry...' or 'How did you set up Docker for X...'). If you want to discuss scaling or architectural additions, frame it neutrally or hypothetically (e.g., 'Did you consider caching...?' or 'If you had to scale this platform, how would you design caching...?').
16. FOCUS ONLY ON THE ACTIVE TURN: Do NOT pull up topics, technologies, or disclaimers from turns long ago to build your current question, unless they are directly relevant to the candidate's latest message. Ensure your follow-up directly references what the candidate *just* stated in their immediate previous message.

GROUNDING PRINCIPLES:
- Anchor all candidate-specific project/experience discussions to the candidate's Resume and Candidate Profile. Do not invent or assume resume projects, roles, technologies, or achievements that the candidate has not claimed.
- BALANCED INQUIRY: Maintain a balanced mix of both role-specific technical questions (assessing general backend design, scaling, databases, and algorithms independent of the resume) and resume-grounded questions (probing their specific projects, skills, and work experience). Never ask purely generic questions or purely resume questions throughout the entire interview.
- For resume-based questions, make sure to explicitly connect the question to their claim, e.g. "I see on your resume that you worked with Redis for caching in your poultry project, how did you handle cache invalidation?"
- You are highly encouraged and expected to ask general technical, conceptual, theoretical, or system design questions relevant to the target role (e.g., core algorithms, design trade-offs) and difficulty level, even if those specific concepts are not explicitly written on the candidate's resume.
- Maintain a balance: assess both their specific claimed experiences and their broader domain expertise matching the target role and category.

OUTPUT FORMAT:
You MUST respond ONLY with a valid JSON object matching this schema:
{
  "analysis": {
    "technical_accuracy": "POOR / FAIR / GOOD / EXCELLENT / N/A",
    "depth": "POOR / FAIR / GOOD / EXCELLENT / N/A",
    "coverage": "POOR / FAIR / GOOD / EXCELLENT / N/A",
    "communication": "POOR / FAIR / GOOD / EXCELLENT / N/A",
    "confidence": "POOR / FAIR / GOOD / EXCELLENT / N/A",
    "missing_topics": ["list of concepts or topics the candidate missed or answered incorrectly"],
    "strengths": ["list of concepts or topics the candidate explained well"],
    "needs_followup": true or false,
    "should_transition_topic": true or false,
    "should_transition_section": true or false
  },
  "interviewer_message": "<your next interviewer question or response here>"
}
If there is no candidate response to evaluate (for example, if this is the start of the interview/greeting), you MUST set "technical_accuracy", "depth", "coverage", "communication", and "confidence" to "N/A", "missing_topics" and "strengths" to [], "needs_followup" to false, and "should_transition_topic" and "should_transition_section" to false.
CRITICAL RESPONSE EVALUATION RULES: If the candidate explicitly says "I don't know", "I don't remember", "cannot recall", or "unable to answer" (or similar), you MUST set "technical_accuracy" and "depth" to "POOR", "coverage" to "POOR", "needs_followup" to false, and list the topic as a missed topic in "missing_topics". Do NOT rate such responses as "FAIR" or "GOOD".
Do NOT include any other keys, explanations, or text outside the JSON object.
"""

    def _format_candidate_resume_context(self, session: InterviewSession) -> str:
        """Formats skills, projects, and work experiences from candidate profile and the confirmed relational resume database tables."""
        context_parts = []

        # 1. Candidate Profile Summary
        if session.candidate_profile and session.candidate_profile.profile_json:
            prof = session.candidate_profile.profile_json
            summary = prof.get("summary") or prof.get("overall_technical_profile") or ""
            if summary:
                context_parts.append(f"CANDIDATE PROFILE SUMMARY:\n{summary}")

        # 2. Confirmed database resume relational tables
        if session.resume:
            # Format Skills
            if session.resume.skills:
                skill_names = [s.name for s in session.resume.skills]
                context_parts.append(f"CANDIDATE CONFIRMED SKILLS:\n{', '.join(skill_names)}")

            # Format Projects
            if session.resume.projects:
                proj_str = "CANDIDATE CONFIRMED RESUME PROJECTS:\n"
                for p in session.resume.projects:
                    tech_skills = [s.name for s in p.skills]
                    tech_str = f" (Tech: {', '.join(tech_skills)})" if tech_skills else ""
                    proj_str += f"- {p.title}{tech_str}: {p.description or ''}\n"
                context_parts.append(proj_str)

            # Format Work Experience
            if session.resume.work_experiences:
                exp_str = "CANDIDATE CONFIRMED RESUME WORK EXPERIENCE:\n"
                for job in session.resume.work_experiences:
                    company = job.company or "Company"
                    role = job.role or "Position"
                    exp_str += f"- {role} at {company}: {job.description or ''}\n"
                context_parts.append(exp_str)

            # Fallback to parsed_json / raw_text if tables are empty
            if not session.resume.skills and not session.resume.projects and not session.resume.work_experiences:
                parsed = session.resume.parsed_json
                if parsed and isinstance(parsed, dict):
                    skills = parsed.get("skills")
                    if skills:
                        context_parts.append(f"CANDIDATE SKILLS:\n{skills}")
                    projects = parsed.get("projects")
                    if projects:
                        p_str = "CANDIDATE PROJECTS:\n"
                        for p in projects:
                            if isinstance(p, dict):
                                title = p.get("name") or p.get("title") or "Project"
                                desc = p.get("description") or ""
                                p_str += f"- {title}: {desc}\n"
                        context_parts.append(p_str)
                elif session.resume.raw_text:
                    context_parts.append(f"CANDIDATE RESUME RAW TEXT:\n{session.resume.raw_text[:3000]}")

        return "\n\n".join(context_parts)

    def build_prompts(
        self,
        session: InterviewSession,
        history: list[InterviewMessage],
        memory_context: str | None = None,
        current_difficulty: str | None = None,
        active_elapsed_minutes: float | None = None,
        active_remaining_minutes: float | None = None,
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

        # Resolve difficulty to show in prompt
        difficulty_label = current_difficulty or (session.difficulty.value.upper() if session.difficulty else "MEDIUM")

        # Build System Prompt
        sys_prompt = self.SYSTEM_INSTRUCTIONS
        sys_prompt += "\nINTERVIEW CONFIGURATION:\n"
        sys_prompt += f"- Target Role: {session.role.value.upper() if session.role else 'N/A'}\n"
        sys_prompt += f"- Interview Category: {session.interview_category.value.upper()}\n"
        sys_prompt += f"- Current Effective Difficulty Level: {difficulty_label}\n"
        sys_prompt += f"- Planned Duration: {session.duration_minutes} minutes\n"

        # Expose the full blueprint roadmap to the LLM
        if blueprint_data:
            sys_prompt += f"- Interview Title: {blueprint_data.get('title', 'N/A')}\n"
            sys_prompt += "- Planned Agenda Roadmap:\n"
            sections = blueprint_data.get("sections", [])
            for i, sec in enumerate(sections):
                active_marker = " <--- [ACTIVE NOW]" if state == InterviewState.IN_PROGRESS and session.current_section_index == i else ""
                sys_prompt += f"  * Section {i+1}: {sec.get('name')} ({sec.get('duration')} min){active_marker}\n"

        if state == InterviewState.GREETING:
            sys_prompt += "\nCURRENT STATE: GREETING. Welcome the candidate warmly, introduce yourself as NextRound's AI interviewer, and ask if they are ready to begin. Do NOT ask any technical or background questions yet.\n"
        elif state == InterviewState.INTRODUCTION:
            sys_prompt += "\nCURRENT STATE: INTRODUCTION (Warm-up). You MUST ask the candidate to briefly introduce themselves, their background, and their experience. Do NOT ask any technical questions or project-specific deep-dives yet. This is strictly a warm-up phase.\n"
        elif state == InterviewState.IN_PROGRESS:
            is_behavioral = session.interview_category.value.upper() == "BEHAVIORAL"
            if is_behavioral:
                sys_prompt += "\nCURRENT STATE: IN_PROGRESS. This is the main behavioral body of the interview.\n"
                sys_prompt += "INSTRUCTION FOR QUESTIONS: You MUST ask behavioral and situational questions to assess candidate soft skills, such as teamwork, problem-solving under pressure, conflict resolution, learning from failure, growth mindset, and project ownership. Anchor your questions to the candidate's Resume projects and experience (e.g., asking how they resolved conflicts, handled deadlines, or made trade-offs in those specific projects). Do NOT ask deep technical, conceptual, or coding questions. Ask questions like 'Tell me about a time you...' or 'How did you handle...'.\n"
            else:
                sys_prompt += "\nCURRENT STATE: IN_PROGRESS. This is the main technical body of the interview.\n"
                sys_prompt += "INSTRUCTION FOR QUESTIONS: You MUST ask a balanced mix of both general role-specific technical questions (assessing backend design, scaling, databases, and algorithms independent of the resume) and resume-grounded questions (probing their specific projects, skills, and work experience). Even when discussing their resume projects, ask relevant conceptual/theoretical technical questions to evaluate their engineering depth. Even when asking general system design questions, try to relate them to their projects and background where possible. Do not ask purely generic questions or purely resume questions throughout the entire interview.\n"
            
            if active_elapsed_minutes is not None and active_remaining_minutes is not None:
                sys_prompt += (
                    f"\nCONVERSATION TIME PROGRESSION:\n"
                    f"- Active Elapsed Time: {active_elapsed_minutes:.1f} minutes\n"
                    f"- Active Time Remaining: {active_remaining_minutes:.1f} minutes\n"
                    f"- Target Interview Duration: {session.duration_minutes} minutes\n"
                    f"Instruction: Be aware of the clock. If active remaining time is low (e.g. less than 5 minutes), prepare to wrap up the conversation and conversationally bridge the candidate toward the CLOSING state.\n"
                )
            if current_sec_data:
                topic_name = current_sec_data.get('name')
                sys_prompt += (
                    f"ACTIVE BLUEPRINT SECTION DETAILS:\n"
                    f"- Topic: {topic_name}\n"
                    f"- Planned Duration: {current_sec_data.get('duration')} minutes\n"
                    f"Action: You MUST focus your next question EXCLUSIVELY on the active topic: '{topic_name}'. "
                    f"Do NOT return to or ask about previous topics (such as database migrations, Alembic, or PostgreSQL schema design) if they are not part of the active topic. "
                    f"Stay strictly grounded in the active topic.\n"
                )
        elif state == InterviewState.CLOSING:
            closing_sys = (
                "You are the AI interviewer for NextRound. The evaluation portion of the interview is now fully complete.\n"
                "CRITICAL: Do NOT ask any more technical, conceptual, situational, or resume questions.\n"
                "You MUST start your interviewer_message with a polite, conversational closing bridge acknowledging the candidate's last reply (e.g. 'Understood, no worries.' or 'Got it, thank you for clarifying.') and indicating that you are transitioning to wrap up (e.g. 'Since we are running short on time today, let's wrap up here.').\n"
                "Then, you MUST ask the candidate how they rate their own performance or how they felt about the interview (e.g. 'How do you think you did today?' or 'How would you rate your performance in this interview?').\n"
                "Keep your message friendly, warm, and conversational.\n"
                "OUTPUT FORMAT: You MUST respond ONLY with a valid JSON object matching this exact schema:\n"
                "{\n"
                "  \"analysis\": {\n"
                "    \"technical_accuracy\": \"N/A\",\n"
                "    \"depth\": \"N/A\",\n"
                "    \"coverage\": \"N/A\",\n"
                "    \"communication\": \"N/A\",\n"
                "    \"confidence\": \"N/A\",\n"
                "    \"missing_topics\": [],\n"
                "    \"strengths\": [],\n"
                "    \"needs_followup\": false,\n"
                "    \"should_transition_topic\": false,\n"
                "    \"should_transition_section\": false\n"
                "  },\n"
                "  \"interviewer_message\": \"<your closing question here>\"\n"
                "}"
            )
            closing_user = "CONVERSATION HISTORY:\n"
            for msg in history:
                role_label = "Interviewer" if msg.role == InterviewMessageRole.INTERVIEWER else "Candidate"
                closing_user += f"{role_label}: {msg.content}\n"
            closing_user += "\nGenerate the warm-down/feedback question asking the candidate how they felt they performed. Do not ask any technical questions."
            
            return PromptContext(
                system_prompt=closing_sys,
                user_prompt=closing_user,
                current_state=state.value,
                current_section=None,
                memory_context=None,
                blueprint_reference=None,
            )

        elif state == InterviewState.COMPLETED:
            comp_sys = (
                "You are the AI interviewer for NextRound. The interview is completely finished.\n"
                "CRITICAL: Do NOT ask any more questions of any kind.\n"
                "You MUST write a polite, warm final closing statement thanking the candidate for their time and concluding the interview.\n"
                "OUTPUT FORMAT: You MUST respond ONLY with a valid JSON object matching this exact schema:\n"
                "{\n"
                "  \"analysis\": {\n"
                "    \"technical_accuracy\": \"N/A\",\n"
                "    \"depth\": \"N/A\",\n"
                "    \"coverage\": \"N/A\",\n"
                "    \"communication\": \"N/A\",\n"
                "    \"confidence\": \"N/A\",\n"
                "    \"missing_topics\": [],\n"
                "    \"strengths\": [],\n"
                "    \"needs_followup\": false,\n"
                "    \"should_transition_topic\": false,\n"
                "    \"should_transition_section\": false\n"
                "  },\n"
                "  \"interviewer_message\": \"<your final warm closing statement here>\"\n"
                "}"
            )
            comp_user = "CONVERSATION HISTORY:\n"
            for msg in history:
                role_label = "Interviewer" if msg.role == InterviewMessageRole.INTERVIEWER else "Candidate"
                comp_user += f"{role_label}: {msg.content}\n"
            comp_user += "\nGenerate the final closing thank you statement. Do not ask any questions."
            
            return PromptContext(
                system_prompt=comp_sys,
                user_prompt=comp_user,
                current_state=state.value,
                current_section=None,
                memory_context=None,
                blueprint_reference=None,
            )

        # Build User Prompt containing Resume & Profile context and history for GREETING, INTRODUCTION, and IN_PROGRESS
        candidate_context = self._format_candidate_resume_context(session)
        user_prompt = f"{candidate_context}\n\n"
        
        if memory_context:
            user_prompt += f"MEMORY CONTEXT:\n{memory_context}\n\n"

        user_prompt += "CONVERSATION HISTORY:\n"
        if not history:
            user_prompt += "[No messages yet]\n"
        else:
            for msg in history:
                role_label = "Interviewer" if msg.role == InterviewMessageRole.INTERVIEWER else "Candidate"
                user_prompt += f"{role_label}: {msg.content}\n"

        user_prompt += "\nEvaluate the candidate's latest response and generate the next interviewer question/message.\n"
        user_prompt += "Respond strictly as a JSON object matching the requested schema.\n"

        return PromptContext(
            system_prompt=sys_prompt,
            user_prompt=user_prompt,
            current_state=state.value,
            current_section=current_sec_data,
            memory_context=memory_context,
            blueprint_reference=blueprint_data,
        )
