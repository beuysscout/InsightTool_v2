from fastapi import APIRouter, HTTPException, UploadFile
from pydantic import BaseModel

from app.agents.guide_reviewer import review_guide
from app.db import store
from app.models.guide import GuideReviewResult, ResearchGuide

router = APIRouter()


class GuideUploadMeta(BaseModel):
    objective: str = ""
    research_goals: list[str] = []


@router.post("/upload", response_model=GuideReviewResult)
async def upload_and_review_guide(
    project_id: str,
    file: UploadFile,
    objective: str = "",
    research_goals: str = "",
):
    """Upload a research guide file and get AI review."""
    project = store.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    content = await file.read()
    guide_text = content.decode("utf-8")

    goals = [g.strip() for g in research_goals.split(",") if g.strip()] if research_goals else []

    result = await review_guide(
        guide_text=guide_text,
        project_name=project.name,
        objective=objective,
        research_goals=goals,
    )

    # Attach project_id to the parsed guide
    result.parsed_guide.project_id = project_id

    # Save the parsed guide (unlocked — researcher reviews first)
    store.save_guide(project_id, result.parsed_guide)

    return result


@router.get("", response_model=ResearchGuide | None)
async def get_guide(project_id: str):
    project = store.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return store.get_guide(project_id)


@router.put("", response_model=ResearchGuide)
async def update_guide(project_id: str, guide: ResearchGuide):
    """Update the guide (e.g. after researcher edits)."""
    project = store.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    guide.project_id = project_id
    return store.save_guide(project_id, guide)


@router.post("/lock", response_model=ResearchGuide)
async def lock_guide(project_id: str):
    """Lock the guide — no further edits. Becomes the analysis framework."""
    guide = store.get_guide(project_id)
    if not guide:
        raise HTTPException(status_code=404, detail="Guide not found")
    guide.locked = True
    return store.save_guide(project_id, guide)
