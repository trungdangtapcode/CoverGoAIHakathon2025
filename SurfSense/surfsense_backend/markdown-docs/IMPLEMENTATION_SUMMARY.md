# User Activity Insights & Planning Service - Implementation Summary

## What Was Built

A comprehensive AI-powered service that analyzes user document activity in SurfSense and generates actionable planning recommendations. This service helps users understand their recent work patterns and provides strategic guidance on what to do next.

## Core Concept

The service analyzes two types of documents:

1. **Connector Documents** (`*_CONNECTOR` types): Information the user is **consuming**
   - Slack messages, Gmail emails, GitHub repos, Notion pages, Calendar events, etc.
   - Shows what information the user is gathering and staying updated on

2. **File Documents** (`FILE` type): Content the user is **creating**
   - Uploaded PDFs, documents, presentations, code files
   - Shows what the user is actively working on

By analyzing both types, the service understands:
- What information the user is consuming (from connectors)
- What work the user is producing (from files)
- How to bridge the gap with actionable planning

## Files Created

### 1. Service Layer
**`app/services/insights_service.py`** (442 lines)
- Core business logic for insights generation
- Document fetching and filtering
- Activity analysis and topic extraction
- LLM-powered plan generation
- Fallback plan generation when LLM fails

Key methods:
- `generate_insights_and_plan()`: Main entry point
- `_fetch_recent_documents()`: Query recent documents with filters
- `_generate_activity_insights()`: Analyze document patterns
- `_generate_plan_with_llm()`: Use AI to create strategic plans
- `_generate_fallback_plan()`: Provide plans without LLM

### 2. API Routes
**`app/routes/insights_routes.py`** (161 lines)
- RESTful API endpoints
- Authentication and authorization
- Error handling
- Two main endpoints:
  - `POST /api/v1/insights/generate`: Full insights + plan
  - `GET /api/v1/insights/preview/{id}`: Quick preview without LLM

### 3. Data Schemas
**`app/schemas/insights.py`** (71 lines)
- Pydantic models for request/response validation
- Type safety and auto-documentation
- Models:
  - `InsightRequest`: API request parameters
  - `ActivityInsight`: Activity analysis results
  - `ActionItem`: Individual task recommendation
  - `Plan`: Complete strategic plan
  - `InsightResponse`: Full API response

### 4. Documentation
**`INSIGHTS_SERVICE_README.md`** (693 lines)
- Complete user guide
- API documentation with examples
- Architecture diagrams
- Integration examples (Python, TypeScript)
- Troubleshooting guide
- Performance considerations

### 5. Tests
**`tests/test_insights.py`** (355 lines)
- Unit tests for service methods
- Integration tests for workflows
- Schema validation tests
- Test coverage for:
  - Document fetching with filters
  - Insight generation
  - Fallback plans
  - API endpoints
  - Edge cases

### 6. Demo Script
**`demo_insights.py`** (390 lines)
- Interactive CLI demonstration
- Beautiful formatted output with emojis
- Two modes: preview and generate
- Usage examples:
  ```bash
  # Preview activity
  python demo_insights.py preview --search-space-id 1 --token TOKEN
  
  # Generate full plan
  python demo_insights.py generate --search-space-id 1 --token TOKEN
  ```

### 7. Integration
- Updated `app/app.py` to register routes
- Updated `app/schemas/__init__.py` to export schemas

## Key Features

### 1. Smart Document Analysis
- Fetches k-latest documents (configurable, default 50)
- Filters by document type (connectors, files, or both)
- Orders by creation time (most recent first)
- Extracts key topics from document titles
- Counts activity by connector type

### 2. AI-Powered Planning
- Uses user's configured strategic LLM
- Generates context-aware action items
- Prioritizes tasks (HIGH/MEDIUM/LOW)
- Provides rationale for each recommendation
- Estimates timeframes

### 3. Robust Error Handling
- Fallback plans when LLM fails
- Graceful handling of no documents
- Validation of all inputs
- Detailed error messages

### 4. Flexible Configuration
- Adjustable document count (10-200)
- Toggle connector documents
- Toggle file documents
- Per-search-space analysis

## API Usage Examples

### Preview Activity
```bash
curl -X GET "http://localhost:8002/api/v1/insights/preview/1?num_documents=30" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Generate Full Insights
```bash
curl -X POST "http://localhost:8002/api/v1/insights/generate" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "search_space_id": 1,
    "num_documents": 50,
    "include_connectors": true,
    "include_files": true
  }'
