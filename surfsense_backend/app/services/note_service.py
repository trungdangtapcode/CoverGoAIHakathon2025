"""Service for Notes - Chat to Notes Evolution"""
from sqlalchemy import and_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Chat, Note
from app.schemas.note import ChatToNoteRequest, NoteCreate, NoteRead, NoteSearchRequest, NoteUpdate


class NoteService:
    """Service for managing notes and converting chats to notes"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_note_from_chat(
        self, request: ChatToNoteRequest, user_id: str, llm_service=None
    ) -> NoteRead:
        """
        Convert a chat conversation to a structured note.

        Uses LLM to summarize the chat and create a clean note.
        """
        # Get the chat
        stmt = select(Chat).where(Chat.id == request.chat_id)
        result = await self.session.execute(stmt)
        chat = result.scalar_one()

        # Generate title and content
        if request.title:
            title = request.title
        else:
            # Auto-generate title from chat (first 50 chars or LLM summary)
            title = chat.title[:50] if hasattr(chat, 'title') and chat.title else f"Note from Chat {chat.id}"

        # For MVP: Use chat content as-is
        # In production: Use LLM to summarize and structure
        content = self._extract_chat_content(chat)

        # Create note
        note = Note(
            search_space_id=request.search_space_id,
            user_id=user_id,
            title=title,
            content=content,
            source_chat_id=request.chat_id,
        )

        self.session.add(note)
        await self.session.commit()
        await self.session.refresh(note)
        return NoteRead.model_validate(note)

    async def create_manual_note(self, note_data: NoteCreate, user_id: str) -> NoteRead:
        """Create a note manually (not from chat)"""
        note = Note(
            search_space_id=note_data.search_space_id,
            user_id=user_id,
            title=note_data.title,
            content=note_data.content,
            source_chat_id=note_data.source_chat_id,
        )

        self.session.add(note)
        await self.session.commit()
        await self.session.refresh(note)
        return NoteRead.model_validate(note)

    async def search_notes(self, search_req: NoteSearchRequest, user_id: str) -> list[NoteRead]:
        """
        Search notes using PostgreSQL full-text search.

        Uses the GIN index on tsvector for fast search.
        """
        # Full-text search query
        search_query = text("""
            SELECT * FROM notes
            WHERE search_space_id = :search_space_id
            AND user_id = :user_id
            AND to_tsvector('english', title || ' ' || content) @@ plainto_tsquery('english', :query)
            ORDER BY created_at DESC
            LIMIT :limit
        """)

        result = await self.session.execute(
            search_query,
            {
                "search_space_id": search_req.search_space_id,
                "user_id": user_id,
                "query": search_req.query,
                "limit": search_req.limit,
            },
        )

        # Map results to Note objects
        notes = []
        for row in result:
            note = Note(
                id=row.id,
                search_space_id=row.search_space_id,
                user_id=row.user_id,
                title=row.title,
                content=row.content,
                source_chat_id=row.source_chat_id,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
            notes.append(NoteRead.model_validate(note))

        return notes

    async def get_all_notes(self, search_space_id: int, user_id: str) -> list[NoteRead]:
        """Get all notes for a search space"""
        stmt = (
            select(Note)
            .where(and_(Note.search_space_id == search_space_id, Note.user_id == user_id))
            .order_by(Note.updated_at.desc())
        )

        result = await self.session.execute(stmt)
        notes = result.scalars().all()
        return [NoteRead.model_validate(n) for n in notes]

    async def update_note(self, note_id: int, update_data: NoteUpdate, user_id: str) -> NoteRead:
        """Update an existing note"""
        stmt = select(Note).where(and_(Note.id == note_id, Note.user_id == user_id))
        result = await self.session.execute(stmt)
        note = result.scalar_one()

        # Update fields
        if update_data.title is not None:
            note.title = update_data.title
        if update_data.content is not None:
            note.content = update_data.content

        from datetime import datetime
        note.updated_at = datetime.utcnow()

        await self.session.commit()
        await self.session.refresh(note)
        return NoteRead.model_validate(note)

    async def delete_note(self, note_id: int, user_id: str) -> bool:
        """Delete a note"""
        stmt = select(Note).where(and_(Note.id == note_id, Note.user_id == user_id))
        result = await self.session.execute(stmt)
        note = result.scalar_one()

        await self.session.delete(note)
        await self.session.commit()
        return True

    # Helper methods

    def _extract_chat_content(self, chat) -> str:
        """Extract content from a chat for note conversion"""
        # For MVP: Return a simple text representation
        # In production: Format messages, add timestamps, use LLM to summarize

        content_parts = []

        # Add chat title
        if hasattr(chat, 'title') and chat.title:
            content_parts.append(f"# {chat.title}\n")

        # Add chat type if available
        if hasattr(chat, 'type'):
            content_parts.append(f"Type: {chat.type}\n")

        # Format messages
        if hasattr(chat, 'messages') and chat.messages:
            content_parts.append("\n## Conversation:\n")
            for msg in chat.messages:
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                content_parts.append(f"**{role.capitalize()}**: {content}\n")

        return "\n".join(content_parts) if content_parts else "Note created from chat"
