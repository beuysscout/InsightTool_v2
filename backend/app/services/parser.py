"""Markdown transcript parser for Askable format.

Parses raw markdown transcripts into canonical Turn objects.
Supports common Askable/interview transcript patterns:
  - "**Speaker Name:** text"
  - "Speaker Name: text"
  - "[00:12:34] Speaker Name: text"
  - Timestamp on separate line followed by speaker line
"""

from __future__ import annotations

import re

from app.models.session import Turn

# Patterns for parsing transcript lines
TIMESTAMP_PATTERN = re.compile(
    r"\[?(\d{1,2}:\d{2}(?::\d{2})?)\]?"
)
SPEAKER_LINE_PATTERN = re.compile(
    r"^(?:\[?(\d{1,2}:\d{2}(?::\d{2})?)\]?\s+)?"  # optional timestamp
    r"\*{0,2}"  # optional bold markers
    r"([A-Za-z][A-Za-z0-9 .'_-]+?)"  # speaker name
    r"\*{0,2}"  # optional bold markers
    r"\s*[:]\s*"  # colon separator
    r"(.+)$",  # spoken text
    re.DOTALL,
)
STANDALONE_TIMESTAMP = re.compile(
    r"^\s*\[?(\d{1,2}:\d{2}(?::\d{2})?)\]?\s*$"
)

# Common interviewer indicators
INTERVIEWER_INDICATORS = [
    "interviewer",
    "moderator",
    "researcher",
    "facilitator",
    "host",
]


def _normalise_timestamp(ts: str) -> str:
    """Normalise timestamp to HH:MM:SS format."""
    parts = ts.split(":")
    if len(parts) == 2:
        return f"00:{parts[0].zfill(2)}:{parts[1].zfill(2)}"
    return f"{parts[0].zfill(2)}:{parts[1].zfill(2)}:{parts[2].zfill(2)}"


def _is_interviewer(speaker: str) -> bool:
    """Heuristic to detect interviewer speaker labels."""
    lower = speaker.lower().strip()
    return any(ind in lower for ind in INTERVIEWER_INDICATORS)


def parse_markdown_transcript(content: str) -> list[Turn]:
    """Parse a markdown transcript into a list of Turn objects.

    Handles multi-line responses by accumulating text until the next
    speaker line is encountered.
    """
    lines = content.split("\n")
    turns: list[Turn] = []
    current_speaker: str | None = None
    current_text_parts: list[str] = []
    current_timestamp = ""
    pending_timestamp = ""
    turn_index = 0

    def _flush():
        nonlocal turn_index
        if current_speaker and current_text_parts:
            text = " ".join(current_text_parts).strip()
            if text:
                turns.append(
                    Turn(
                        turn_index=turn_index,
                        speaker=current_speaker.strip(),
                        text=text,
                        timestamp=current_timestamp,
                        is_interviewer=_is_interviewer(current_speaker),
                    )
                )
                turn_index += 1

    for line in lines:
        stripped = line.strip()

        # Skip empty lines and markdown headers/separators
        if not stripped or stripped.startswith("#") or stripped == "---":
            continue

        # Check for standalone timestamp line
        ts_match = STANDALONE_TIMESTAMP.match(stripped)
        if ts_match:
            pending_timestamp = _normalise_timestamp(ts_match.group(1))
            continue

        # Check for speaker line
        speaker_match = SPEAKER_LINE_PATTERN.match(stripped)
        if speaker_match:
            _flush()
            ts = speaker_match.group(1)
            current_timestamp = (
                _normalise_timestamp(ts) if ts else pending_timestamp
            )
            pending_timestamp = ""
            current_speaker = speaker_match.group(2)
            current_text_parts = [speaker_match.group(3).strip()]
            continue

        # Continuation of current speaker's text
        if current_speaker:
            current_text_parts.append(stripped)

    # Flush the last turn
    _flush()

    return turns
