from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class Turn(BaseModel):
    turn_index: int
    speaker: str
    text: str
    timestamp: str = ""  # e.g. "00:12:34"
    is_interviewer: bool = False


class SessionStatus(str, Enum):
    UPLOADED = "uploaded"
    ANONYMISED = "anonymised"
    ORGANISED = "organised"
    THEMED = "themed"
    COMPLETE = "complete"


class PiiDetection(BaseModel):
    original_text: str
    replacement_token: str  # e.g. [PARTICIPANT], [NAME], [EMAIL]
    pii_type: str
    confidence: float
    start_offset: int
    end_offset: int
    turn_index: int
    status: str = "pending"  # pending | redacted | kept


class AnonymisationLog(BaseModel):
    auto_redacted: int = 0
    researcher_reviewed: int = 0
    exclusions: int = 0
    detections: list[PiiDetection] = Field(default_factory=list)


class CoverageStatus(str, Enum):
    COVERED = "covered"
    PARTIAL = "partial"
    NOT_COVERED = "not_covered"


class MappedTurn(BaseModel):
    turn_index: int
    speaker: str
    text: str
    timestamp: str = ""
    mapping_confidence: float = 0.0


class SectionMapping(BaseModel):
    section_id: str
    section_name: str
    time_bracket: str = ""
    coverage_status: CoverageStatus = CoverageStatus.NOT_COVERED
    mapped_turns: list[MappedTurn] = Field(default_factory=list)
    coverage_notes: str = ""


class OrganisedTranscript(BaseModel):
    session_id: str
    participant_id: str
    section_mappings: list[SectionMapping] = Field(default_factory=list)
    off_script_turns: list[Turn] = Field(default_factory=list)


class Session(BaseModel):
    session_id: str
    project_id: str
    participant_id: str  # e.g. P01, P02
    transcript: list[Turn] = Field(default_factory=list)
    anonymisation_log: AnonymisationLog = Field(default_factory=AnonymisationLog)
    organised: OrganisedTranscript | None = None
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: SessionStatus = SessionStatus.UPLOADED
