"""API routes for Work Mode - Task Management"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Task, User, get_async_session
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


@router.post("/sync-demo", response_model=list[TaskRead])
async def sync_demo_tasks(
    sync_req: TaskSyncRequest,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """
    Generate 10 demo tasks for testing Work Mode.
    
    This creates a realistic set of tasks with different priorities and due dates,
    similar to what you'd get from Linear integration.
    """
    demo_tasks = [
        {
            "title": "🔴 Submit Q4 financial report to board",
            "description": "Compile and finalize Q4 financial statements including revenue, expenses, and profit margins. Must be reviewed by CFO before board meeting tomorrow.",
            "priority": "URGENT",
            "due_offset": -1,
        },
        {
            "title": "🔴 Respond to client complaint about delayed shipment",
            "description": "Major client (Acme Corp) is upset about 2-week delay in their order. Need to provide explanation, compensation offer, and updated delivery timeline today.",
            "priority": "URGENT",
            "due_offset": 0,
        },
        {
            "title": "🟠 Prepare presentation for Monday's team meeting",
            "description": "Create slides covering project status updates, upcoming milestones, and resource allocation for Q1. Include charts and team feedback summary.",
            "priority": "HIGH",
            "due_offset": 1,
        },
        {
            "title": "🟠 Review and approve vacation requests",
            "description": "Process 8 pending vacation requests from team members. Check coverage plans and approve/deny based on project deadlines and team availability.",
            "priority": "HIGH",
            "due_offset": 2,
        },
        {
            "title": "🟠 Update employee handbook with new policies",
            "description": "Incorporate new remote work policy, updated PTO guidelines, and revised expense reimbursement procedures. Get legal approval before distribution.",
            "priority": "HIGH",
            "due_offset": 3,
        },
        {
            "title": "🟡 Schedule interviews for Marketing Manager position",
            "description": "Coordinate with 5 candidates and 3 interviewers to set up interview slots. Send calendar invites and prepare interview questions packet.",
            "priority": "MEDIUM",
            "due_offset": 5,
        },
        {
            "title": "🟡 Organize team building event for next month",
            "description": "Research venue options, get quotes from caterers, and create poll for team preferences. Budget: $2000 for 20 people. Consider dietary restrictions.",
            "priority": "MEDIUM",
            "due_offset": 7,
        },
        {
            "title": "🟡 Update customer contact database",
            "description": "Clean up duplicate entries, verify email addresses, and update company information for top 50 clients. Export updated list for sales team.",
            "priority": "MEDIUM",
            "due_offset": 10,
        },
        {
            "title": "🟢 Research new project management software options",
            "description": "Compare 3-4 tools (pricing, features, integrations). Create comparison spreadsheet and schedule demos with vendors for team evaluation.",
            "priority": "LOW",
            "due_offset": 14,
        },
        {
            "title": "🟢 Archive old project files to cloud storage",
            "description": "Move completed project files from 2022-2023 to archive folder. Organize by year and project name. Update file index spreadsheet.",
            "priority": "LOW",
            "due_offset": 21,
        },
    ]
    
    try:
        created_tasks = []
        
        for i, task_data in enumerate(demo_tasks, 1):
            due_date = datetime.utcnow() + timedelta(days=task_data["due_offset"])
            
            task = Task(
                search_space_id=sync_req.search_space_id,
                user_id=str(user.id),
                title=task_data["title"],
                description=task_data["description"],
                source_type="LINEAR",
                external_id=f"DEMO-{i:03d}",
                external_url=f"https://linear.app/surfsense/issue/DEMO-{i:03d}",
                external_metadata={
                    "issue_number": i,
                    "labels": ["demo", "work-mode"],
                },
                status="UNDONE",
                priority=task_data["priority"],
                due_date=due_date,
            )
            
            session.add(task)
            created_tasks.append(task)
        
        await session.commit()
        
        # Refresh all tasks to get their IDs
        for task in created_tasks:
            await session.refresh(task)
        
        return [TaskRead.model_validate(task) for task in created_tasks]
        
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create demo tasks: {str(e)}")


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
