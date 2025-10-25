"""Tests for the insights service and routes."""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Document, DocumentType
from app.schemas.insights import InsightRequest
from app.services.insights_service import InsightsService


class TestInsightsService:
    """Test InsightsService functionality."""

    @pytest.mark.asyncio
    async def test_fetch_recent_documents(
        self, async_session: AsyncSession, test_user, test_search_space
    ):
        """Test fetching recent documents with filters."""
        # Create test documents
        base_time = datetime.utcnow()
        
        # Create connector documents
        for i in range(5):
            doc = Document(
                title=f"Slack Message {i}",
                content=f"Content of slack message {i} about project planning",
                document_type=DocumentType.SLACK_CONNECTOR,
                search_space_id=test_search_space.id,
                content_hash=f"hash_slack_{i}",
                created_at=base_time - timedelta(hours=i),
            )
            async_session.add(doc)
        
        # Create file documents
        for i in range(3):
            doc = Document(
                title=f"Design Document {i}",
                content=f"Design specifications for feature {i}",
                document_type=DocumentType.FILE,
                search_space_id=test_search_space.id,
                content_hash=f"hash_file_{i}",
                created_at=base_time - timedelta(hours=i + 5),
            )
            async_session.add(doc)
        
        await async_session.commit()

        # Test fetching all documents
        service = InsightsService(async_session, user_id=str(test_user.id))
        documents = await service._fetch_recent_documents(
            search_space_id=test_search_space.id,
            num_documents=10,
            include_connectors=True,
            include_files=True,
        )

        assert len(documents) == 8  # 5 slack + 3 files
        
        # Test fetching only connectors
        documents = await service._fetch_recent_documents(
            search_space_id=test_search_space.id,
            num_documents=10,
            include_connectors=True,
            include_files=False,
        )

        assert len(documents) == 5  # Only slack
        assert all(doc.document_type == DocumentType.SLACK_CONNECTOR for doc in documents)
        
        # Test fetching only files
        documents = await service._fetch_recent_documents(
            search_space_id=test_search_space.id,
            num_documents=10,
            include_connectors=False,
            include_files=True,
        )

        assert len(documents) == 3  # Only files
        assert all(doc.document_type == DocumentType.FILE for doc in documents)

    @pytest.mark.asyncio
    async def test_generate_activity_insights(
        self, async_session: AsyncSession, test_user, test_search_space
    ):
        """Test generating activity insights from documents."""
        # Create test documents
        base_time = datetime.utcnow()
        test_docs = []
        
        # Create diverse documents
        for i in range(5):
            doc = Document(
                title=f"Project Meeting Notes {i}",
                content=f"Discussion about project timeline and deliverables",
                document_type=DocumentType.NOTION_CONNECTOR,
                search_space_id=test_search_space.id,
                content_hash=f"hash_notion_{i}",
                created_at=base_time - timedelta(days=i),
            )
            async_session.add(doc)
            test_docs.append(doc)
        
        for i in range(3):
            doc = Document(
                title=f"Development Task {i}",
                content=f"Implementation details for feature {i}",
                document_type=DocumentType.FILE,
                search_space_id=test_search_space.id,
                content_hash=f"hash_file2_{i}",
                created_at=base_time - timedelta(days=i + 5),
            )
            async_session.add(doc)
            test_docs.append(doc)
        
        await async_session.commit()

        # Generate insights
        service = InsightsService(async_session, user_id=str(test_user.id))
        insights = await service._generate_activity_insights(test_docs)

        # Verify insights
        assert insights.document_count == 8
        assert "8 document(s)" in insights.summary
        assert len(insights.key_topics) > 0  # Should extract some topics
        assert insights.connector_activity[DocumentType.NOTION_CONNECTOR.value] == 5
        assert insights.connector_activity[DocumentType.FILE.value] == 3

    @pytest.mark.asyncio
    async def test_generate_fallback_plan(
        self, async_session: AsyncSession, test_user, test_search_space
    ):
        """Test fallback plan generation when LLM fails."""
        from app.schemas.insights import ActivityInsight
        
        service = InsightsService(async_session, user_id=str(test_user.id))
        
        # Create mock insights
        insights = ActivityInsight(
            summary="Analyzed 10 documents from the last 2 days.",
            key_topics=["Project", "Development", "Design"],
            connector_activity={
                "SLACK_CONNECTOR": 5,
                "FILE": 3,
                "NOTION_CONNECTOR": 2,
            },
            document_count=10,
            time_period_summary="last 2 days",
        )

        # Generate fallback plan
        plan = service._generate_fallback_plan(insights)

        # Verify plan structure
        assert plan.title
        assert plan.description
        assert len(plan.action_items) > 0
        assert plan.estimated_timeframe

        # Verify action items have required fields
        for item in plan.action_items:
            assert item.title
            assert item.description
            assert item.priority in ["HIGH", "MEDIUM", "LOW"]
            assert item.rationale


