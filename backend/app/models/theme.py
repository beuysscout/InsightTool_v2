from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ThemeStatus(str, Enum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    MERGED = "merged"
    DISCARDED = "discarded"


class ThemeEvidence(BaseModel):
    quote: str
    participant_id: str
    timestamp: str = ""
    turn_index: int
    guide_section: str = ""
    guide_question_id: str | None = None


class Theme(BaseModel):
    theme_id: str
    theme_name: str
    theme_description: str
    evidence: list[ThemeEvidence] = Field(default_factory=list)
    instance_count: int = 0
    status: ThemeStatus = ThemeStatus.PROPOSED
    researcher_notes: str | None = None


class SessionThemes(BaseModel):
    session_id: str
    participant_id: str
    themes: list[Theme] = Field(default_factory=list)
