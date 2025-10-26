"""API routes for Notes - Chat to Notes Evolution"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import User, get_async_session
from app.schemas.note import ChatToNoteRequest, NoteCreate, NoteRead, NoteSearchRequest, NoteUpdate
from app.services.note_service import NoteService
from app.users import current_active_user

router = APIRouter(prefix="/notes", tags=["Notes"])


@router.post("/from-chat", response_model=NoteRead)
async def create_note_from_chat(
    request: ChatToNoteRequest,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """
    Convert a chat conversation to a structured note.

    This endpoint:
    1. Takes a chat ID
    2. Extracts the conversation content
    3. (Future: Uses LLM to summarize and structure)
    4. Creates a searchable note

    Example:
    ```json
    {
        "chat_id": 123,
        "search_space_id": 1,
        "title": "Meeting Notes" // optional
    }
    ```
    """
    service = NoteService(session)
    try:
        note = await service.create_note_from_chat(request, user_id=str(user.id))
        return note
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create note from chat: {str(e)}")


@router.post("/create", response_model=NoteRead)
async def create_note(
    note_data: NoteCreate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """
    Create a note manually (not from chat).

    Use this for creating notes from scratch.
    """
    service = NoteService(session)
    try:
        note = await service.create_manual_note(note_data, user_id=str(user.id))
        return note
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create note: {str(e)}")


@router.post("/search", response_model=list[NoteRead])
async def search_notes(
    search_req: NoteSearchRequest,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """
    Search notes using full-text search.

    This uses PostgreSQL's GIN index for fast search across title and content.

    Example:
    ```json
    {
        "search_space_id": 1,
        "query": "meeting notes",
        "limit": 20
    }
    ```
    """
    service = NoteService(session)
    try:
        notes = await service.search_notes(search_req, user_id=str(user.id))
        return notes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search notes: {str(e)}")


@router.post("/{search_space_id}", response_model=list[NoteRead])
async def get_all_notes(
    search_space_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """Get all notes for a search space, sorted by most recently updated"""
    service = NoteService(session)
    try:
        notes = await service.get_all_notes(search_space_id, user_id=str(user.id))
        return notes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get notes: {str(e)}")


@router.put("/{note_id}", response_model=NoteRead)
async def update_note(
    note_id: int,
    update_data: NoteUpdate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """Update an existing note's title or content"""
    service = NoteService(session)
    try:
        note = await service.update_note(note_id, update_data, user_id=str(user.id))
        return note
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Note not found: {str(e)}")


@router.delete("/{note_id}")
async def delete_note(
    note_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """Delete a note"""
    service = NoteService(session)
    try:
        await service.delete_note(note_id, user_id=str(user.id))
        return {"message": "Note deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Note not found: {str(e)}")
