"""Email schemas for API requests and responses."""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class EmailSendRequest(BaseModel):
    """Schema for sending an email to a user."""

    to_email: EmailStr = Field(..., description="Recipient email address")
    subject: str = Field(..., min_length=1, max_length=200, description="Email subject")
    content: str = Field(..., min_length=1, description="Email content")
    is_html: bool = Field(default=False, description="Whether content is HTML")
    reply_to: Optional[EmailStr] = Field(
        None, description="Optional reply-to email address"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "to_email": "user@example.com",
                "subject": "Welcome to SurfSense!",
                "content": "Hello! Welcome to our platform.",
                "is_html": False,
                "reply_to": None,
            }
        }


class BulkEmailSendRequest(BaseModel):
    """Schema for sending bulk emails."""

    to_emails: list[EmailStr] = Field(
        ..., min_length=1, description="List of recipient email addresses"
    )
    subject: str = Field(..., min_length=1, max_length=200, description="Email subject")
    content: str = Field(..., min_length=1, description="Email content")
    is_html: bool = Field(default=False, description="Whether content is HTML")

    class Config:
        json_schema_extra = {
            "example": {
                "to_emails": ["user1@example.com", "user2@example.com"],
                "subject": "Newsletter",
                "content": "Check out our latest updates!",
                "is_html": False,
            }
        }


class EmailResponse(BaseModel):
    """Schema for email send response."""

    success: bool = Field(..., description="Whether the email was sent successfully")
    message: str = Field(..., description="Result message")

    class Config:
        json_schema_extra = {
            "example": {"success": True, "message": "Email sent successfully"}
        }


class BulkEmailResponse(BaseModel):
    """Schema for bulk email send response."""

    success_count: int = Field(..., description="Number of successfully sent emails")
    failure_count: int = Field(..., description="Number of failed emails")
    failed_emails: list[str] = Field(
        default=[], description="List of email addresses that failed"
    )
    message: str = Field(..., description="Result message")

    class Config:
        json_schema_extra = {
            "example": {
                "success_count": 2,
                "failure_count": 0,
                "failed_emails": [],
                "message": "All emails sent successfully",
            }
        }


class SendToUserRequest(BaseModel):
    """Schema for sending email to an existing user by ID."""

    subject: str = Field(..., min_length=1, max_length=200, description="Email subject")
    content: str = Field(..., min_length=1, description="Email content")
    is_html: bool = Field(default=False, description="Whether content is HTML")
    reply_to: Optional[EmailStr] = Field(
        None, description="Optional reply-to email address"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "subject": "Important Update",
                "content": "Hello! Here's an important update for you.",
                "is_html": False,
            }
        }
