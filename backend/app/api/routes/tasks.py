from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import TaskRun
from app.schemas import TaskRunRead

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskRunRead])
def list_tasks(
    db: Session = Depends(get_db),
    status: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[TaskRun]:
    stmt = select(TaskRun).order_by(TaskRun.created_at.desc()).limit(limit)
    if status:
        stmt = stmt.where(TaskRun.status == status)
    return list(db.scalars(stmt).all())


@router.get("/{task_run_id}", response_model=TaskRunRead)
def get_task(task_run_id: int, db: Session = Depends(get_db)) -> TaskRun:
    task = db.get(TaskRun, task_run_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
