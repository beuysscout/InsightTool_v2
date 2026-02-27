"""Supabase-backed project store.

All operations go through the Supabase REST API. Complex nested
objects (transcript turns, sections, themes) are stored as JSONB
and serialised/deserialised via Pydantic.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.db.supabase import get_client
from app.models.guide import ResearchGuide
from app.models.project import Project, ProjectStatus
from app.models.session import Session, SessionStatus
from app.models.theme import SessionThemes


def generate_id() -> str:
    return uuid4().hex[:12]


# ── helpers ──────────────────────────────────────────────────

def _sb():
    return get_client()


# ── Projects ─────────────────────────────────────────────────

def create_project(name: str) -> Project:
    project_id = generate_id()
    row = {
        "project_id": project_id,
        "name": name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": ProjectStatus.SETUP.value,
        "session_count": 0,
        "participant_count": 0,
    }
    _sb().table("projects").insert(row).execute()
    return Project(**row)


def get_project(project_id: str) -> Project | None:
    resp = (
        _sb()
        .table("projects")
        .select("*")
        .eq("project_id", project_id)
        .execute()
    )
    if not resp.data:
        return None
    return Project(**resp.data[0])


def list_projects() -> list[Project]:
    resp = (
        _sb()
        .table("projects")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    return [Project(**r) for r in resp.data]


def delete_project(project_id: str) -> bool:
    resp = (
        _sb()
        .table("projects")
        .delete()
        .eq("project_id", project_id)
        .execute()
    )
    return len(resp.data) > 0


def _update_project_fields(project_id: str, **fields) -> None:
    _sb().table("projects").update(fields).eq("project_id", project_id).execute()


# ── Guides ───────────────────────────────────────────────────

def save_guide(project_id: str, guide: ResearchGuide) -> ResearchGuide:
    row = {
        "project_id": project_id,
        "project_name": guide.project_name,
        "objective": guide.objective,
        "research_goals": guide.research_goals,
        "sections": [s.model_dump() for s in guide.sections],
        "version": guide.version,
        "locked": guide.locked,
    }
    _sb().table("guides").upsert(row).execute()

    # Update project status
    if guide.locked:
        _update_project_fields(project_id, status=ProjectStatus.GUIDE_LOCKED.value)
    else:
        _update_project_fields(project_id, status=ProjectStatus.GUIDE_UPLOADED.value)

    return guide


def get_guide(project_id: str) -> ResearchGuide | None:
    resp = (
        _sb()
        .table("guides")
        .select("*")
        .eq("project_id", project_id)
        .execute()
    )
    if not resp.data:
        return None
    r = resp.data[0]
    return ResearchGuide(
        project_id=r["project_id"],
        project_name=r["project_name"],
        objective=r["objective"],
        research_goals=r["research_goals"],
        sections=r["sections"],
        version=r["version"],
        locked=r["locked"],
    )


# ── Sessions ─────────────────────────────────────────────────

def create_session(project_id: str) -> Session:
    session_id = generate_id()

    # Count existing sessions to generate participant ID
    count_resp = (
        _sb()
        .table("sessions")
        .select("session_id", count="exact")
        .eq("project_id", project_id)
        .execute()
    )
    participant_num = (count_resp.count or 0) + 1
    participant_id = f"P{participant_num:02d}"

    now = datetime.now(timezone.utc)
    row = {
        "session_id": session_id,
        "project_id": project_id,
        "participant_id": participant_id,
        "transcript": [],
        "anonymisation_log": {
            "auto_redacted": 0,
            "researcher_reviewed": 0,
            "exclusions": 0,
            "detections": [],
        },
        "organised": None,
        "upload_timestamp": now.isoformat(),
        "status": SessionStatus.UPLOADED.value,
    }
    _sb().table("sessions").insert(row).execute()

    # Update project counts and status
    _update_project_fields(
        project_id,
        session_count=participant_num,
        participant_count=participant_num,
        status=ProjectStatus.COLLECTING.value,
    )

    return Session(
        session_id=session_id,
        project_id=project_id,
        participant_id=participant_id,
        upload_timestamp=now,
    )


def get_session(session_id: str) -> Session | None:
    resp = (
        _sb()
        .table("sessions")
        .select("*")
        .eq("session_id", session_id)
        .execute()
    )
    if not resp.data:
        return None
    return _row_to_session(resp.data[0])


def list_sessions(project_id: str) -> list[Session]:
    resp = (
        _sb()
        .table("sessions")
        .select("*")
        .eq("project_id", project_id)
        .order("upload_timestamp")
        .execute()
    )
    return [_row_to_session(r) for r in resp.data]


def update_session(session: Session) -> Session:
    row = {
        "transcript": [t.model_dump() for t in session.transcript],
        "anonymisation_log": session.anonymisation_log.model_dump(),
        "organised": session.organised.model_dump() if session.organised else None,
        "status": session.status.value,
    }
    _sb().table("sessions").update(row).eq("session_id", session.session_id).execute()
    return session


def _row_to_session(r: dict) -> Session:
    return Session(
        session_id=r["session_id"],
        project_id=r["project_id"],
        participant_id=r["participant_id"],
        transcript=r["transcript"],
        anonymisation_log=r["anonymisation_log"],
        organised=r["organised"],
        upload_timestamp=r["upload_timestamp"],
        status=r["status"],
    )


# ── Themes ───────────────────────────────────────────────────

def save_themes(session_id: str, themes: SessionThemes) -> SessionThemes:
    row = {
        "session_id": session_id,
        "participant_id": themes.participant_id,
        "themes": [t.model_dump() for t in themes.themes],
    }
    _sb().table("session_themes").upsert(row).execute()

    # Update session status
    _sb().table("sessions").update(
        {"status": SessionStatus.THEMED.value}
    ).eq("session_id", session_id).execute()

    return themes


def get_themes(session_id: str) -> SessionThemes | None:
    resp = (
        _sb()
        .table("session_themes")
        .select("*")
        .eq("session_id", session_id)
        .execute()
    )
    if not resp.data:
        return None
    r = resp.data[0]
    return SessionThemes(
        session_id=r["session_id"],
        participant_id=r["participant_id"],
        themes=r["themes"],
    )


def list_all_themes(project_id: str) -> list[SessionThemes]:
    # Get session IDs for this project, then fetch their themes
    sessions_resp = (
        _sb()
        .table("sessions")
        .select("session_id")
        .eq("project_id", project_id)
        .execute()
    )
    session_ids = [s["session_id"] for s in sessions_resp.data]
    if not session_ids:
        return []

    themes_resp = (
        _sb()
        .table("session_themes")
        .select("*")
        .in_("session_id", session_ids)
        .execute()
    )
    return [
        SessionThemes(
            session_id=r["session_id"],
            participant_id=r["participant_id"],
            themes=r["themes"],
        )
        for r in themes_resp.data
    ]
