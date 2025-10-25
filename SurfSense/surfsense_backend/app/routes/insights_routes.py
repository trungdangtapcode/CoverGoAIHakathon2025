"""API routes for user insights and planning."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SearchSpace, User, get_async_session
from app.schemas.insights import InsightRequest, InsightResponse
from app.services.insights_service import InsightsService
from app.users import current_active_user
from app.utils.check_ownership import check_ownership

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/insights/generate", response_model=InsightResponse)
async def generate_insights_and_plan(
    request: InsightRequest,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """
    Generate insights and planning based on user's recent document activity.

    This endpoint analyzes the user's recent documents from:
    - Third-party connectors (Slack, Notion, GitHub, Gmail, etc.) - showing information consumption
    - Uploaded files - showing personal work and focus areas

    The analysis includes:
    1. Activity insights: Summary of recent activity, key topics, and document type breakdown
    2. Strategic plan: Actionable recommendations with prioritized tasks

    Args:
        request: InsightRequest containing search_space_id and analysis parameters
        session: Database session
        user: Current authenticated user

    Returns:
        InsightResponse with activity insights and recommended plan

    Raises:
        HTTPException 403: If user doesn't own the search space
        HTTPException 404: If search space not found or no documents available
        HTTPException 500: If analysis fails
    """
    try:
        # Verify search space ownership
        await check_ownership(session, SearchSpace, request.search_space_id, user)

        # Create insights service
        insights_service = InsightsService(session, user_id=str(user.id))

        # Generate insights and plan
        result = await insights_service.generate_insights_and_plan(
            search_space_id=request.search_space_id,
            num_documents=request.num_documents,
            include_connectors=request.include_connectors,
            include_files=request.include_files,
        )

        logger.info(
            f"Generated insights for user {user.id} in search space {request.search_space_id}"
        )

        return result

    except ValueError as e:
        # Handle validation errors
        logger.warning(f"Validation error for user {user.id}: {e}")
        raise HTTPException(status_code=404, detail=str(e)) from e

    except RuntimeError as e:
        # Handle LLM configuration errors
        logger.error(f"Runtime error for user {user.id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate plan: {str(e)}. Please ensure you have configured an LLM in your search space settings.",
        ) from e

    except HTTPException:
        # Re-raise HTTP exceptions (e.g., from check_ownership)
        raise

    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error generating insights for user {user.id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate insights and plan: {str(e)}",
        ) from e


@router.get("/insights/preview/{search_space_id}")
async def preview_document_activity(
    search_space_id: int,
    num_documents: int = 30,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """
    Preview recent document activity without generating a full plan.

    This is a lightweight endpoint that shows what documents would be analyzed
    without invoking the LLM for plan generation.

    Args:
        search_space_id: ID of the search space to preview
        num_documents: Number of recent documents to show (default: 30)
        session: Database session
        user: Current authenticated user

    Returns:
        Dictionary with document preview and basic statistics

    Raises:
        HTTPException 403: If user doesn't own the search space
        HTTPException 404: If search space not found
    """
    try:
        # Verify search space ownership
        await check_ownership(session, SearchSpace, search_space_id, user)

        # Create insights service
        insights_service = InsightsService(session, user_id=str(user.id))

        # Fetch recent documents
        documents = await insights_service._fetch_recent_documents(
            search_space_id=search_space_id,
            num_documents=num_documents,
            include_connectors=True,
            include_files=True,
        )

        if not documents:
            raise HTTPException(
                status_code=404,
                detail="No documents found in the specified search space",
            )

        # Generate basic insights (without LLM)
        insights = await insights_service._generate_activity_insights(documents)

        # Prepare document preview
        doc_preview = [
            {
                "id": doc.id,
                "title": doc.title,
                "type": doc.document_type.value,
                "created_at": doc.created_at.isoformat(),
                "content_preview": doc.content[:150] + "..."
                if len(doc.content) > 150
                else doc.content,
            }
            for doc in documents[:10]  # Show only first 10 in preview
        ]

        return {
            "search_space_id": search_space_id,
            "total_documents_found": len(documents),
            "documents_preview": doc_preview,
            "insights_preview": {
                "summary": insights.summary,
                "key_topics": insights.key_topics[:5],
                "document_type_breakdown": insights.connector_activity,
            },
            "message": "This is a preview. Use /insights/generate to create a full plan.",
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error previewing document activity for user {user.id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to preview activity: {str(e)}"
        ) from e
