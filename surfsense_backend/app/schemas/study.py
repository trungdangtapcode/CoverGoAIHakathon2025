"""Pydantic schemas for Study Mode (flashcards and MCQs)"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from .base import IDModel, TimestampModel


class StudyMaterialBase(BaseModel):
    """Base schema for study materials"""
    material_type: str  # 'FLASHCARD' or 'MCQ'
    question: str
    answer: Optional[str] = None
    options: Optional[dict] = None  # For MCQs: {"A": "option1", "B": "option2", ...}


class StudyMaterialCreate(StudyMaterialBase):
    """Schema for creating a study material"""
    search_space_id: int
    document_id: Optional[int] = None


class StudyMaterialUpdate(BaseModel):
    """Schema for updating study material performance"""
    times_attempted: Optional[int] = None
    times_correct: Optional[int] = None
    last_attempted_at: Optional[datetime] = None


class StudyMaterialRead(StudyMaterialBase, IDModel, TimestampModel):
    """Schema for reading study material"""
    id: int
    search_space_id: int
    document_id: Optional[int] = None
    times_attempted: int
    times_correct: int
    last_attempted_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StudyMaterialAttempt(BaseModel):
    """Schema for recording a study attempt"""
    material_id: int
    is_correct: bool


class GenerateStudyMaterialsRequest(BaseModel):
    """Request to generate study materials from documents"""
    document_ids: list[int]
    material_type: str  # 'FLASHCARD' or 'MCQ'
    count: int = 10  # Number of materials to generate
