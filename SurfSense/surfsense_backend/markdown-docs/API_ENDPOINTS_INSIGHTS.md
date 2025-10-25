# API Endpoints Documentation

## Insights Service Endpoints

The Insights Service provides two main endpoints for analyzing user activity and generating actionable plans.

---

## 1. Generate Insights and Plan

Analyze recent document activity and generate an AI-powered strategic plan with actionable recommendations.

### Endpoint
```
POST /api/v1/insights/generate
```

### Authentication
Required. Include JWT token in Authorization header:
```
Authorization: Bearer {your_jwt_token}
```

### Request Body
```json
{
  "search_space_id": integer (required),
  "num_documents": integer (optional, default: 50, min: 10, max: 200),
  "include_connectors": boolean (optional, default: true),
  "include_files": boolean (optional, default: true)
}
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `search_space_id` | integer | Yes | - | ID of the search space to analyze |
| `num_documents` | integer | No | 50 | Number of recent documents to analyze (10-200) |
| `include_connectors` | boolean | No | true | Include documents from third-party connectors |
| `include_files` | boolean | No | true | Include user-uploaded files |

### Response

**Status Code:** 200 OK

```json
{
  "insights": {
    "summary": "string - Brief summary of recent activity",
    "key_topics": ["string"] - List of identified key topics,
    "connector_activity": {
      "DOCUMENT_TYPE": integer - Count by document type
    },
    "document_count": integer - Total documents analyzed,
    "time_period_summary": "string - Time period description"
  },
  "plan": {
    "title": "string - Plan title",
    "description": "string - Plan overview",
    "action_items": [
      {
        "title": "string - Action title",
        "description": "string - Detailed description",
        "priority": "HIGH|MEDIUM|LOW",
        "rationale": "string - Why this action is recommended"
      }
    ],
    "estimated_timeframe": "string - Estimated completion time"
  },
  "metadata": {
    "search_space_id": integer,
    "documents_analyzed": integer,
    "analysis_timestamp": "string (ISO 8601)",
    "included_types": {
      "connectors": boolean,
      "files": boolean
    }
  }
}
```

### Error Responses

**404 Not Found**
```json
{
  "detail": "No documents found in the specified search space"
}
```

**403 Forbidden**
```json
{
  "detail": "Not enough permissions"
}
```

**500 Internal Server Error**
```json
{
  "detail": "Failed to generate plan: {error_message}"
}
```

### Example Request

```bash
curl -X POST "https://api.surfsense.ai/api/v1/insights/generate" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "search_space_id": 1,
    "num_documents": 50,
    "include_connectors": true,
    "include_files": true
  }'
```

### Example Response

```json
{
  "insights": {
    "summary": "Analyzed 50 document(s) from the last 3 day(s). User uploaded 5 file(s). Retrieved 45 document(s) from connected third-party sources.",
    "key_topics": ["Project", "Design", "Meeting", "Development", "Review"],
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
    "description": "Based on your recent activity focusing on project development and team collaboration, here's a strategic plan to move forward.",
    "action_items": [
      {
        "title": "Review and consolidate design documents",
        "description": "Go through the 5 design-related files and create a unified design specification document",
        "priority": "HIGH",
        "rationale": "Multiple design discussions across Slack and uploaded design files indicate this is a key focus area"
      },
      {
        "title": "Follow up on GitHub pull requests",
        "description": "Review the 10 recent GitHub notifications and provide feedback on pending PRs",
        "priority": "HIGH",
        "rationale": "Active GitHub activity shows ongoing code review needs"
      },
      {
        "title": "Schedule team sync meeting",
        "description": "Based on Slack conversations, schedule a meeting to align on project timeline",
        "priority": "MEDIUM",
        "rationale": "Multiple team coordination messages suggest need for synchronization"
      }
    ],
    "estimated_timeframe": "1-2 weeks"
  },
  "metadata": {
    "search_space_id": 1,
    "documents_analyzed": 50,
    "analysis_timestamp": "2025-10-26T10:30:00Z",
    "included_types": {
      "connectors": true,
      "files": true
    }
  }
}
```

---

## 2. Preview Document Activity

Get a quick preview of recent documents without generating a full AI-powered plan. Useful for checking what data will be analyzed.

### Endpoint
```
GET /api/v1/insights/preview/{search_space_id}
```

### Authentication
Required. Include JWT token in Authorization header:
```
Authorization: Bearer {your_jwt_token}
```

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `search_space_id` | integer | Yes | ID of the search space to preview |

### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `num_documents` | integer | No | 30 | Number of recent documents to preview |

### Response

**Status Code:** 200 OK

```json
{
  "search_space_id": integer,
  "total_documents_found": integer,
  "documents_preview": [
    {
      "id": integer,
      "title": "string",
      "type": "string - Document type",
      "created_at": "string (ISO 8601)",
      "content_preview": "string - First 150 characters"
    }
  ],
  "insights_preview": {
    "summary": "string",
    "key_topics": ["string"],
    "document_type_breakdown": {
      "DOCUMENT_TYPE": integer
    }
  },
  "message": "string - Informational message"
}
```

### Error Responses

**404 Not Found**
```json
{
  "detail": "No documents found in the specified search space"
}
```

**403 Forbidden**
```json
{
  "detail": "Not enough permissions"
}
```

### Example Request

```bash
curl -X GET "https://api.surfsense.ai/api/v1/insights/preview/1?num_documents=30" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

