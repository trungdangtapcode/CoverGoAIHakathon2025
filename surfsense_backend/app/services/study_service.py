"""Service for Study Mode - AI-generated flashcards and MCQs"""
from datetime import datetime
from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Document, StudyMaterial
from app.schemas.study import (
    GenerateStudyMaterialsRequest,
    StudyMaterialAttempt,
    StudyMaterialCreate,
    StudyMaterialRead,
)


class StudyService:
    """Service for generating and managing study materials"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def generate_study_materials(
        self, request: GenerateStudyMaterialsRequest, llm_service
    ) -> list[StudyMaterialRead]:
        """
        Generate study materials (flashcards or MCQs) from documents using LLM.

        For hackathon MVP: Uses simple prompting to generate materials.
        """
        # Get documents
        stmt = select(Document).where(Document.id.in_(request.document_ids))
        result = await self.session.execute(stmt)
        documents = result.scalars().all()

        if not documents:
            return []

        # Combine document content
        combined_content = "\n\n".join([f"Document: {doc.title}\n{doc.content[:2000]}" for doc in documents])

        # Generate materials using LLM
        materials_data = []

        if request.material_type == "FLASHCARD":
            prompt = f"""Based on the following documents, generate {request.count} flashcard-style question-answer pairs for studying.
Format each as:
Q: [question]
A: [answer]

Documents:
{combined_content}

Generate {request.count} flashcards:"""

            response = await llm_service.generate(prompt)
            # Parse response into Q&A pairs
            materials_data = self._parse_flashcards(response, documents[0].search_space_id, documents[0].id)

        elif request.material_type == "MCQ":
            prompt = f"""Based on the following documents, generate {request.count} multiple-choice questions for studying.
Format each as:
Q: [question]
A) [option A]
B) [option B]
C) [option C]
D) [option D]
Correct: [A/B/C/D]

Documents:
{combined_content}

Generate {request.count} MCQs:"""

            response = await llm_service.generate(prompt)
            # Parse response into MCQs
            materials_data = self._parse_mcqs(response, documents[0].search_space_id, documents[0].id)

        # Save to database
        created_materials = []
        for material_data in materials_data[:request.count]:  # Limit to requested count
            material = StudyMaterial(**material_data)
            self.session.add(material)
            await self.session.flush()
            created_materials.append(StudyMaterialRead.model_validate(material))

        await self.session.commit()
        return created_materials

    async def get_study_materials(
        self, search_space_id: int, material_type: Optional[str] = None
    ) -> list[StudyMaterialRead]:
        """Get all study materials for a search space, optionally filtered by type"""
        conditions = [StudyMaterial.search_space_id == search_space_id]
        if material_type:
            conditions.append(StudyMaterial.material_type == material_type)

        stmt = select(StudyMaterial).where(and_(*conditions)).order_by(StudyMaterial.created_at.desc())
        result = await self.session.execute(stmt)
        materials = result.scalars().all()
        return [StudyMaterialRead.model_validate(m) for m in materials]

    async def record_attempt(self, attempt: StudyMaterialAttempt) -> StudyMaterialRead:
        """Record a study attempt and update performance statistics"""
        stmt = select(StudyMaterial).where(StudyMaterial.id == attempt.material_id)
        result = await self.session.execute(stmt)
        material = result.scalar_one()

        # Update statistics
        material.times_attempted += 1
        if attempt.is_correct:
            material.times_correct += 1
        material.last_attempted_at = datetime.utcnow()

        await self.session.commit()
        await self.session.refresh(material)
        return StudyMaterialRead.model_validate(material)

    async def get_performance_stats(self, search_space_id: int) -> dict:
        """Get learning performance statistics for a search space"""
        stmt = select(StudyMaterial).where(StudyMaterial.search_space_id == search_space_id)
        result = await self.session.execute(stmt)
        materials = result.scalars().all()

        total_materials = len(materials)
        total_attempts = sum(m.times_attempted for m in materials)
        total_correct = sum(m.times_correct for m in materials)

        accuracy = (total_correct / total_attempts * 100) if total_attempts > 0 else 0

        # Materials by type
        flashcards = [m for m in materials if m.material_type == "FLASHCARD"]
        mcqs = [m for m in materials if m.material_type == "MCQ"]

        return {
            "total_materials": total_materials,
            "flashcards_count": len(flashcards),
            "mcqs_count": len(mcqs),
            "total_attempts": total_attempts,
            "total_correct": total_correct,
            "accuracy_percentage": round(accuracy, 2),
            "mastered_materials": len([m for m in materials if m.times_correct >= 3 and m.times_attempted >= 3]),
        }

    # Helper methods for parsing LLM responses

    def _parse_flashcards(self, response: str, search_space_id: int, document_id: int) -> list[dict]:
        """Parse LLM response into flashcard data"""
        materials = []
        lines = response.strip().split('\n')

        current_q = None
        for line in lines:
            line = line.strip()
            if line.startswith('Q:'):
                current_q = line[2:].strip()
            elif line.startswith('A:') and current_q:
                answer = line[2:].strip()
                materials.append({
                    "search_space_id": search_space_id,
                    "document_id": document_id,
                    "material_type": "FLASHCARD",
                    "question": current_q,
                    "answer": answer,
                    "options": None,
                })
                current_q = None

        return materials

    def _parse_mcqs(self, response: str, search_space_id: int, document_id: int) -> list[dict]:
        """Parse LLM response into MCQ data"""
        materials = []
        lines = response.strip().split('\n')

        current_q = None
        current_options = {}
        correct_answer = None

        for line in lines:
            line = line.strip()
            if line.startswith('Q:'):
                # Save previous MCQ if exists
                if current_q and current_options and correct_answer:
                    materials.append({
                        "search_space_id": search_space_id,
                        "document_id": document_id,
                        "material_type": "MCQ",
                        "question": current_q,
                        "answer": correct_answer,
                        "options": current_options,
                    })

                current_q = line[2:].strip()
                current_options = {}
                correct_answer = None

            elif line.startswith(('A)', 'B)', 'C)', 'D)')):
                key = line[0]
                value = line[2:].strip()
                current_options[key] = value

            elif line.startswith('Correct:'):
                correct_answer = line.split(':')[1].strip()

        # Save last MCQ
        if current_q and current_options and correct_answer:
            materials.append({
                "search_space_id": search_space_id,
                "document_id": document_id,
                "material_type": "MCQ",
                "question": current_q,
                "answer": correct_answer,
                "options": current_options,
            })

        return materials
