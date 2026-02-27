from fastapi import APIRouter, HTTPException, UploadFile
from pydantic import BaseModel

from app.agents.theme_extractor import extract_themes
from app.agents.transcript_organiser import organise_transcript
from app.db import store
from app.models.session import (
    AnonymisationLog,
    OrganisedTranscript,
    PiiDetection,
    Session,
    SessionStatus,
)
from app.services.anonymiser import apply_redactions, scan_turns_for_pii
from app.services.parser import parse_markdown_transcript

router = APIRouter()


@router.post("/upload", response_model=Session)
async def upload_transcript(project_id: str, file: UploadFile):
    """Upload a markdown transcript. Parses into turns but does NOT
    run AI yet — PII scan happens first."""
    project = store.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    content = await file.read()
    text = content.decode("utf-8")

    turns = parse_markdown_transcript(text)
    if not turns:
        raise HTTPException(status_code=400, detail="Could not parse any turns from transcript")

    session = store.create_session(project_id)
    session.transcript = turns
    session.status = SessionStatus.UPLOADED
    store.update_session(session)

    return session


@router.get("", response_model=list[Session])
async def list_sessions(project_id: str):
    project = store.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return store.list_sessions(project_id)


@router.get("/{session_id}", response_model=Session)
async def get_session(project_id: str, session_id: str):
    session = store.get_session(session_id)
    if not session or session.project_id != project_id:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


# --- PII Anonymisation ---

@router.post("/{session_id}/scan-pii", response_model=list[PiiDetection])
async def scan_pii(project_id: str, session_id: str):
    """Run PII scan on transcript turns. Returns detections for review."""
    session = store.get_session(session_id)
    if not session or session.project_id != project_id:
        raise HTTPException(status_code=404, detail="Session not found")

    detections = scan_turns_for_pii(session.transcript)

    # Store detections on the session for later
    session.anonymisation_log.detections = detections
    store.update_session(session)

    return detections


class AnonymiseRequest(BaseModel):
    detections: list[PiiDetection]


@router.post("/{session_id}/anonymise", response_model=Session)
async def anonymise_transcript(
    project_id: str, session_id: str, body: AnonymiseRequest
):
    """Apply researcher-reviewed PII redactions. Replaces transcript
    with anonymised version."""
    session = store.get_session(session_id)
    if not session or session.project_id != project_id:
        raise HTTPException(status_code=404, detail="Session not found")

    anonymised_turns, log = apply_redactions(session.transcript, body.detections)
    session.transcript = anonymised_turns
    session.anonymisation_log = log
    session.status = SessionStatus.ANONYMISED
    store.update_session(session)

    return session


# --- Organise ---

@router.post("/{session_id}/organise", response_model=OrganisedTranscript)
async def organise_session_transcript(project_id: str, session_id: str):
    """AI organises the anonymised transcript against guide sections."""
    session = store.get_session(session_id)
    if not session or session.project_id != project_id:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status not in (SessionStatus.ANONYMISED, SessionStatus.ORGANISED):
        raise HTTPException(
            status_code=400,
            detail=f"Session must be anonymised first. Current status: {session.status.value}",
        )

    guide = store.get_guide(project_id)
    if not guide:
        raise HTTPException(status_code=400, detail="No guide found for project")
    if not guide.locked:
        raise HTTPException(status_code=400, detail="Guide must be locked before organising transcripts")

    organised = await organise_transcript(
        turns=session.transcript,
        guide=guide,
        session_id=session.session_id,
        participant_id=session.participant_id,
    )

    session.organised = organised
    session.status = SessionStatus.ORGANISED
    store.update_session(session)

    return organised


# --- Theme extraction ---

@router.post("/{session_id}/extract-themes")
async def extract_session_themes(project_id: str, session_id: str):
    """AI extracts emergent themes from the organised transcript."""
    session = store.get_session(session_id)
    if not session or session.project_id != project_id:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status != SessionStatus.ORGANISED:
        raise HTTPException(
            status_code=400,
            detail=f"Session must be organised first. Current status: {session.status.value}",
        )

    if not session.organised:
        raise HTTPException(status_code=400, detail="No organised transcript found")

    themes = await extract_themes(
        organised=session.organised,
        session_id=session.session_id,
        participant_id=session.participant_id,
    )

    store.save_themes(session.session_id, themes)

    return themes
