"""Service for Work Mode - Task Management and Sync"""
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import and_, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Document, Task
from app.schemas.task import TaskCreate, TaskFilterRequest, TaskRead


class TaskService:
    """Service for managing tasks and syncing from connectors"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def sync_tasks_from_connectors(
        self, search_space_id: int, user_id: str, connector_types: list[str]
    ) -> list[TaskRead]:
        """
        Sync tasks from workspace connectors (Linear, Jira, Slack, etc.)

        This queries documents that were indexed from connectors and extracts task information.
        """
        synced_tasks = []

        for connector_type in connector_types:
            # Query documents from this connector type
            # DocumentType enum has: LINEAR_CONNECTOR, JIRA_CONNECTOR, SLACK_CONNECTOR, etc.
            stmt = select(Document).where(
                and_(
                    Document.search_space_id == search_space_id,
                    Document.document_type == f"{connector_type}_CONNECTOR",
                )
            )
            result = await self.session.execute(stmt)
            connector_docs = result.scalars().all()

            for doc in connector_docs:
                # Extract task info from document metadata
                metadata = doc.document_metadata or {}

                # Check if this is a task-like document
                if not self._is_task_document(metadata, connector_type):
                    continue

                # Extract task details
                external_id = metadata.get("id") or metadata.get("issue_key") or str(doc.id)
                title = doc.title
                description = doc.content[:500] if doc.content else None

                # Extract priority and due date from metadata
                priority = self._extract_priority(metadata, connector_type)
                due_date = self._extract_due_date(metadata, connector_type)
                status_raw = self._extract_status(metadata, connector_type)

                # Map to our simple UNDONE/DONE status
                status = "DONE" if status_raw in ["DONE", "CLOSED", "COMPLETED", "RESOLVED"] else "UNDONE"

                # Check if task already exists
                existing_task = await self._get_task_by_external_id(
                    search_space_id, connector_type, external_id
                )

                if existing_task:
                    # Update existing task
                    existing_task.title = title
                    existing_task.description = description
                    existing_task.priority = priority
                    existing_task.due_date = due_date
                    existing_task.status = status
                    existing_task.external_metadata = metadata
                    existing_task.updated_at = datetime.utcnow()
                    if status == "DONE" and not existing_task.completed_at:
                        existing_task.completed_at = datetime.utcnow()

                    synced_tasks.append(TaskRead.model_validate(existing_task))
                else:
                    # Create new task
                    new_task = Task(
                        search_space_id=search_space_id,
                        user_id=user_id,
                        title=title,
                        description=description,
                        source_type=connector_type,
                        external_id=external_id,
                        external_url=metadata.get("url") or metadata.get("link"),
                        external_metadata=metadata,
                        status=status,
                        priority=priority,
                        due_date=due_date,
                        completed_at=datetime.utcnow() if status == "DONE" else None,
                    )
                    self.session.add(new_task)
                    await self.session.flush()
                    synced_tasks.append(TaskRead.model_validate(new_task))

        await self.session.commit()
        return synced_tasks

    async def get_tasks_filtered(
        self, filter_req: TaskFilterRequest, user_id: str
    ) -> list[TaskRead]:
        """
        Get tasks with filtering and sorting.

        Sort priority: priority (URGENT > HIGH > MEDIUM > LOW) → due_date ASC → created_at ASC
        """
        conditions = [Task.search_space_id == filter_req.search_space_id, Task.user_id == user_id]

        if filter_req.status:
            conditions.append(Task.status == filter_req.status)

        stmt = select(Task).where(and_(*conditions))

        # Apply sorting
        if filter_req.sort_by_priority:
            # Custom priority ordering: URGENT > HIGH > MEDIUM > LOW > NULL
            priority_order = text(
                "CASE "
                "WHEN priority = 'URGENT' THEN 1 "
                "WHEN priority = 'HIGH' THEN 2 "
                "WHEN priority = 'MEDIUM' THEN 3 "
                "WHEN priority = 'LOW' THEN 4 "
                "ELSE 5 END"
            )
            stmt = stmt.order_by(
                priority_order,
                Task.due_date.asc().nulls_last(),
                Task.created_at.asc(),
            )
        else:
            stmt = stmt.order_by(Task.created_at.desc())

        result = await self.session.execute(stmt)
        tasks = result.scalars().all()
        return [TaskRead.model_validate(task) for task in tasks]

    async def complete_task(self, task_id: int, user_id: str) -> TaskRead:
        """
        Mark task as complete and auto-link recent chats and documents.

        Auto-linking logic:
        - Find chats and documents from the last 2 hours
        - Use semantic similarity > 0.7 with task title/description
        """
        stmt = select(Task).where(and_(Task.id == task_id, Task.user_id == user_id))
        result = await self.session.execute(stmt)
        task = result.scalar_one()

        # Mark as done
        task.status = "DONE"
        task.completed_at = datetime.utcnow()
        task.updated_at = datetime.utcnow()

        # Auto-link recent chats and documents
        # TODO: Implement semantic similarity search
        # For MVP, we'll link items from last 2 hours in the same search space
        two_hours_ago = datetime.utcnow() - timedelta(hours=2)

        # Find recent chats (simplified - would use vector similarity in production)
        from app.db import Chat
        chat_stmt = select(Chat.id).where(
            and_(
                Chat.search_space_id == task.search_space_id,
                Chat.created_at >= two_hours_ago,
            )
        ).limit(5)
        chat_result = await self.session.execute(chat_stmt)
        recent_chat_ids = [row[0] for row in chat_result.all()]

        # Find recent documents
        doc_stmt = select(Document.id).where(
            and_(
                Document.search_space_id == task.search_space_id,
                Document.created_at >= two_hours_ago,
            )
        ).limit(5)
        doc_result = await self.session.execute(doc_stmt)
        recent_doc_ids = [row[0] for row in doc_result.all()]

        task.linked_chat_ids = recent_chat_ids
        task.linked_document_ids = recent_doc_ids

        await self.session.commit()
        await self.session.refresh(task)
        return TaskRead.model_validate(task)

    async def create_manual_task(self, task_data: TaskCreate, user_id: str) -> TaskRead:
        """Create a manual task (not from connectors)"""
        new_task = Task(
            search_space_id=task_data.search_space_id,
            user_id=user_id,
            title=task_data.title,
            description=task_data.description,
            source_type="MANUAL",
            status="UNDONE",
            priority=task_data.priority,
            due_date=task_data.due_date,
        )
        self.session.add(new_task)
        await self.session.commit()
        await self.session.refresh(new_task)
        return TaskRead.model_validate(new_task)

    # Helper methods

    async def _get_task_by_external_id(
        self, search_space_id: int, source_type: str, external_id: str
    ) -> Optional[Task]:
        """Get existing task by external ID"""
        stmt = select(Task).where(
            and_(
                Task.search_space_id == search_space_id,
                Task.source_type == source_type,
                Task.external_id == external_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def _is_task_document(self, metadata: dict, connector_type: str) -> bool:
        """Check if document represents a task"""
        if connector_type == "LINEAR":
            # Linear issues are tasks
            return metadata.get("type") == "issue" or "issue" in metadata
        elif connector_type == "JIRA":
            # Jira issues are tasks
            return metadata.get("issue_key") is not None or "fields" in metadata
        elif connector_type == "SLACK":
            # Slack tasks might be marked with specific emoji or keywords
            return False  # Skip Slack for MVP
        return False

    def _extract_priority(self, metadata: dict, connector_type: str) -> Optional[str]:
        """Extract priority from connector metadata"""
        if connector_type == "LINEAR":
            priority_num = metadata.get("priority")
            if priority_num == 0: return "URGENT"
            if priority_num == 1: return "HIGH"
            if priority_num == 2: return "MEDIUM"
            if priority_num == 3: return "LOW"
        elif connector_type == "JIRA":
            priority_name = metadata.get("fields", {}).get("priority", {}).get("name", "").upper()
            if "HIGHEST" in priority_name or "BLOCKER" in priority_name:
                return "URGENT"
            if "HIGH" in priority_name:
                return "HIGH"
            if "MEDIUM" in priority_name:
                return "MEDIUM"
            if "LOW" in priority_name:
                return "LOW"
        return None

    def _extract_due_date(self, metadata: dict, connector_type: str) -> Optional[datetime]:
        """Extract due date from connector metadata"""
        if connector_type == "LINEAR":
            due_str = metadata.get("dueDate")
            if due_str:
                try:
                    return datetime.fromisoformat(due_str.replace("Z", "+00:00"))
                except:
                    pass
        elif connector_type == "JIRA":
            due_str = metadata.get("fields", {}).get("duedate")
            if due_str:
                try:
                    return datetime.fromisoformat(due_str)
                except:
                    pass
        return None

    def _extract_status(self, metadata: dict, connector_type: str) -> str:
        """Extract status from connector metadata"""
        if connector_type == "LINEAR":
            state = metadata.get("state", {})
            return state.get("name", "TODO").upper()
        elif connector_type == "JIRA":
            status = metadata.get("fields", {}).get("status", {})
            return status.get("name", "TODO").upper()
        return "TODO"
