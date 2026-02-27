from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ProjectStatus(str, Enum):
    SETUP = "setup"
    GUIDE_UPLOADED = "guide_uploaded"
    GUIDE_LOCKED = "guide_locked"
    COLLECTING = "collecting"
    SYNTHESISING = "synthesising"
    COMPLETE = "complete"


class Project(BaseModel):
    project_id: str
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: ProjectStatus = ProjectStatus.SETUP
    session_count: int = 0
    participant_count: int = 0


class ProjectCreate(BaseModel):
    name: str


class ProjectSummary(BaseModel):
    project_id: str
    name: str
    created_at: datetime
    status: ProjectStatus
    session_count: int
    participant_count: int
