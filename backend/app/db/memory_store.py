"""In-memory project store for local development without Supabase.

Mirrors the same interface as the Supabase store so callers don't
need to know which backend is active.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.models.guide import ResearchGuide
from app.models.project import Project, ProjectStatus
from app.models.session import Session, SessionStatus
from app.models.theme import SessionThemes

# ── In-memory tables ─────────────────────────────────────────

_projects: dict[str, dict] = {}
_guides: dict[str, ResearchGuide] = {}
_sessions: dict[str, dict] = {}
_themes: dict[str, SessionThemes] = {}


def generate_id() -> str:
    return uuid4().hex[:12]


# ── Projects ─────────────────────────────────────────────────

def create_project(name: str) -> Project:
    project_id = generate_id()
    project = Project(
        project_id=project_id,
        name=name,
        created_at=datetime.now(timezone.utc),
        status=ProjectStatus.SETUP,
        session_count=0,
        participant_count=0,
    )
    _projects[project_id] = project.model_dump()
    return project


def get_project(project_id: str) -> Project | None:
    row = _projects.get(project_id)
    if not row:
        return None
    return Project(**row)


def list_projects() -> list[Project]:
    return sorted(
        [Project(**r) for r in _projects.values()],
        key=lambda p: p.created_at,
        reverse=True,
    )


def delete_project(project_id: str) -> bool:
    if project_id not in _projects:
        return False
    del _projects[project_id]
    _guides.pop(project_id, None)
    # Remove sessions and their themes
    session_ids = [
        sid for sid, s in _sessions.items() if s["project_id"] == project_id
    ]
    for sid in session_ids:
        del _sessions[sid]
        _themes.pop(sid, None)
    return True


def _update_project_fields(project_id: str, **fields) -> None:
    if project_id in _projects:
        _projects[project_id].update(fields)


# ── Guides ───────────────────────────────────────────────────

def save_guide(project_id: str, guide: ResearchGuide) -> ResearchGuide:
    _guides[project_id] = guide
    if guide.locked:
        _update_project_fields(project_id, status=ProjectStatus.GUIDE_LOCKED.value)
    else:
        _update_project_fields(project_id, status=ProjectStatus.GUIDE_UPLOADED.value)
    return guide


def get_guide(project_id: str) -> ResearchGuide | None:
    return _guides.get(project_id)


# ── Sessions ─────────────────────────────────────────────────

def create_session(project_id: str) -> Session:
    session_id = generate_id()
    participant_num = sum(
        1 for s in _sessions.values() if s["project_id"] == project_id
    ) + 1
    participant_id = f"P{participant_num:02d}"
    now = datetime.now(timezone.utc)

    session = Session(
        session_id=session_id,
        project_id=project_id,
        participant_id=participant_id,
        upload_timestamp=now,
    )
    _sessions[session_id] = session.model_dump()

    _update_project_fields(
        project_id,
        session_count=participant_num,
        participant_count=participant_num,
        status=ProjectStatus.COLLECTING.value,
    )
    return session


def get_session(session_id: str) -> Session | None:
    row = _sessions.get(session_id)
    if not row:
        return None
    return Session(**row)


def list_sessions(project_id: str) -> list[Session]:
    return [
        Session(**r)
        for r in sorted(
            (s for s in _sessions.values() if s["project_id"] == project_id),
            key=lambda s: s["upload_timestamp"],
        )
    ]


def update_session(session: Session) -> Session:
    _sessions[session.session_id] = session.model_dump()
    return session


# ── Themes ───────────────────────────────────────────────────

def save_themes(session_id: str, themes: SessionThemes) -> SessionThemes:
    _themes[session_id] = themes
    if session_id in _sessions:
        _sessions[session_id]["status"] = SessionStatus.THEMED.value
    return themes


def get_themes(session_id: str) -> SessionThemes | None:
    return _themes.get(session_id)


def list_all_themes(project_id: str) -> list[SessionThemes]:
    session_ids = {
        sid for sid, s in _sessions.items() if s["project_id"] == project_id
    }
    return [t for sid, t in _themes.items() if sid in session_ids]
