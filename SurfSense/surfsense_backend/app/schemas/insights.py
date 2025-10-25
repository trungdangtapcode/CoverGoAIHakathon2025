"""Schemas for insights and planning endpoints."""

from pydantic import BaseModel, Field


class InsightRequest(BaseModel):
    """Request schema for generating user insights and planning."""

    search_space_id: int = Field(..., description="Search space ID to analyze")
    num_documents: int = Field(
        default=50,
        ge=10,
        le=200,
        description="Number of recent documents to analyze (10-200)",
    )
    include_connectors: bool = Field(
        default=True,
        description="Include documents from third-party connectors (*_CONNECTOR types)",
    )
    include_files: bool = Field(
        default=True, description="Include user-uploaded files (FILE type)"
    )


class ActivityInsight(BaseModel):
    """Insight about user activity based on document analysis."""

    summary: str = Field(..., description="Summary of user's recent activity")
    key_topics: list[str] = Field(
        default_factory=list, description="Key topics identified from recent documents"
    )
    connector_activity: dict[str, int] = Field(
        default_factory=dict,
        description="Activity breakdown by connector type (e.g., SLACK: 10, NOTION: 5)",
    )
    document_count: int = Field(..., description="Total number of documents analyzed")
    time_period_summary: str = Field(
        ..., description="Summary of the time period covered by the documents"
    )


class ActionItem(BaseModel):
    """A suggested action item based on user activity."""

    title: str = Field(..., description="Brief title of the action item")
    description: str = Field(..., description="Detailed description of the action")
    priority: str = Field(
        ..., description="Priority level: HIGH, MEDIUM, or LOW", pattern="^(HIGH|MEDIUM|LOW)$"
    )
    rationale: str = Field(
        ..., description="Why this action is recommended based on user's activity"
    )


class Plan(BaseModel):
    """A plan generated based on user insights."""

    title: str = Field(..., description="Title of the plan")
    description: str = Field(..., description="Overall description of the plan")
    action_items: list[ActionItem] = Field(
        default_factory=list, description="List of recommended action items"
    )
    estimated_timeframe: str = Field(
        ..., description="Estimated timeframe to complete the plan"
    )


class InsightResponse(BaseModel):
    """Response schema containing insights and planning."""

    insights: ActivityInsight = Field(..., description="User activity insights")
    plan: Plan = Field(..., description="Recommended plan based on insights")
    metadata: dict = Field(
        default_factory=dict, description="Additional metadata about the analysis"
    )
