"""Theme Extractor Agent.

Works through an organised transcript and surfaces emergent themes
with full traceability — every theme grounded in specific quotes
with participant ID, timestamp, and guide section.
"""

from __future__ import annotations

import json

import anthropic

from app.config import settings
from app.models.session import OrganisedTranscript
from app.models.theme import SessionThemes, Theme, ThemeEvidence, ThemeStatus

SYSTEM_PROMPT = """\
You are an expert qualitative research analyst performing inductive \
thematic analysis on an interview transcript.

Your job:
1. Read through the organised transcript carefully.
2. Identify emergent themes — recurring patterns, notable observations, \
strong sentiments, or significant behaviours expressed by the participant.
3. For each theme:
   - Give it a clear, descriptive name
   - Write a 1-2 sentence description of the pattern
   - List ALL supporting quotes with exact text, timestamp, and which \
guide section they came from
   - Count the number of distinct instances
4. Themes must be grounded in evidence. Never propose a theme without \
at least one verbatim quote.
5. Look for themes across all sections — a theme may span multiple \
guide sections.
6. Also look at off-script responses — they often contain the most \
interesting emergent patterns.

Return your response as valid JSON matching the schema below. Do not \
include any text outside the JSON.

Schema:
{
  "themes": [
    {
      "theme_id": "T01",
      "theme_name": "string",
      "theme_description": "string",
      "evidence": [
        {
          "quote": "exact verbatim quote from transcript",
          "participant_id": "P01",
          "timestamp": "00:12:34",
          "turn_index": 5,
          "guide_section": "section name or Off-script",
          "guide_question_id": "Q01 or null"
        }
      ],
      "instance_count": 3
    }
  ]
}
"""


def _format_organised_transcript(organised: OrganisedTranscript) -> str:
    """Format the organised transcript for the prompt."""
    parts = [f"Participant: {organised.participant_id}\n"]

    for mapping in organised.section_mappings:
        parts.append(
            f"## {mapping.section_name} ({mapping.time_bracket}) "
            f"— {mapping.coverage_status.value}"
        )
        for mt in mapping.mapped_turns:
            ts = f"[{mt.timestamp}] " if mt.timestamp else ""
            parts.append(f"  {ts}(turn {mt.turn_index}): \"{mt.text}\"")
        if mapping.coverage_notes:
            parts.append(f"  Note: {mapping.coverage_notes}")
        parts.append("")

    if organised.off_script_turns:
        parts.append("## Off-script responses")
        for turn in organised.off_script_turns:
            ts = f"[{turn.timestamp}] " if turn.timestamp else ""
            parts.append(f"  {ts}(turn {turn.turn_index}): \"{turn.text}\"")

    return "\n".join(parts)


async def extract_themes(
    organised: OrganisedTranscript,
    session_id: str,
    participant_id: str,
) -> SessionThemes:
    """Send organised transcript to Claude for theme extraction."""

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    user_content = (
        f"Analyse this organised transcript and extract emergent themes.\n\n"
        f"{_format_organised_transcript(organised)}"
    )

    message = await client.messages.create(
        model=settings.claude_model,
        max_tokens=4096,
        temperature=0.3,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )

    response_text = message.content[0].text

    # Strip markdown code fences if present
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        response_text = "\n".join(lines)

    data = json.loads(response_text)

    themes = []
    for t in data.get("themes", []):
        evidence = [
            ThemeEvidence(
                quote=e["quote"],
                participant_id=e.get("participant_id", participant_id),
                timestamp=e.get("timestamp", ""),
                turn_index=e.get("turn_index", 0),
                guide_section=e.get("guide_section", ""),
                guide_question_id=e.get("guide_question_id"),
            )
            for e in t.get("evidence", [])
        ]
        themes.append(
            Theme(
                theme_id=t["theme_id"],
                theme_name=t["theme_name"],
                theme_description=t["theme_description"],
                evidence=evidence,
                instance_count=t.get("instance_count", len(evidence)),
                status=ThemeStatus.PROPOSED,
            )
        )

    return SessionThemes(
        session_id=session_id,
        participant_id=participant_id,
        themes=themes,
    )
