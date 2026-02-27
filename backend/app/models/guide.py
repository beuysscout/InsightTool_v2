from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class AiFlagType(str, Enum):
    LEADING = "leading"
    AMBIGUOUS = "ambiguous"
    OUT_OF_SCOPE = "out_of_scope"
    MISSING_COVERAGE = "missing_coverage"


class AiFlag(BaseModel):
    flag_type: AiFlagType
    message: str
    suggestion: str | None = None
    status: str = "pending"  # pending | accepted | dismissed


class Question(BaseModel):
    question_id: str
    question_text: str
    mapped_goal: str | None = None
    required: bool = True
    probes: list[str] = Field(default_factory=list)
    ai_flags: list[AiFlag] = Field(default_factory=list)


class GuideSection(BaseModel):
    section_id: str
    section_name: str
    time_bracket: str = ""  # e.g. "0:00-10:00"
    questions: list[Question] = Field(default_factory=list)


class ResearchGuide(BaseModel):
    project_id: str
    project_name: str
    objective: str = ""
    research_goals: list[str] = Field(default_factory=list)
    sections: list[GuideSection] = Field(default_factory=list)
    version: int = 1
    locked: bool = False


class GuideReviewResult(BaseModel):
    """Output from the Guide Reviewer agent."""

    parsed_guide: ResearchGuide
    flags: list[AiFlag] = Field(default_factory=list)
    suggested_probes: list[dict] = Field(default_factory=list)
    coverage_gaps: list[str] = Field(default_factory=list)
    estimated_duration_minutes: int | None = None
