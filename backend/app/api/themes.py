from fastapi import APIRouter, HTTPException

from app.db import store
from app.models.theme import SessionThemes, Theme, ThemeStatus

router = APIRouter()


@router.get("", response_model=list[SessionThemes])
async def list_all_themes(project_id: str):
    """Get all themes across all sessions in the project."""
    project = store.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return store.list_all_themes(project_id)


@router.get("/{session_id}", response_model=SessionThemes | None)
async def get_session_themes(project_id: str, session_id: str):
    """Get themes for a specific session."""
    return store.get_themes(session_id)


@router.put("/{session_id}/{theme_id}/status")
async def update_theme_status(
    project_id: str,
    session_id: str,
    theme_id: str,
    status: ThemeStatus,
    researcher_notes: str | None = None,
):
    """Update a theme's status (accept, merge, discard)."""
    themes = store.get_themes(session_id)
    if not themes:
        raise HTTPException(status_code=404, detail="No themes found for session")

    for theme in themes.themes:
        if theme.theme_id == theme_id:
            theme.status = status
            if researcher_notes is not None:
                theme.researcher_notes = researcher_notes
            store.save_themes(session_id, themes)
            return theme

    raise HTTPException(status_code=404, detail="Theme not found")
