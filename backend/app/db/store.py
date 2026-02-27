"""In-memory project store.

Provides a simple dict-based store for development. Will be replaced
with Supabase persistence once credentials are configured.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.models.guide import ResearchGuide
from app.models.project import Project, ProjectStatus
from app.models.session import Session, SessionStatus
from app.models.theme import SessionThemes

# In-memory storage
_projects: dict[str, Project] = {}
_guides: dict[str, ResearchGuide] = {}  # keyed by project_id
_sessions: dict[str, Session] = {}  # keyed by session_id
_themes: dict[str, SessionThemes] = {}  # keyed by session_id


def generate_id() -> str:
    return uuid4().hex[:12]


# --- Projects ---

def create_project(name: str) -> Project:
    project_id = generate_id()
    project = Project(
        project_id=project_id,
        name=name,
        created_at=datetime.now(timezone.utc),
    )
    _projects[project_id] = project
    return project


def get_project(project_id: str) -> Project | None:
    return _projects.get(project_id)


def list_projects() -> list[Project]:
    return list(_projects.values())


def delete_project(project_id: str) -> bool:
    if project_id not in _projects:
        return False
    del _projects[project_id]
    _guides.pop(project_id, None)
    # Remove sessions belonging to this project
    session_ids = [
        sid for sid, s in _sessions.items() if s.project_id == project_id
    ]
    for sid in session_ids:
        _sessions.pop(sid, None)
        _themes.pop(sid, None)
    return True


# --- Guides ---

def save_guide(project_id: str, guide: ResearchGuide) -> ResearchGuide:
    _guides[project_id] = guide
    project = _projects.get(project_id)
    if project:
        if guide.locked:
            project.status = ProjectStatus.GUIDE_LOCKED
        else:
            project.status = ProjectStatus.GUIDE_UPLOADED
    return guide


def get_guide(project_id: str) -> ResearchGuide | None:
    return _guides.get(project_id)


# --- Sessions ---

def create_session(project_id: str) -> Session:
    session_id = generate_id()
    project = _projects.get(project_id)
    # Calculate participant ID
    existing = [s for s in _sessions.values() if s.project_id == project_id]
    participant_num = len(existing) + 1
    participant_id = f"P{participant_num:02d}"

    session = Session(
        session_id=session_id,
        project_id=project_id,
        participant_id=participant_id,
    )
    _sessions[session_id] = session

    if project:
        project.session_count = len(existing) + 1
        project.participant_count = project.session_count
        if project.status == ProjectStatus.GUIDE_LOCKED:
            project.status = ProjectStatus.COLLECTING

    return session


def get_session(session_id: str) -> Session | None:
    return _sessions.get(session_id)


def list_sessions(project_id: str) -> list[Session]:
    return [s for s in _sessions.values() if s.project_id == project_id]


def update_session(session: Session) -> Session:
    _sessions[session.session_id] = session
    return session


# --- Themes ---

def save_themes(session_id: str, themes: SessionThemes) -> SessionThemes:
    _themes[session_id] = themes
    session = _sessions.get(session_id)
    if session:
        session.status = SessionStatus.THEMED
    return themes


def get_themes(session_id: str) -> SessionThemes | None:
    return _themes.get(session_id)


def list_all_themes(project_id: str) -> list[SessionThemes]:
    project_sessions = list_sessions(project_id)
    session_ids = {s.session_id for s in project_sessions}
    return [t for sid, t in _themes.items() if sid in session_ids]
