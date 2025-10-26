from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db import Chat, Chunk, Document, SearchSpace, User, get_async_session, searchspace_links
from app.schemas import (
    SearchSpaceCreate,
    SearchSpaceImportRequest,
    SearchSpaceImportResponse,
    SearchSpaceLinkCreate,
    SearchSpaceRead,
    SearchSpaceUpdate,
)
from app.users import current_active_user
from app.utils.check_ownership import check_ownership

router = APIRouter()


@router.post("/searchspaces/", response_model=SearchSpaceRead)
async def create_search_space(
    search_space: SearchSpaceCreate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    try:
        db_search_space = SearchSpace(**search_space.model_dump(), user_id=user.id)
        session.add(db_search_space)
        await session.commit()
        await session.refresh(db_search_space)
        return db_search_space
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to create search space: {e!s}"
        ) from e


@router.post("/searchspaces/", response_model=list[SearchSpaceRead])
async def read_search_spaces(
    skip: int = 0,
    limit: int = 200,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    try:
        result = await session.execute(
            select(SearchSpace)
            .filter(SearchSpace.user_id == user.id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch search spaces: {e!s}"
        ) from e


@router.post("/searchspaces/{search_space_id}", response_model=SearchSpaceRead)
async def read_search_space(
    search_space_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    try:
        search_space = await check_ownership(
            session, SearchSpace, search_space_id, user
        )
        return search_space

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch search space: {e!s}"
        ) from e


@router.put("/searchspaces/{search_space_id}", response_model=SearchSpaceRead)
async def update_search_space(
    search_space_id: int,
    search_space_update: SearchSpaceUpdate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    try:
        db_search_space = await check_ownership(
            session, SearchSpace, search_space_id, user
        )
        update_data = search_space_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_search_space, key, value)
        await session.commit()
        await session.refresh(db_search_space)
        return db_search_space
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to update search space: {e!s}"
        ) from e


@router.delete("/searchspaces/{search_space_id}", response_model=dict)
async def delete_search_space(
    search_space_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    try:
        db_search_space = await check_ownership(
            session, SearchSpace, search_space_id, user
        )
        await session.delete(db_search_space)
        await session.commit()
        return {"message": "Search space deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to delete search space: {e!s}"
        ) from e


# SearchSpace linking endpoints (Obsidian-like graph)
@router.post("/searchspaces/links", response_model=dict)
async def link_search_spaces(
    link_data: SearchSpaceLinkCreate,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """
    Link two SearchSpaces together (source -> target).
    Both SearchSpaces must belong to the current user.
    """
    try:
        # Verify ownership of both SearchSpaces
        try:
            source_space = await check_ownership(
                session, SearchSpace, link_data.source_space_id, user
            )
        except HTTPException as e:
            if e.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail=f"Source SearchSpace with ID {link_data.source_space_id} not found or not accessible"
                ) from e
            raise

        try:
            target_space = await check_ownership(
                session, SearchSpace, link_data.target_space_id, user
            )
        except HTTPException as e:
            if e.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail=f"Target SearchSpace with ID {link_data.target_space_id} not found or not accessible"
                ) from e
            raise

        # Prevent self-linking
        if link_data.source_space_id == link_data.target_space_id:
            raise HTTPException(
                status_code=400,
                detail="Cannot link a SearchSpace to itself"
            )
        
        # Check if link already exists
        result = await session.execute(
            select(searchspace_links).where(
                and_(
                    searchspace_links.c.source_space_id == link_data.source_space_id,
                    searchspace_links.c.target_space_id == link_data.target_space_id,
                )
            )
        )
        existing_link = result.first()
        
        if existing_link:
            raise HTTPException(
                status_code=400,
                detail="Link already exists between these SearchSpaces"
            )
        
        # Create the link
        await session.execute(
            searchspace_links.insert().values(
                source_space_id=link_data.source_space_id,
                target_space_id=link_data.target_space_id,
            )
        )
        await session.commit()
        
        return {
            "message": "SearchSpaces linked successfully",
            "source_space": source_space.name,
            "target_space": target_space.name,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to link SearchSpaces: {e!s}"
        ) from e


@router.delete("/searchspaces/links/{source_space_id}/{target_space_id}", response_model=dict)
async def unlink_search_spaces(
    source_space_id: int,
    target_space_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """
    Remove a link between two SearchSpaces.
    Both SearchSpaces must belong to the current user.
    """
    try:
        # Verify ownership of both SearchSpaces
        await check_ownership(session, SearchSpace, source_space_id, user)
        await check_ownership(session, SearchSpace, target_space_id, user)
        
        # Delete the link
        result = await session.execute(
            searchspace_links.delete().where(
                and_(
                    searchspace_links.c.source_space_id == source_space_id,
                    searchspace_links.c.target_space_id == target_space_id,
                )
            )
        )
        
        if result.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Link not found between these SearchSpaces"
            )
        
        await session.commit()
        return {"message": "SearchSpaces unlinked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to unlink SearchSpaces: {e!s}"
        ) from e


@router.post("/searchspaces/{search_space_id}/links", response_model=dict)
async def get_search_space_links(
    search_space_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """
    Get all SearchSpaces linked to and from a given SearchSpace.
    Returns both outgoing links (spaces this one references) and 
    incoming links (spaces that reference this one).
    """
    try:
        # Verify ownership
        space = await check_ownership(session, SearchSpace, search_space_id, user)
        
        # Get outgoing links (spaces this space references)
        outgoing_result = await session.execute(
            select(SearchSpace, searchspace_links.c.created_at)
            .join(
                searchspace_links,
                SearchSpace.id == searchspace_links.c.target_space_id
            )
            .where(searchspace_links.c.source_space_id == search_space_id)
        )
        outgoing_links = [
            {
                "id": space.id,
                "name": space.name,
                "description": space.description,
                "created_at": created_at,
            }
            for space, created_at in outgoing_result.all()
        ]
        
        # Get incoming links (spaces that reference this space)
        incoming_result = await session.execute(
            select(SearchSpace, searchspace_links.c.created_at)
            .join(
                searchspace_links,
                SearchSpace.id == searchspace_links.c.source_space_id
            )
            .where(searchspace_links.c.target_space_id == search_space_id)
        )
        incoming_links = [
            {
                "id": space.id,
                "name": space.name,
                "description": space.description,
                "created_at": created_at,
            }
            for space, created_at in incoming_result.all()
        ]
        
        return {
            "search_space": {
                "id": space.id,
                "name": space.name,
                "description": space.description,
            },
            "linked_to": outgoing_links,  # Spaces this one references
            "linked_from": incoming_links,  # Spaces that reference this one
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve SearchSpace links: {e!s}"
        ) from e


@router.post("/searchspaces/import", response_model=SearchSpaceImportResponse)
async def import_workspace_data(
    import_request: SearchSpaceImportRequest,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """
    Import selected data (messages, content, titles) from one SearchSpace to another.

    This endpoint extracts specific fields from documents and chats in the source workspace
    and creates new documents in the target workspace for LLM usage.
    """
    try:
        # Verify ownership of both SearchSpaces
        try:
            source_space = await check_ownership(
                session, SearchSpace, import_request.source_space_id, user
            )
        except HTTPException as e:
            if e.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail=f"Source SearchSpace with ID {import_request.source_space_id} not found or not accessible"
                ) from e
            raise

        try:
            target_space = await check_ownership(
                session, SearchSpace, import_request.target_space_id, user
            )
        except HTTPException as e:
            if e.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail=f"Target SearchSpace with ID {import_request.target_space_id} not found or not accessible"
                ) from e
            raise

        # Prevent importing from same workspace
        if import_request.source_space_id == import_request.target_space_id:
            raise HTTPException(
                status_code=400,
                detail="Cannot import from a SearchSpace to itself"
            )

        imported_documents = 0
        imported_messages = 0
        imported_items = []

        # Import documents (content, titles, metadata)
        if any(field in import_request.import_fields for field in ["content", "titles", "metadata"]):
            # Build document query
            doc_query = select(Document).where(Document.search_space_id == import_request.source_space_id)

            # Filter by document types if specified
            if import_request.import_document_types:
                from app.db import DocumentType
                doc_types = []
                for doc_type in import_request.import_document_types:
                    try:
                        doc_types.append(DocumentType[doc_type])
                    except KeyError:
                        continue
                if doc_types:
                    doc_query = doc_query.where(Document.document_type.in_(doc_types))

            # Apply limit
            if import_request.limit:
                doc_query = doc_query.limit(import_request.limit)

            result = await session.execute(doc_query)
            source_documents = result.scalars().all()

            for doc in source_documents:
                # Extract requested fields
                extracted_content = ""
                extracted_metadata = {}

                if "titles" in import_request.import_fields:
                    extracted_content += f"Title: {doc.title}\n\n"

                if "content" in import_request.import_fields:
                    extracted_content += f"Content: {doc.content}\n\n"

                if "metadata" in import_request.import_fields and doc.document_metadata:
                    extracted_metadata = doc.document_metadata
                    # Add metadata as readable text
                    metadata_text = "\n".join([f"{key}: {value}" for key, value in doc.document_metadata.items()])
                    extracted_content += f"Metadata: {metadata_text}\n\n"

                # Create new document in target workspace with extracted data
                if extracted_content.strip():
                    new_doc = Document(
                        title=f"Imported: {doc.title}",
                        document_type=doc.document_type,
                        document_metadata={
                            **extracted_metadata,
                            "imported_from_workspace_id": import_request.source_space_id,
                            "imported_from_workspace_name": source_space.name,
                            "original_document_id": doc.id,
                            "import_fields": import_request.import_fields
                        },
                        content=extracted_content.strip(),
                        content_hash=f"import_{doc.id}_{hash(extracted_content)}",
                        search_space_id=import_request.target_space_id
                    )
                    session.add(new_doc)
                    imported_documents += 1

                    imported_items.append({
                        "type": "document",
                        "original_id": doc.id,
                        "title": doc.title,
                        "extracted_fields": [field for field in import_request.import_fields if field in ["titles", "content", "metadata"]]
                    })

        # Import chat messages
        if "messages" in import_request.import_fields:
            chat_query = select(Chat).where(Chat.search_space_id == import_request.source_space_id)

            if import_request.limit:
                chat_query = chat_query.limit(import_request.limit)

            result = await session.execute(chat_query)
            source_chats = result.scalars().all()

            for chat in source_chats:
                # Extract messages from chat
                messages = chat.messages if chat.messages else []

                if messages:
                    # Convert messages to readable format
                    messages_content = f"Chat: {chat.title}\n\n"
                    for msg in messages:
                        role = msg.get("role", "user")
                        content = msg.get("content", "")
                        messages_content += f"{role.capitalize()}: {content}\n\n"

                    # Create new document with chat messages
                    new_doc = Document(
                        title=f"Imported Chat: {chat.title}",
                        document_type="EXTENSION",  # Use EXTENSION as generic type for imported chats
                        document_metadata={
                            "imported_from_workspace_id": import_request.source_space_id,
                            "imported_from_workspace_name": source_space.name,
                            "original_chat_id": chat.id,
                            "import_fields": ["messages"],
                            "chat_type": chat.type.value if hasattr(chat, 'type') else "unknown"
                        },
                        content=messages_content.strip(),
                        content_hash=f"import_chat_{chat.id}_{hash(messages_content)}",
                        search_space_id=import_request.target_space_id
                    )
                    session.add(new_doc)
                    imported_messages += 1

                    imported_items.append({
                        "type": "chat",
                        "original_id": chat.id,
                        "title": chat.title,
                        "extracted_fields": ["messages"]
                    })

        await session.commit()

        return SearchSpaceImportResponse(
            message=f"Successfully imported {imported_documents} documents and {imported_messages} chat conversations from '{source_space.name}' to '{target_space.name}'",
            imported_documents=imported_documents,
            imported_messages=imported_messages,
            imported_items=imported_items
        )

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to import workspace data: {e!s}"
        ) from e


