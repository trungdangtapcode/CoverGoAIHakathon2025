"""API routes for Study Mode - Flashcards and MCQs"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import User, get_async_session
from app.schemas.study import (
    GenerateStudyMaterialsRequest,
    StudyMaterialAttempt,
    StudyMaterialRead,
)
from app.services.study_service import StudyService
from app.users import current_active_user

router = APIRouter(prefix="/study", tags=["Study Mode"])


@router.post("/generate", response_model=list[StudyMaterialRead])
async def generate_study_materials(
    request: GenerateStudyMaterialsRequest,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """
    Generate AI-powered study materials (flashcards or MCQs) from documents.

    This endpoint:
    1. Takes document IDs and material type
    2. Uses LLM to generate questions and answers
    3. Stores materials in database
    4. Returns generated materials

    Example:
    ```json
    {
        "document_ids": [1, 2, 3],
        "material_type": "FLASHCARD",
        "count": 10
    }
    ```
    """
    service = StudyService(session)

    # For MVP: Use a simple LLM service mock
    # In production, this would use the actual LLM service
    class SimpleLLMService:
        async def generate(self, prompt: str) -> str:
            # Mock response for hackathon demo
            if "flashcard" in prompt.lower():
                return """Q: What is the main concept?
A: The main concept is about active learning.

Q: How does it improve retention?
A: By engaging with the material through questions and answers.

Q: What are the benefits?
A: Better memory, deeper understanding, and practical application."""

            else:  # MCQ
                return """Q: What is the primary goal?
A) To read passively
B) To engage actively
C) To memorize facts
D) To skip content
Correct: B

Q: Which method works best?
A) Reading only
B) Watching videos
C) Active recall
D) Highlighting text
Correct: C"""

    try:
        materials = await service.generate_study_materials(request, SimpleLLMService())
        return materials
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate materials: {str(e)}")


@router.get("/{search_space_id}", response_model=list[StudyMaterialRead])
async def get_study_materials(
    search_space_id: int,
    material_type: str = None,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """
    Get all study materials for a search space.

    Optionally filter by material_type: 'FLASHCARD' or 'MCQ'
    """
    service = StudyService(session)
    try:
        materials = await service.get_study_materials(search_space_id, material_type)
        return materials
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get materials: {str(e)}")


@router.post("/attempt", response_model=StudyMaterialRead)
async def record_attempt(
    attempt: StudyMaterialAttempt,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """
    Record a study attempt and update performance statistics.

    This tracks:
    - times_attempted (incremented)
    - times_correct (incremented if is_correct=true)
    - last_attempted_at (updated to now)
    """
    service = StudyService(session)
    try:
        updated_material = await service.record_attempt(attempt)
        return updated_material
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record attempt: {str(e)}")


@router.get("/stats/{search_space_id}")
async def get_performance_stats(
    search_space_id: int,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """
    Get learning performance statistics for a search space.

    Returns:
    - total_materials
    - flashcards_count
    - mcqs_count
    - total_attempts
    - total_correct
    - accuracy_percentage
    - mastered_materials (correct >= 3 times)
    """
    service = StudyService(session)
    try:
        stats = await service.get_performance_stats(search_space_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")