```

## Example Response

```json
{
  "insights": {
    "summary": "Analyzed 50 document(s) from the last 3 day(s). User uploaded 5 file(s). Retrieved 45 document(s) from connected third-party sources.",
    "key_topics": ["Project", "Design", "Meeting", "Development"],
    "connector_activity": {
      "SLACK_CONNECTOR": 20,
      "NOTION_CONNECTOR": 15,
      "GITHUB_CONNECTOR": 10,
      "FILE": 5
    },
    "document_count": 50,
    "time_period_summary": "last 3 day(s)"
  },
  "plan": {
    "title": "Weekly Productivity Plan",
    "description": "Strategic plan based on recent activity",
    "action_items": [
      {
        "title": "Review and consolidate design documents",
        "description": "Go through the 5 design-related files and create a unified spec",
        "priority": "HIGH",
        "rationale": "Multiple design discussions across Slack and files"
      },
      {
        "title": "Follow up on GitHub pull requests",
        "description": "Review the 10 recent GitHub notifications",
        "priority": "HIGH",
        "rationale": "Active GitHub activity shows ongoing code review needs"
      }
    ],
    "estimated_timeframe": "1-2 weeks"
  },
  "metadata": {
    "search_space_id": 1,
    "documents_analyzed": 50,
    "analysis_timestamp": "2025-10-26T10:30:00Z"
  }
}
```

## Technical Highlights

### Database Queries
- Efficient JOIN with SearchSpace for user verification
- Filtering by document type using Enum
- ORDER BY created_at DESC for recency
- LIMIT for pagination
- Uses async/await for non-blocking I/O

### LLM Integration
- Uses user's configured strategic LLM
- Structured JSON prompts
- Response parsing with fallback
- Context-aware prompt construction
- Handles LLM failures gracefully

### Type Safety
- Pydantic models for all data
- SQLAlchemy ORM for database
- Type hints throughout
- Validation at every layer

## How It Works - Flow Diagram

```
User Request
    │
    ├─→ Authentication (JWT)
    │
    ├─→ Check Search Space Ownership
    │
    ├─→ Fetch Recent Documents
    │     ├─ Filter by type (connectors/files)
    │     ├─ Order by created_at DESC
    │     └─ Limit to num_documents
    │
    ├─→ Generate Activity Insights
    │     ├─ Count by document type
    │     ├─ Extract key topics
    │     ├─ Analyze time period
    │     └─ Create summary
    │
    ├─→ Generate Plan with LLM
    │     ├─ Prepare document context (30 docs)
    │     ├─ Create strategic prompt
    │     ├─ Call user's strategic LLM
    │     ├─ Parse JSON response
    │     └─ Create action items
    │
    └─→ Return InsightResponse
          ├─ insights (activity analysis)
          ├─ plan (action items)
          └─ metadata (analysis info)
```

## Integration Points

### Database
- Queries `documents` table
- Joins with `searchspaces` for user verification
- Filters by `document_type` enum
- Uses `created_at` for sorting

### LLM Service
- Uses existing `get_user_strategic_llm()` function
- Leverages user's configured LLM preferences
- Respects search space settings

### Authentication
- Uses existing `current_active_user` dependency
- Integrates with FastAPI Users
- JWT token validation

### Routes
- Registered in main `app.py`
- Follows existing route patterns
- Uses standard error handling

## Testing

Comprehensive test suite covers:
- ✅ Document fetching with various filters
- ✅ Activity insight generation
- ✅ Fallback plan generation
- ✅ Schema validation
- ✅ Edge cases (no documents, invalid params)
- ✅ Integration workflow

Run tests:
```bash
pytest tests/test_insights.py -v
```

## Performance Considerations

### Optimizations
- Limits document fetching to requested amount
- Only processes top 30 documents for LLM context
- Async/await for non-blocking operations
- Efficient database queries with proper indexing

### Scalability
- Works with large document sets
- Configurable analysis depth
- Preview mode for quick checks
- Fallback when LLM is slow/unavailable

## Use Cases

1. **Daily Planning**: Generate tasks at start of day
2. **Weekly Review**: Understand what happened this week
3. **Project Context**: See what user is focused on
4. **Team Insights**: Understand team communication patterns
5. **Personal Productivity**: Get AI recommendations based on activity

## Future Enhancements

Potential improvements:
- Trend analysis (compare to previous periods)
- Team-level insights (multiple users)
- Custom planning templates
- Scheduled generation (daily/weekly)
- Export to various formats
- ML-based priority prediction
- Document clustering
- Sentiment analysis

## Dependencies

No new dependencies! Uses existing packages:
- FastAPI (web framework)
- SQLAlchemy (ORM)
- Pydantic (validation)
- LiteLLM (LLM integration via existing service)

## Configuration

Users need:
1. Strategic LLM configured in search space
2. At least one search space with documents
3. JWT token for authentication

No additional environment variables or setup required!

## Conclusion

This service provides a powerful way for users to:
- Understand their recent activity patterns
- Get AI-powered recommendations
- Bridge information consumption with action
- Stay productive with strategic planning

It's fully integrated with the existing SurfSense architecture, follows established patterns, and requires no additional infrastructure.

## Quick Start

1. Start SurfSense backend
2. Ensure you have documents in your search space
3. Configure a strategic LLM
4. Call the API:

```bash
curl -X POST "http://localhost:8002/api/v1/insights/generate" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"search_space_id": 1, "num_documents": 50}'
```

Or use the demo script:
```bash
python demo_insights.py generate --search-space-id 1 --token YOUR_TOKEN
```

Done! 🎉
