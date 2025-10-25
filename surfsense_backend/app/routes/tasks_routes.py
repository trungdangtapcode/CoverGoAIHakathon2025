"""API routes for Work Mode - Task Management"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import User, get_async_session
from app.schemas.task import (
    TaskCompleteRequest,
    TaskCreate,
    TaskFilterRequest,
    TaskRead,
    TaskSyncRequest,
)
from app.services.task_service import TaskService
from app.users import current_active_user

router = APIRouter(prefix="/tasks", tags=["Work Mode - Tasks"])


@router.post("/sync", response_model=list[TaskRead])
async def sync_tasks(
    sync_req: TaskSyncRequest,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """
    Sync tasks from workspace connectors (Linear, Jira, Slack, etc.)

    This endpoint:
    1. Queries documents indexed from connectors
    2. Extracts task information from metadata
    3. Creates/updates tasks in the database
    4. Returns all synced tasks
    """
    service = TaskService(session)
    try:
        tasks = await service.sync_tasks_from_connectors(
            search_space_id=sync_req.search_space_id,
            user_id=str(user.id),
            connector_types=sync_req.connector_types,
        )
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync tasks: {str(e)}")


@router.post("/filter", response_model=list[TaskRead])
async def get_tasks(
    filter_req: TaskFilterRequest,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """
    Get tasks with filtering and sorting.

    Default behavior:
    - Returns UNDONE tasks
    - Sorted by priority (URGENT > HIGH > MEDIUM > LOW) → due_date (earliest first) → created_at (oldest first)

    This is the main endpoint for answering "what tasks are undone this week?"
    """
    service = TaskService(session)
    try:
        tasks = await service.get_tasks_filtered(filter_req=filter_req, user_id=str(user.id))
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tasks: {str(e)}")


@router.post("/complete", response_model=TaskRead)
async def complete_task(
    complete_req: TaskCompleteRequest,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """
    Mark a task as complete and auto-link related chats/documents.

    Auto-linking logic:
    - Finds chats and documents from the last 2 hours
    - Links them to the task for future reference
    - (Future: Use semantic similarity > 0.7)
    """
    service = TaskService(session)
    try:
        task = await service.complete_task(task_id=complete_req.task_id, user_id=str(user.id))
        return task
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete task: {str(e)}")


@router.post("/create", response_model=TaskRead)
async def create_task(
    task_data: TaskCreate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """
    Create a manual task (not from connectors).

    Use this for tasks that don't come from Linear/Jira/etc.
    """
    service = TaskService(session)
    try:
        task = await service.create_manual_task(task_data=task_data, user_id=str(user.id))
        return task
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(
    task_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """Get a single task by ID"""
    from sqlalchemy import and_, select
    from app.db import Task

    stmt = select(Task).where(and_(Task.id == task_id, Task.user_id == user.id))
    result = await session.execute(stmt)
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskRead.model_validate(task)
