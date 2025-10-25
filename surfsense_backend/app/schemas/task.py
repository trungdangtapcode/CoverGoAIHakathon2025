"""Pydantic schemas for Work Mode (task management)"""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from .base import IDModel, TimestampModel


class TaskBase(BaseModel):
    """Base schema for tasks"""
    title: str
    description: Optional[str] = None
    priority: Optional[str] = None  # 'LOW', 'MEDIUM', 'HIGH', 'URGENT'
    due_date: Optional[datetime] = None


class TaskCreate(TaskBase):
    """Schema for creating a task manually"""
    search_space_id: int


class TaskUpdate(BaseModel):
    """Schema for updating a task"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None  # 'UNDONE', 'DONE'
    priority: Optional[str] = None
    due_date: Optional[datetime] = None


class TaskRead(TaskBase, IDModel, TimestampModel):
    """Schema for reading a task"""
    id: int
    search_space_id: int
    user_id: uuid.UUID

    # Source tracking
    source_type: Optional[str] = None  # 'LINEAR', 'JIRA', 'SLACK', 'MANUAL'
    external_id: Optional[str] = None
    external_url: Optional[str] = None
    external_metadata: Optional[dict] = None

    # Status
    status: str  # 'UNDONE', 'DONE'

    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Linked resources
    linked_chat_ids: list[int] = []
    linked_document_ids: list[int] = []

    model_config = ConfigDict(from_attributes=True)


class TaskCompleteRequest(BaseModel):
    """Request to mark a task as complete"""
    task_id: int
    # Auto-linking will find recent chats/docs within 2 hours with similarity > 0.7


class TaskSyncRequest(BaseModel):
    """Request to sync tasks from connectors"""
    search_space_id: int
    connector_types: list[str]  # ['LINEAR', 'JIRA', 'SLACK']


class TaskFilterRequest(BaseModel):
    """Request to filter tasks"""
    search_space_id: int
    status: Optional[str] = 'UNDONE'  # 'UNDONE', 'DONE', or None for all
    sort_by_priority: bool = True  # Sort by priority → due_date → created_at
