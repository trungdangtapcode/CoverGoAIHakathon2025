"""Tests for Work Mode - Task Management"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Task
from app.services.task_service import TaskService


class TestTaskService:
    """Test TaskService methods"""

    @pytest.mark.asyncio
    async def test_create_manual_task(self, async_session: AsyncSession, test_user, test_search_space):
        """Test creating a manual task"""
        from app.schemas.task import TaskCreate

        service = TaskService(async_session)

        task_data = TaskCreate(
            search_space_id=test_search_space.id,
            title="Complete feature implementation",
            description="Implement the new MVP feature",
            priority="HIGH",
            due_date=None,
        )

        task = await service.create_manual_task(task_data, user_id=str(test_user.id))

        assert task.title == "Complete feature implementation"
        assert task.priority == "HIGH"
        assert task.status == "UNDONE"
        assert task.source_type == "MANUAL"

    @pytest.mark.asyncio
    async def test_get_tasks_filtered(self, async_session: AsyncSession, test_user, test_search_space):
        """Test filtering and sorting tasks"""
        from app.schemas.task import TaskFilterRequest
        from datetime import datetime, timedelta

        service = TaskService(async_session)

        # Create multiple tasks with different priorities
        tasks_data = [
            Task(
                search_space_id=test_search_space.id,
                user_id=test_user.id,
                title="Urgent task",
                status="UNDONE",
                priority="URGENT",
                source_type="MANUAL",
            ),
            Task(
                search_space_id=test_search_space.id,
                user_id=test_user.id,
                title="Low priority task",
                status="UNDONE",
                priority="LOW",
                source_type="MANUAL",
            ),
            Task(
                search_space_id=test_search_space.id,
                user_id=test_user.id,
                title="High priority task",
                status="UNDONE",
                priority="HIGH",
                due_date=datetime.utcnow() + timedelta(days=1),
                source_type="MANUAL",
            ),
        ]

        for task in tasks_data:
            async_session.add(task)
        await async_session.commit()

        # Filter and get tasks
        filter_req = TaskFilterRequest(
            search_space_id=test_search_space.id,
            status="UNDONE",
            sort_by_priority=True,
        )

        tasks = await service.get_tasks_filtered(filter_req, user_id=str(test_user.id))

        # Verify sorting: URGENT > HIGH > LOW
        assert len(tasks) == 3
        assert tasks[0].priority == "URGENT"
        assert tasks[1].priority == "HIGH"
        assert tasks[2].priority == "LOW"

    @pytest.mark.asyncio
    async def test_complete_task(self, async_session: AsyncSession, test_user, test_search_space):
        """Test completing a task"""
        service = TaskService(async_session)

        # Create a task
        task = Task(
            search_space_id=test_search_space.id,
            user_id=test_user.id,
            title="Task to complete",
            status="UNDONE",
            source_type="MANUAL",
        )
        async_session.add(task)
        await async_session.commit()
        await async_session.refresh(task)

        # Complete the task
        completed_task = await service.complete_task(task.id, user_id=str(test_user.id))

        assert completed_task.status == "DONE"
        assert completed_task.completed_at is not None
        # Auto-linking will be tested separately with actual chats/docs


class TestTaskRoutes:
    """Test Task API routes"""

    def test_create_task_endpoint(
        self, test_client: TestClient, mock_current_user, test_search_space
    ):
        """Test POST /api/v1/tasks/create"""
        response = test_client.post(
            "/api/v1/tasks/create",
            json={
                "search_space_id": test_search_space.id,
                "title": "New task from API",
                "description": "Created via API test",
                "priority": "MEDIUM",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New task from API"
        assert data["priority"] == "MEDIUM"
        assert data["status"] == "UNDONE"

    def test_get_tasks_endpoint(
        self, test_client: TestClient, mock_current_user, test_search_space, async_session
    ):
        """Test POST /api/v1/tasks/filter"""
        response = test_client.post(
            "/api/v1/tasks/filter",
            json={
                "search_space_id": test_search_space.id,
                "status": "UNDONE",
                "sort_by_priority": True,
            },
        )

        assert response.status_code == 200
        assert isinstance(response.json(), list)
