from fastapi import APIRouter, HTTPException

from app.db import store
from app.models.project import Project, ProjectCreate, ProjectSummary

router = APIRouter()


@router.post("", response_model=Project)
async def create_project(body: ProjectCreate):
    return store.create_project(body.name)


@router.get("", response_model=list[ProjectSummary])
async def list_projects():
    projects = store.list_projects()
    return [
        ProjectSummary(
            project_id=p.project_id,
            name=p.name,
            created_at=p.created_at,
            status=p.status,
            session_count=p.session_count,
            participant_count=p.participant_count,
        )
        for p in projects
    ]


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: str):
    project = store.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    if not store.delete_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    return {"deleted": True}
