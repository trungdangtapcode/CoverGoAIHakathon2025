"""Example: Manual trigger endpoint for activity reminders."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.tasks.celery_tasks.reminder_tasks import send_activity_reminder_task
from app.users import User, current_active_user

router = APIRouter()


class TriggerReminderRequest(BaseModel):
    """Request to manually trigger a reminder."""
    search_space_id: int
    num_documents: int = 50


@router.post("/reminder/trigger-now")
async def trigger_reminder_now(
    request: TriggerReminderRequest,
    user: User = Depends(current_active_user),
):
    """
    Manually trigger an activity reminder email right now.
    
    This bypasses the scheduled time and sends immediately.
    Useful for testing or on-demand reminders.
    """
    if not user.email:
        raise HTTPException(status_code=400, detail="User has no email address")
    
    # Queue the task
    task = send_activity_reminder_task.delay(
        str(user.id),
        request.search_space_id,
        request.num_documents
    )
    
    return {
        "success": True,
        "message": "Reminder task queued",
        "task_id": task.id,
        "user_email": user.email,
    }


# Add this router to app.py:
# from app.routes.manual_reminder_routes import router as manual_reminder_router
# app.include_router(manual_reminder_router, prefix="/api/v1", tags=["reminders"])
