"""Guide Reviewer Agent.

Parses an uploaded research guide and reviews it for quality.
Flags leading/ambiguous questions, checks objective coverage,
and suggests probe questions.
"""

from __future__ import annotations

import json

import anthropic

from app.config import settings
from app.models.guide import (
    AiFlag,
    AiFlagType,
    GuideReviewResult,
    GuideSection,
    Question,
    ResearchGuide,
)

SYSTEM_PROMPT = """\
You are an expert UX research methodologist. You are reviewing an interview \
guide that a researcher has written for a discovery research study.

Your job:
1. Parse the guide into a structured format with sections, questions, time \
brackets, and objectives.
2. Review each question for quality:
   - Flag leading questions (ones that suggest a preferred answer)
   - Flag ambiguous questions (unclear what is being asked)
   - Flag questions that seem out of scope for the stated objectives
3. Check that every research goal has at least one question mapped to it. \
Flag any gaps.
4. Suggest probe/follow-up questions where depth may be needed.
5. Estimate total session duration based on the number of questions and \
time brackets.

Return your response as valid JSON matching the schema below. Do not include \
any text outside the JSON.

Schema:
{
  "sections": [
    {
      "section_id": "S01",
      "section_name": "string",
      "time_bracket": "0:00-10:00",
      "questions": [
        {
          "question_id": "Q01",
          "question_text": "string",
          "mapped_goal": "goal text or null",
          "required": true,
          "probes": ["string"]
        }
      ]
    }
  ],
  "flags": [
    {
      "flag_type": "leading|ambiguous|out_of_scope|missing_coverage",
      "message": "string",
      "suggestion": "string or null"
    }
  ],
  "suggested_probes": [
    {
      "question_id": "Q01",
      "probe": "string"
    }
  ],
  "coverage_gaps": ["goal text that has no questions"],
  "estimated_duration_minutes": 45
}
"""


async def review_guide(
    guide_text: str,
    project_name: str,
    objective: str = "",
    research_goals: list[str] | None = None,
) -> GuideReviewResult:
    """Send the guide text to Claude for parsing and review."""

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    user_content = f"Project: {project_name}\n"
    if objective:
        user_content += f"Objective: {objective}\n"
    if research_goals:
        user_content += f"Research goals:\n"
        for i, goal in enumerate(research_goals, 1):
            user_content += f"  {i}. {goal}\n"
    user_content += f"\n---\n\nInterview Guide:\n\n{guide_text}"

    message = await client.messages.create(
        model=settings.claude_model,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )

    response_text = message.content[0].text

    # Strip markdown code fences if present
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        lines = lines[1:]  # remove opening fence
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        response_text = "\n".join(lines)

    data = json.loads(response_text)

    # Build structured result
    sections = []
    for s in data.get("sections", []):
        questions = []
        for q in s.get("questions", []):
            questions.append(
                Question(
                    question_id=q["question_id"],
                    question_text=q["question_text"],
                    mapped_goal=q.get("mapped_goal"),
                    required=q.get("required", True),
                    probes=q.get("probes", []),
                )
            )
        sections.append(
            GuideSection(
                section_id=s["section_id"],
                section_name=s["section_name"],
                time_bracket=s.get("time_bracket", ""),
                questions=questions,
            )
        )

    flags = [
        AiFlag(
            flag_type=AiFlagType(f["flag_type"]),
            message=f["message"],
            suggestion=f.get("suggestion"),
        )
        for f in data.get("flags", [])
    ]

    guide = ResearchGuide(
        project_id="",  # filled by caller
        project_name=project_name,
        objective=objective,
        research_goals=research_goals or [],
        sections=sections,
    )

    return GuideReviewResult(
        parsed_guide=guide,
        flags=flags,
        suggested_probes=data.get("suggested_probes", []),
        coverage_gaps=data.get("coverage_gaps", []),
        estimated_duration_minutes=data.get("estimated_duration_minutes"),
    )
