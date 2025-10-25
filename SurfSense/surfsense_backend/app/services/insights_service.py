"""Service for generating user insights and planning based on document activity."""

import json
import logging
from collections import Counter
from datetime import datetime, timedelta

from langchain.schema import SystemMessage, HumanMessage
from sqlalchemy import and_, desc, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db import Document, DocumentType, SearchSpace
from app.schemas.insights import (
    ActionItem,
    ActivityInsight,
    InsightResponse,
    Plan,
)
from app.services.llm_service import get_user_strategic_llm

logger = logging.getLogger(__name__)


class InsightsService:
    """Service for generating insights and planning from user activity."""

    def __init__(self, session: AsyncSession, user_id: str):
        """
        Initialize the insights service.

        Args:
            session: Database session
            user_id: User ID for which to generate insights
        """
        self.session = session
        self.user_id = user_id

    async def generate_insights_and_plan(
        self,
        search_space_id: int,
        num_documents: int = 50,
        include_connectors: bool = True,
        include_files: bool = True,
    ) -> InsightResponse:
        """
        Generate insights and planning based on recent user activity.

        Args:
            search_space_id: Search space ID to analyze
            num_documents: Number of recent documents to analyze
            include_connectors: Include documents from third-party connectors
            include_files: Include user-uploaded files

        Returns:
            InsightResponse containing insights and planning

        Raises:
            ValueError: If invalid parameters are provided
            RuntimeError: If LLM is not configured
        """
        if not include_connectors and not include_files:
            raise ValueError("At least one document type must be included")

        # Fetch recent documents
        documents = await self._fetch_recent_documents(
            search_space_id, num_documents, include_connectors, include_files
        )

        if not documents:
            raise ValueError("No documents found in the specified search space")

        # Generate activity insights
        insights = await self._generate_activity_insights(documents)

        # Generate plan using LLM
        plan = await self._generate_plan_with_llm(
            search_space_id, documents, insights
        )

        # Compile metadata
        metadata = {
            "search_space_id": search_space_id,
            "documents_analyzed": len(documents),
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "included_types": {
                "connectors": include_connectors,
                "files": include_files,
            },
        }

        return InsightResponse(insights=insights, plan=plan, metadata=metadata)

    async def _fetch_recent_documents(
        self,
        search_space_id: int,
        num_documents: int,
        include_connectors: bool,
        include_files: bool,
    ) -> list[Document]:
        """
        Fetch recent documents from the specified search space.

        Args:
            search_space_id: Search space ID
            num_documents: Number of documents to fetch
            include_connectors: Include connector documents
            include_files: Include file documents

        Returns:
            List of Document objects
        """
        # Build the filter conditions
        type_filters = []

        if include_connectors:
            # All connector types end with "_CONNECTOR"
            connector_types = [
                doc_type
                for doc_type in DocumentType
                if doc_type.value.endswith("_CONNECTOR")
            ]
            type_filters.extend(connector_types)

        if include_files:
            type_filters.append(DocumentType.FILE)

        # Query recent documents
        query = (
            select(Document)
            .join(SearchSpace)
            .where(
                and_(
                    SearchSpace.user_id == self.user_id,
                    Document.search_space_id == search_space_id,
                    Document.document_type.in_(type_filters),
                )
            )
            .order_by(desc(Document.created_at))
            .limit(num_documents)
        )

        result = await self.session.execute(query)
        documents = result.scalars().all()

        return list(documents)

    async def _generate_activity_insights(
        self, documents: list[Document]
    ) -> ActivityInsight:
        """
        Generate activity insights from documents.

        Args:
            documents: List of documents to analyze

        Returns:
            ActivityInsight object
        """
        if not documents:
            return ActivityInsight(
                summary="No recent activity found.",
                key_topics=[],
                connector_activity={},
                document_count=0,
                time_period_summary="No documents to analyze",
            )

        # Count documents by type
        type_counter = Counter(doc.document_type.value for doc in documents)

        # Analyze time range
        oldest_doc = min(documents, key=lambda d: d.created_at)
        newest_doc = max(documents, key=lambda d: d.created_at)
        time_delta = newest_doc.created_at - oldest_doc.created_at

        # Format time period
        if time_delta.days > 0:
            time_period = f"last {time_delta.days} day(s)"
        elif time_delta.seconds > 3600:
            time_period = f"last {time_delta.seconds // 3600} hour(s)"
        else:
            time_period = "recent activity"

        # Extract key topics from titles (simple keyword extraction)
        all_titles = " ".join([doc.title for doc in documents])
        # This is a simple approach; could be enhanced with NLP
        words = all_titles.lower().split()
        # Filter out common words and get most frequent
        common_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "as",
            "is",
            "was",
            "are",
            "be",
            "been",
        }
        meaningful_words = [w for w in words if w not in common_words and len(w) > 3]
        word_counter = Counter(meaningful_words)
        key_topics = [word.title() for word, _ in word_counter.most_common(10)]

        # Generate VERY detailed summary with lots of information
        summary_parts = []
        
        # Main activity overview
        summary_parts.append(
            f"You had {len(documents)} updates from the {time_period}."
        )
        
        # Break down by connector type with detailed counts
        connector_breakdown = []
        for doc_type, count in sorted(type_counter.items(), key=lambda x: x[1], reverse=True):
            if "_CONNECTOR" in doc_type:
                clean_name = doc_type.replace("_CONNECTOR", "").replace("_", " ").title()
                connector_breakdown.append(f"{count} from {clean_name}")
        
        if connector_breakdown:
            if len(connector_breakdown) == 1:
                summary_parts.append(connector_breakdown[0] + ".")
            elif len(connector_breakdown) == 2:
                summary_parts.append(f"{connector_breakdown[0]} and {connector_breakdown[1]}.")
            else:
                summary_parts.append(
                    f"{', '.join(connector_breakdown[:-1])}, and {connector_breakdown[-1]}."
                )
        
        if DocumentType.FILE.value in type_counter:
            summary_parts.append(
                f"You also uploaded {type_counter[DocumentType.FILE.value]} file(s)."
            )
        
        # Add MORE document highlights - show up to 10 recent titles
        recent_highlights = [doc.title for doc in documents[:10] if doc.title and doc.title.strip()]
        if recent_highlights:
            if len(recent_highlights) >= 5:
                summary_parts.append(
                    f"Recent items include: \"{recent_highlights[0]}\", \"{recent_highlights[1]}\", "
                    f"\"{recent_highlights[2]}\", \"{recent_highlights[3]}\", and \"{recent_highlights[4]}\"."
                )
                if len(recent_highlights) > 5:
                    more_titles = recent_highlights[5:10]
                    summary_parts.append(
                        f"Also: {', '.join(['\"' + t + '\"' for t in more_titles])}."
                    )
            elif len(recent_highlights) >= 3:
                summary_parts.append(
                    f"Recent items include: \"{recent_highlights[0]}\", \"{recent_highlights[1]}\", "
                    f"and \"{recent_highlights[2]}\"."
                )
        
        # Add time context details
        if newest_doc and oldest_doc:
            summary_parts.append(
                f"Most recent update was \"{newest_doc.title}\" on {newest_doc.created_at.strftime('%B %d at %I:%M %p')}."
            )
        
        # Add topic richness
        if key_topics:
            topics_list = ", ".join(key_topics[:8])
            summary_parts.append(
                f"Main topics across these updates: {topics_list}."
            )

        summary = " ".join(summary_parts)

        return ActivityInsight(
            summary=summary,
            key_topics=key_topics,
            connector_activity=dict(type_counter),
            document_count=len(documents),
            time_period_summary=time_period,
        )

    async def _generate_plan_with_llm(
        self, search_space_id: int, documents: list[Document], insights: ActivityInsight
    ) -> Plan:
        """
        Generate a plan using LLM based on document analysis and insights.

        Args:
            search_space_id: Search space ID
            documents: List of documents analyzed
            insights: Generated activity insights

        Returns:
            Plan object with action items

        Raises:
            RuntimeError: If LLM is not configured
        """
        # Get the user's strategic LLM
        llm = await get_user_strategic_llm(
            self.session, self.user_id, search_space_id
        )

        if not llm:
            raise RuntimeError(
                f"No strategic LLM configured for user {self.user_id} "
                f"in search space {search_space_id}"
            )

        # Prepare document summaries for LLM context
        doc_summaries = []
        for idx, doc in enumerate(documents[:30], 1):  # Limit to 30 for context size
            # Extract metadata insights
            metadata_str = ""
            if doc.document_metadata:
                if isinstance(doc.document_metadata, dict):
                    metadata_items = [
                        f"{k}: {v}"
                        for k, v in list(doc.document_metadata.items())[:3]
                    ]
                    metadata_str = " | ".join(metadata_items)

            # Truncate content preview
            content_preview = (
                doc.content[:200] + "..." if len(doc.content) > 200 else doc.content
            )

            doc_summaries.append(
                f"[{idx}] {doc.document_type.value} - {doc.title}\n"
                f"    Created: {doc.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                f"    Metadata: {metadata_str}\n"
                f"    Preview: {content_preview}\n"
            )

        documents_context = "\n".join(doc_summaries)

        # Create prompt for LLM - generate detailed actionable plans
        system_message = SystemMessage(
            content=f"""You are an AI assistant specializing in productivity planning and personal insights.
Your task is to analyze a user's recent document activity and generate actionable planning recommendations.

Today's date: {datetime.utcnow().strftime("%Y-%m-%d")}

The user has been working with various documents from:
- Third-party connectors (e.g., Slack, Notion, GitHub, Gmail, Calendar) - these show what information the user is consuming
- Uploaded files - these show what content the user is personally working on

You will be provided with:
1. Activity insights (summary, key topics, document types)
2. Recent document list with titles, types, and previews

Your goal is to:
1. Understand the user's current focus areas and interests
2. Identify patterns in their information consumption and work
3. Generate a strategic plan with 3-5 actionable items

The plan should be:
- Specific and actionable (not generic advice)
- Based on actual document content and patterns
- Prioritized by importance
- Realistic and achievable
- Detailed enough to be helpful

You MUST respond with a valid JSON object in this EXACT format:
{{
    "title": "Plan title based on user's focus",
    "description": "2-3 sentence overview of the plan",
    "action_items": [
        {{
            "title": "Action item title",
            "description": "Detailed description of what to do and how",
            "priority": "HIGH|MEDIUM|LOW",
            "rationale": "Why this action matters based on user's activity"
        }}
    ],
    "estimated_timeframe": "e.g., '1-2 weeks', 'Next 3 days', 'This week'"
}}

Provide ONLY the JSON object, no additional text or explanation."""
        )

        human_message = HumanMessage(
            content=f"""## User Activity Insights:
{insights.summary}

**Key Topics Detected:** {', '.join(insights.key_topics[:10]) if insights.key_topics else 'None'}

**Document Type Breakdown:**
{json.dumps(insights.connector_activity, indent=2)}

## Recent Documents ({len(documents)} total, showing top 30):

{documents_context}

Based on this activity, generate a strategic plan with actionable items that will help the user make progress on their work and leverage the information they've been gathering."""
        )

        try:
            # Get response from LLM
            response = await llm.agenerate(messages=[[system_message, human_message]])
            response_text = response.generations[0][0].text.strip()

            # Parse JSON response
            # Try to extract JSON if it's wrapped in markdown code blocks
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            plan_data = json.loads(response_text)

            # Validate and create Plan object
            action_items = [
                ActionItem(**item) for item in plan_data.get("action_items", [])
            ]

            plan = Plan(
                title=plan_data.get("title", "Productivity Plan"),
                description=plan_data.get(
                    "description", "A plan based on your recent activity"
                ),
                action_items=action_items,
                estimated_timeframe=plan_data.get("estimated_timeframe", "1-2 weeks"),
            )

            return plan

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Response text: {response_text}")
            # Return a fallback plan
            return self._generate_fallback_plan(insights)
        except Exception as e:
            logger.error(f"Error generating plan with LLM: {e}")
            return self._generate_fallback_plan(insights)

    def _generate_fallback_plan(self, insights: ActivityInsight) -> Plan:
        """
        Generate a simple fallback plan when LLM fails.

        Args:
            insights: Activity insights

        Returns:
            Basic Plan object
        """
        action_items = []

        # Suggest reviewing recent files
        if insights.connector_activity.get(DocumentType.FILE.value, 0) > 0:
            action_items.append(
                ActionItem(
                    title="Review and organize uploaded files",
                    description="Go through recently uploaded files and organize them by project or topic",
                    priority="MEDIUM",
                    rationale=f"You have uploaded {insights.connector_activity[DocumentType.FILE.value]} files recently",
                )
            )

        # Suggest following up on connector data
        connector_count = sum(
            count
            for doc_type, count in insights.connector_activity.items()
            if "_CONNECTOR" in doc_type
        )
        if connector_count > 0:
            action_items.append(
                ActionItem(
                    title="Follow up on recent communications and updates",
                    description="Review recent messages and updates from connected platforms",
                    priority="HIGH",
                    rationale=f"You have {connector_count} items from connected sources",
                )
            )

        # Suggest focusing on key topics
        if insights.key_topics:
            action_items.append(
                ActionItem(
                    title=f"Deep dive into {insights.key_topics[0]}",
                    description=f"Focus on {insights.key_topics[0]} which appears frequently in your recent activity",
                    priority="MEDIUM",
                    rationale="This topic appears prominently in your recent documents",
                )
            )

        return Plan(
            title="Activity-Based Action Plan",
            description=f"Based on your activity over the {insights.time_period_summary}, here are recommended actions.",
            action_items=action_items if action_items else [
                ActionItem(
                    title="Continue current work",
                    description="Keep up with your current document workflow",
                    priority="MEDIUM",
                    rationale="Your activity shows consistent engagement",
                )
            ],
            estimated_timeframe="Next few days",
        )