### Example Response

```json
{
  "search_space_id": 1,
  "total_documents_found": 30,
  "documents_preview": [
    {
      "id": 123,
      "title": "Design Review Meeting Notes",
      "type": "NOTION_CONNECTOR",
      "created_at": "2025-10-26T09:00:00Z",
      "content_preview": "Meeting notes from design review session discussing new UI components and user feedback. Key decisions: move forward with mobile-first approach..."
    },
    {
      "id": 124,
      "title": "Feature Implementation Plan",
      "type": "FILE",
      "created_at": "2025-10-26T08:30:00Z",
      "content_preview": "Technical specification for implementing the new authentication system with OAuth2 and JWT tokens. Requirements include multi-factor authentication..."
    }
  ],
  "insights_preview": {
    "summary": "Analyzed 30 document(s) from the last 2 day(s). User uploaded 5 file(s). Retrieved 25 document(s) from connected third-party sources.",
    "key_topics": ["Design", "Meeting", "Review", "Components", "Authentication"],
    "document_type_breakdown": {
      "NOTION_CONNECTOR": 10,
      "SLACK_CONNECTOR": 15,
      "FILE": 5
    }
  },
  "message": "This is a preview. Use /insights/generate to create a full plan."
}
```

---

## Document Types

The service analyzes two categories of documents:

### Connector Documents (*_CONNECTOR types)
Documents automatically fetched from third-party integrations (information consumption):

- `SLACK_CONNECTOR` - Slack messages and threads
- `NOTION_CONNECTOR` - Notion pages and databases
- `GITHUB_CONNECTOR` - GitHub repositories and issues
- `GOOGLE_GMAIL_CONNECTOR` - Gmail emails
- `GOOGLE_CALENDAR_CONNECTOR` - Calendar events
- `JIRA_CONNECTOR` - Jira issues and comments
- `CONFLUENCE_CONNECTOR` - Confluence pages
- `CLICKUP_CONNECTOR` - ClickUp tasks
- `AIRTABLE_CONNECTOR` - Airtable records
- `DISCORD_CONNECTOR` - Discord messages
- `LINEAR_CONNECTOR` - Linear issues
- `LUMA_CONNECTOR` - Luma events
- `ELASTICSEARCH_CONNECTOR` - Elasticsearch documents

### File Documents
Documents uploaded by the user (work output):

- `FILE` - User-uploaded files (PDFs, docs, presentations, etc.)

---

## Rate Limits

- No specific rate limits on these endpoints
- LLM usage is subject to the user's configured LLM provider limits
- Recommended: Cache results for 1 hour if generating frequent insights

---

## Best Practices

1. **Use Preview First**: Call the preview endpoint before generating full insights to verify the data
2. **Optimal Document Count**: Use 50-100 documents for balanced analysis
3. **Include Both Types**: Enable both connectors and files for comprehensive insights
4. **Regular Usage**: Generate insights daily or weekly for best results
5. **Handle Errors**: Always check for 500 errors related to LLM configuration

---

## Common Use Cases

### 1. Daily Planning
```bash
# Generate plan at start of day based on yesterday's activity
curl -X POST ".../insights/generate" \
  -d '{"search_space_id": 1, "num_documents": 30}'
```

### 2. Weekly Review
```bash
# Analyze full week of activity
curl -X POST ".../insights/generate" \
  -d '{"search_space_id": 1, "num_documents": 100}'
```

### 3. Project Focus
```bash
# Focus on user's work (exclude connectors)
curl -X POST ".../insights/generate" \
  -d '{"search_space_id": 1, "include_connectors": false}'
```

### 4. Information Consumption Analysis
```bash
# See what information user is gathering
curl -X POST ".../insights/generate" \
  -d '{"search_space_id": 1, "include_files": false}'
```

---

## Integration Libraries

### Python
```python
from surfsense_sdk import InsightsClient

client = InsightsClient(api_key="your_token")
result = client.generate_insights(search_space_id=1, num_documents=50)
```

### JavaScript/TypeScript
```typescript
import { SurfSenseClient } from 'surfsense-js';

const client = new SurfSenseClient({ apiKey: 'your_token' });
const result = await client.insights.generate({
  searchSpaceId: 1,
  numDocuments: 50
});
```

---

## Support

For questions or issues:
- Check the [full documentation](INSIGHTS_SERVICE_README.md)
- Review the [implementation summary](IMPLEMENTATION_SUMMARY.md)
- Run the [demo script](demo_insights.py) for interactive examples

---

## Version

API Version: 1.0  
Last Updated: 2025-10-26
