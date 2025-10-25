import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from .base import IDModel, TimestampModel


class SearchSpaceBase(BaseModel):
    name: str
    description: str | None = None


class SearchSpaceCreate(SearchSpaceBase):
    pass


class SearchSpaceUpdate(SearchSpaceBase):
    pass


class SearchSpaceRead(SearchSpaceBase, IDModel, TimestampModel):
    id: int
    created_at: datetime
    user_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


# Schema for SearchSpace linking
class SearchSpaceLinkCreate(BaseModel):
    """Schema for linking two SearchSpaces"""
    source_space_id: int
    target_space_id: int


# Schema for SearchSpace data import
class SearchSpaceImportRequest(BaseModel):
    """Schema for importing data from one SearchSpace to another"""
    source_space_id: int
    target_space_id: int
    import_fields: list[str]  # ["messages", "content", "titles", "metadata"]
    import_document_types: list[str] | None = None  # Filter by document types
    limit: int | None = 100  # Limit number of items to import


class SearchSpaceImportResponse(BaseModel):
    """Schema for import operation response"""
    message: str
    imported_documents: int
    imported_messages: int
    imported_items: list[dict]

    model_config = ConfigDict(from_attributes=True)
