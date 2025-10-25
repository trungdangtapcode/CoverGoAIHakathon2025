"""Email routes for sending emails to users."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import User, get_async_session
from app.schemas.email import (
    BulkEmailResponse,
    BulkEmailSendRequest,
    EmailResponse,
    EmailSendRequest,
    SendToUserRequest,
)
from app.services.email_service import get_email_service
from app.users import current_active_user

router = APIRouter()


@router.post("/email/send", response_model=EmailResponse)
async def send_email(
    email_request: EmailSendRequest,
    email_service=Depends(get_email_service),
    current_user: User = Depends(current_active_user),
):
    """
    Send an email to a specific email address.

    Requires authentication. Only authenticated users can send emails.

    Args:
        email_request: Email details (to, subject, content, etc.)
        email_service: Email service dependency
        current_user: Current authenticated user

    Returns:
        EmailResponse with success status and message
    """
    if email_request.is_html:
        success, message = email_service.send_html_email(
            to_email=email_request.to_email,
            subject=email_request.subject,
            html_content=email_request.content,
            reply_to=email_request.reply_to,
        )
    else:
        success, message = email_service.send_text_email(
            to_email=email_request.to_email,
            subject=email_request.subject,
            content=email_request.content,
            reply_to=email_request.reply_to,
        )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message
        )

    return EmailResponse(success=success, message=message)


@router.post("/email/send-to-user/{user_id}", response_model=EmailResponse)
async def send_email_to_user(
    user_id: uuid.UUID,
    email_request: SendToUserRequest,
    session: AsyncSession = Depends(get_async_session),
    email_service=Depends(get_email_service),
    current_user: User = Depends(current_active_user),
):
    """
    Send an email to a specific user by their user ID.

    Requires authentication. Looks up the user's email from the database.

    Args:
        user_id: UUID of the target user
        email_request: Email details (subject, content, etc.)
        session: Database session
        email_service: Email service dependency
        current_user: Current authenticated user

    Returns:
        EmailResponse with success status and message
    """
    # Get user from database
    from sqlalchemy import select

    result = await session.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if not target_user.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have an email address",
        )

    # Send email
    if email_request.is_html:
        success, message = email_service.send_html_email(
            to_email=target_user.email,
            subject=email_request.subject,
            html_content=email_request.content,
            reply_to=email_request.reply_to,
        )
    else:
        success, message = email_service.send_text_email(
            to_email=target_user.email,
            subject=email_request.subject,
            content=email_request.content,
            reply_to=email_request.reply_to,
        )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message
        )

    return EmailResponse(success=success, message=message)


@router.post("/email/send-bulk", response_model=BulkEmailResponse)
async def send_bulk_emails(
    email_request: BulkEmailSendRequest,
    email_service=Depends(get_email_service),
    current_user: User = Depends(current_active_user),
):
    """
    Send emails to multiple recipients at once.

    Requires authentication. Useful for newsletters or announcements.

    Args:
        email_request: Bulk email details (recipients, subject, content)
        email_service: Email service dependency
        current_user: Current authenticated user

    Returns:
        BulkEmailResponse with counts of successful/failed sends
    """
    success_count, failure_count, failed_emails = email_service.send_bulk_emails(
        recipients=email_request.to_emails,
        subject=email_request.subject,
        content=email_request.content,
        is_html=email_request.is_html,
    )

    if success_count == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send any emails",
        )

    message = (
        f"Successfully sent {success_count} emails"
        if failure_count == 0
        else f"Sent {success_count} emails, {failure_count} failed"
    )

    return BulkEmailResponse(
        success_count=success_count,
        failure_count=failure_count,
        failed_emails=failed_emails,
        message=message,
    )


@router.post("/email/send-to-all-users", response_model=BulkEmailResponse)
async def send_email_to_all_users(
    email_request: SendToUserRequest,
    session: AsyncSession = Depends(get_async_session),
    email_service=Depends(get_email_service),
    current_user: User = Depends(current_active_user),
):
    """
    Send an email to all registered users.

    Requires authentication. Be careful with this endpoint!

    Args:
        email_request: Email details (subject, content, etc.)
        session: Database session
        email_service: Email service dependency
        current_user: Current authenticated user

    Returns:
        BulkEmailResponse with counts of successful/failed sends
    """
    # Get all users with email addresses
    from sqlalchemy import select

    result = await session.execute(select(User).where(User.email.isnot(None)))
    users = result.scalars().all()

    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No users found with emails"
        )

    # Extract email addresses
    recipient_emails = [user.email for user in users if user.email]

    if not recipient_emails:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No valid email addresses found"
        )

    # Send bulk emails
    success_count, failure_count, failed_emails = email_service.send_bulk_emails(
        recipients=recipient_emails,
        subject=email_request.subject,
        content=email_request.content,
        is_html=email_request.is_html,
    )

    message = (
        f"Successfully sent emails to all {success_count} users"
        if failure_count == 0
        else f"Sent to {success_count} users, {failure_count} failed"
    )

    return BulkEmailResponse(
        success_count=success_count,
        failure_count=failure_count,
        failed_emails=failed_emails,
        message=message,
    )