class TestInsightsRoutes:
    """Test insights API routes."""

    @pytest.mark.asyncio
    async def test_preview_endpoint_basic(
        self, client, test_user, test_search_space, async_session
    ):
        """Test the preview endpoint returns document info."""
        # Create test documents
        base_time = datetime.utcnow()
        for i in range(5):
            doc = Document(
                title=f"Test Document {i}",
                content=f"Test content {i}",
                document_type=DocumentType.SLACK_CONNECTOR,
                search_space_id=test_search_space.id,
                content_hash=f"hash_preview_{i}",
                created_at=base_time - timedelta(hours=i),
            )
            async_session.add(doc)
        
        await async_session.commit()

        # Note: This test assumes you have authentication set up in your test fixtures
        # You may need to adjust based on your test configuration
        # response = client.get(
        #     f"/api/v1/insights/preview/{test_search_space.id}?num_documents=5",
        #     headers={"Authorization": f"Bearer {test_user_token}"}
        # )
        # 
        # assert response.status_code == 200
        # data = response.json()
        # assert data["total_documents_found"] == 5
        # assert len(data["documents_preview"]) <= 10
        # assert "insights_preview" in data

    @pytest.mark.asyncio
    async def test_generate_insights_validation(
        self, async_session: AsyncSession, test_user, test_search_space
    ):
        """Test request validation for insights generation."""
        service = InsightsService(async_session, user_id=str(test_user.id))

        # Test invalid configuration (no document types)
        with pytest.raises(ValueError, match="At least one document type"):
            await service.generate_insights_and_plan(
                search_space_id=test_search_space.id,
                num_documents=50,
                include_connectors=False,
                include_files=False,
            )

    @pytest.mark.asyncio
    async def test_insights_with_no_documents(
        self, async_session: AsyncSession, test_user, test_search_space
    ):
        """Test insights generation when no documents exist."""
        service = InsightsService(async_session, user_id=str(test_user.id))

        # Should raise ValueError for empty search space
        with pytest.raises(ValueError, match="No documents found"):
            await service.generate_insights_and_plan(
                search_space_id=test_search_space.id,
                num_documents=50,
                include_connectors=True,
                include_files=True,
            )


class TestInsightSchemas:
    """Test insight schemas and validation."""

    def test_insight_request_validation(self):
        """Test InsightRequest schema validation."""
        # Valid request
        request = InsightRequest(
            search_space_id=1,
            num_documents=50,
            include_connectors=True,
            include_files=True,
        )
        assert request.num_documents == 50

        # Test default values
        request = InsightRequest(search_space_id=1)
        assert request.num_documents == 50  # default
        assert request.include_connectors is True  # default
        assert request.include_files is True  # default

        # Test min/max validation
        with pytest.raises(Exception):  # Pydantic validation error
            InsightRequest(search_space_id=1, num_documents=5)  # Below minimum (10)

        with pytest.raises(Exception):  # Pydantic validation error
            InsightRequest(search_space_id=1, num_documents=300)  # Above maximum (200)

    def test_action_item_priority_validation(self):
        """Test ActionItem priority validation."""
        from app.schemas.insights import ActionItem

        # Valid priorities
        for priority in ["HIGH", "MEDIUM", "LOW"]:
            item = ActionItem(
                title="Test",
                description="Test description",
                priority=priority,
                rationale="Test rationale",
            )
            assert item.priority == priority

        # Invalid priority should fail validation
        with pytest.raises(Exception):  # Pydantic validation error
            ActionItem(
                title="Test",
                description="Test description",
                priority="INVALID",
                rationale="Test rationale",
            )


# Integration test example (requires full setup)
@pytest.mark.integration
class TestInsightsIntegration:
    """Integration tests for the complete insights workflow."""

    @pytest.mark.asyncio
    async def test_full_insights_generation_workflow(
        self, async_session: AsyncSession, test_user, test_search_space
    ):
        """Test the complete workflow from documents to insights to plan."""
        # Setup: Create a realistic set of documents
        base_time = datetime.utcnow()
        
        # Simulate a week of activity
        doc_data = [
            ("Slack: Team standup", DocumentType.SLACK_CONNECTOR, "Daily standup discussion about project progress"),
            ("GitHub: Pull request review", DocumentType.GITHUB_CONNECTOR, "Code review for authentication feature"),
            ("Notion: Design specs", DocumentType.NOTION_CONNECTOR, "UI/UX design specifications for new dashboard"),
            ("File: Technical document", DocumentType.FILE, "Architecture documentation for microservices"),
            ("Gmail: Client feedback", DocumentType.GOOGLE_GMAIL_CONNECTOR, "Client requested additional features"),
        ]
        
        for i, (title, doc_type, content) in enumerate(doc_data):
            doc = Document(
                title=title,
                content=content,
                document_type=doc_type,
                search_space_id=test_search_space.id,
                content_hash=f"hash_integration_{i}",
                created_at=base_time - timedelta(days=i),
            )
            async_session.add(doc)
        
        await async_session.commit()

        # Execute: Generate insights
        service = InsightsService(async_session, user_id=str(test_user.id))
        
        # This will use fallback if LLM is not configured in test environment
        result = await service.generate_insights_and_plan(
            search_space_id=test_search_space.id,
            num_documents=10,
            include_connectors=True,
            include_files=True,
        )

        # Verify: Check all components are present
        assert result.insights.document_count == 5
        assert len(result.insights.key_topics) > 0
        assert result.plan.title
        assert len(result.plan.action_items) > 0
        assert result.metadata["search_space_id"] == test_search_space.id

        # Verify action items are well-formed
        for item in result.plan.action_items:
            assert item.priority in ["HIGH", "MEDIUM", "LOW"]
            assert len(item.title) > 0
            assert len(item.description) > 10  # Should have meaningful description
            assert len(item.rationale) > 0
