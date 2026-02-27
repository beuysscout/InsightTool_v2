from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class InsightStatus(str, Enum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    MERGED = "merged"


class EvidenceQuote(BaseModel):
    quote: str
    participant_id: str
    timestamp: str = ""
    session_id: str
    guide_section: str = ""


class HighlightQuote(BaseModel):
    text: str
    participant_id: str
    timestamp: str = ""
    session_id: str
    guide_section: str = ""


class Insight(BaseModel):
    insight_id: str
    theme_group: list[str] = Field(default_factory=list)
    insight_summary: str
    highlight_quote: HighlightQuote
    supporting_evidence: list[EvidenceQuote] = Field(default_factory=list)
    participant_count: int = 0
    total_instances: int = 0
    participants: list[str] = Field(default_factory=list)
    status: InsightStatus = InsightStatus.PROPOSED


class InsightSynthesisResult(BaseModel):
    project_name: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    total_sessions: int = 0
    total_participants: int = 0
    insights: list[Insight] = Field(default_factory=list)
