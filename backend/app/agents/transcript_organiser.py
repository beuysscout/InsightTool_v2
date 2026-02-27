"""Transcript Organiser Agent.

Maps anonymised transcript turns against the locked research guide sections.
Uses time brackets as a primary signal, supplemented by semantic matching
via Claude.
"""

from __future__ import annotations

import json

import anthropic

from app.config import settings
from app.models.guide import ResearchGuide
from app.models.session import (
    CoverageStatus,
    MappedTurn,
    OrganisedTranscript,
    SectionMapping,
    Turn,
)

SYSTEM_PROMPT = """\
You are an expert qualitative research analyst. You are organising an \
interview transcript against a research guide.

Your job:
1. Map each participant response (non-interviewer turn) to the most \
relevant guide section based on:
   - Time brackets (primary signal — if a response falls within a \
section's time range, it likely belongs there)
   - Content relevance (semantic match between the response and the \
section's questions)
2. For each section, determine coverage status:
   - "covered" — at least one substantive response maps to this section
   - "partial" — responses touch on the section but lack depth
   - "not_covered" — no responses map to this section
3. If a section is not covered, provide a brief note explaining why \
(e.g. "Ran long on previous section", "Question was skipped").
4. Identify off-script responses — participant turns that don't map to \
any guide section.
5. Assign a mapping_confidence (0.0 to 1.0) for each mapped turn.

Return your response as valid JSON matching the schema below. Do not \
include any text outside the JSON.

Schema:
{
  "section_mappings": [
    {
      "section_id": "S01",
      "section_name": "string",
      "time_bracket": "0:00-10:00",
      "coverage_status": "covered|partial|not_covered",
      "mapped_turns": [
        {
          "turn_index": 0,
          "speaker": "string",
          "text": "string",
          "timestamp": "00:00:00",
          "mapping_confidence": 0.95
        }
      ],
      "coverage_notes": "string"
    }
  ],
  "off_script_turns": [
    {
      "turn_index": 0,
      "speaker": "string",
      "text": "string",
      "timestamp": "00:00:00"
    }
  ]
}
"""


def _format_guide_for_prompt(guide: ResearchGuide) -> str:
    """Format the guide into a readable text block for the prompt."""
    parts = []
    for section in guide.sections:
        parts.append(f"## {section.section_id}: {section.section_name}")
        if section.time_bracket:
            parts.append(f"   Time bracket: {section.time_bracket}")
        for q in section.questions:
            marker = "[Required]" if q.required else "[Optional]"
            parts.append(f"   - {q.question_id}: {q.question_text} {marker}")
            if q.mapped_goal:
                parts.append(f"     Goal: {q.mapped_goal}")
        parts.append("")
    return "\n".join(parts)


def _format_transcript_for_prompt(turns: list[Turn]) -> str:
    """Format transcript turns into a readable text block."""
    parts = []
    for turn in turns:
        role = "INTERVIEWER" if turn.is_interviewer else "PARTICIPANT"
        ts = f"[{turn.timestamp}] " if turn.timestamp else ""
        parts.append(f"{ts}{role} (turn {turn.turn_index}): {turn.text}")
    return "\n".join(parts)


async def organise_transcript(
    turns: list[Turn],
    guide: ResearchGuide,
    session_id: str,
    participant_id: str,
) -> OrganisedTranscript:
    """Send transcript and guide to Claude for organisation."""

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    user_content = (
        f"## Research Guide\n\n"
        f"{_format_guide_for_prompt(guide)}\n\n"
        f"---\n\n"
        f"## Transcript (Participant {participant_id})\n\n"
        f"{_format_transcript_for_prompt(turns)}"
    )

    message = await client.messages.create(
        model=settings.claude_model,
        max_tokens=8192,
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

    section_mappings = []
    for sm in data.get("section_mappings", []):
        mapped_turns = [
            MappedTurn(
                turn_index=mt["turn_index"],
                speaker=mt["speaker"],
                text=mt["text"],
                timestamp=mt.get("timestamp", ""),
                mapping_confidence=mt.get("mapping_confidence", 0.0),
            )
            for mt in sm.get("mapped_turns", [])
        ]
        section_mappings.append(
            SectionMapping(
                section_id=sm["section_id"],
                section_name=sm["section_name"],
                time_bracket=sm.get("time_bracket", ""),
                coverage_status=CoverageStatus(sm["coverage_status"]),
                mapped_turns=mapped_turns,
                coverage_notes=sm.get("coverage_notes", ""),
            )
        )

    off_script = [
        Turn(
            turn_index=t["turn_index"],
            speaker=t["speaker"],
            text=t["text"],
            timestamp=t.get("timestamp", ""),
        )
        for t in data.get("off_script_turns", [])
    ]

    return OrganisedTranscript(
        session_id=session_id,
        participant_id=participant_id,
        section_mappings=section_mappings,
        off_script_turns=off_script,
    )
