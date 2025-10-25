"""Pydantic schemas for Notes (chat to notes evolution)"""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from .base import IDModel, TimestampModel


class NoteBase(BaseModel):
    """Base schema for notes"""
    title: str
    content: str


class NoteCreate(NoteBase):
    """Schema for creating a note"""
    search_space_id: int
    source_chat_id: Optional[int] = None  # If converted from a chat


class NoteUpdate(BaseModel):
    """Schema for updating a note"""
    title: Optional[str] = None
    content: Optional[str] = None


class NoteRead(NoteBase, IDModel, TimestampModel):
    """Schema for reading a note"""
    id: int
    search_space_id: int
    user_id: uuid.UUID
    source_chat_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class NoteSearchRequest(BaseModel):
    """Request to search notes"""
    search_space_id: int
    query: str  # Full-text search query
    limit: int = 20


class ChatToNoteRequest(BaseModel):
    """Request to convert a chat to a note"""
    chat_id: int
    search_space_id: int
    title: Optional[str] = None  # If not provided, will be auto-generated from chat
