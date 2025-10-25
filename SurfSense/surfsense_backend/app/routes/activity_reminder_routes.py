"""Routes for activity reminder emails - casual reminders about what's happening."""

import logging
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SearchSpace, get_async_session
from app.utils.check_ownership import check_ownership
from app.services.activity_reminder_service import ActivityReminderService
from app.users import User, current_active_user

router = APIRouter()
logger = logging.getLogger(__name__)


# Request schemas
class SendReminderRequest(BaseModel):
    """Request to send a casual activity reminder email."""

    search_space_id: int = Field(..., description="Search space to check activity from")
    num_documents: int = Field(
        default=50, ge=10, le=200, description="How many recent docs to look at"
    )
    include_connectors: bool = Field(
        default=True, description="Include stuff from connected apps (Slack, Gmail, etc.)"
    )
    include_files: bool = Field(
        default=False, description="Include user uploaded files"
    )
    recipient_email: EmailStr | None = Field(
        None, description="Send to different email (defaults to your email)"
    )


class PreviewEmailRequest(BaseModel):
    """Request to preview what the email would look like."""

    search_space_id: int = Field(..., description="Search space to check")
    num_documents: int = Field(
        default=50, ge=10, le=200, description="How many docs to analyze"
    )
    include_connectors: bool = Field(default=True, description="Include connectors")
    include_files: bool = Field(default=False, description="Include files")
    format: Literal["html", "text"] = Field(
        default="html", description="Preview as HTML or plain text"
    )


# Response schemas
class SendReminderResponse(BaseModel):
    """Response after sending reminder."""

    success: bool
    message: str
    email_sent_to: str
    insights: dict | None = None


class PreviewEmailResponse(BaseModel):
    """Preview of email content."""

    format: str
    subject: str
    content: str
    insights_summary: dict


@router.post("/reminder/send", response_model=SendReminderResponse)
async def send_activity_reminder(
    request: SendReminderRequest,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Send a casual reminder email about recent activity.
    
    This email focuses on **what's been happening** in your connected apps.
    Planning suggestions are included as an optional bonus if available.
    
    Perfect for:
    - Daily morning catch-up emails
    - Weekly activity summaries  
    - End of day reminders
    
    The email is casual and easy to scan - just what happened and maybe some ideas
    for what to do next.
    """
    try:
        # Check user owns this search space
        await check_ownership(session, SearchSpace, request.search_space_id, user)

        # Determine recipient
        recipient_email = request.recipient_email or user.email
        if not recipient_email:
            raise HTTPException(
                status_code=400, detail="No email found. Provide recipient_email."
            )

        # Create service and send
        service = ActivityReminderService(session, str(user.id), recipient_email)

        success, message, insights = await service.generate_and_send_reminder(
            search_space_id=request.search_space_id,
            num_documents=request.num_documents,
            include_connectors=request.include_connectors,
            include_files=request.include_files,
        )

        if not success:
            raise HTTPException(status_code=500, detail=message)

        return SendReminderResponse(
            success=True,
            message="Activity reminder sent!",
            email_sent_to=recipient_email,
            insights=insights.model_dump() if insights else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending reminder: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reminder/preview", response_model=PreviewEmailResponse)
async def preview_activity_reminder(
    request: PreviewEmailRequest,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Preview what the reminder email will look like without actually sending it.
    
    Use this to:
    - See what content will be generated
    - Check the email formatting
    - Test before setting up automated reminders
    
    Returns the full email content (HTML or text) plus a summary of what was analyzed.
    """
    try:
        # Check ownership
        await check_ownership(session, SearchSpace, request.search_space_id, user)

        # Get user email
        if not user.email:
            raise HTTPException(status_code=400, detail="User email not found")

        # Create service
        service = ActivityReminderService(session, str(user.id), user.email)

        # Generate preview
        preview = await service.preview_email(
            search_space_id=request.search_space_id,
            num_documents=request.num_documents,
            include_connectors=request.include_connectors,
            include_files=request.include_files,
            format=request.format,
        )

        return PreviewEmailResponse(
            format=preview["format"],
            subject=preview["subject"],
            content=preview["content"],
            insights_summary=preview["summary"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating preview: {e}")
        raise HTTPException(status_code=500, detail=str(e))
