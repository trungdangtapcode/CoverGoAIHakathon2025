# User Activity Insights and Planning Service

## Overview

This service provides intelligent insights and actionable planning based on a user's recent document activity in SurfSense. It analyzes documents from both third-party connectors (Slack, Notion, GitHub, Gmail, etc.) and user-uploaded files to understand the user's current focus areas and generate strategic action plans.

## Key Features

- **Activity Analysis**: Automatically analyzes recent documents to identify patterns and key topics
- **Smart Planning**: Uses AI (LLM) to generate actionable plans with prioritized tasks
- **Flexible Scope**: Configure the number of documents to analyze and which types to include
- **Preview Mode**: Check what documents will be analyzed before generating a full plan

## API Endpoints

### 1. Generate Insights and Plan

**POST** `/api/v1/insights/generate`

Analyzes recent documents and generates a comprehensive plan with actionable items.

#### Request Body

```json
{
  "search_space_id": 1,
  "num_documents": 50,
  "include_connectors": true,
  "include_files": true
}
```

**Parameters:**
- `search_space_id` (required): ID of the search space to analyze
- `num_documents` (optional): Number of recent documents to analyze (10-200, default: 50)
- `include_connectors` (optional): Include documents from third-party connectors (default: true)
- `include_files` (optional): Include user-uploaded files (default: true)

#### Response

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
    "title": "Week Productivity Plan",
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

### 2. Preview Document Activity

**GET** `/api/v1/insights/preview/{search_space_id}?num_documents=30`

Get a quick preview of recent documents without generating a full plan. Useful for checking what data will be analyzed.

#### Response

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
      "content_preview": "Meeting notes from design review session discussing new UI components..."
    }
  ],
  "insights_preview": {
    "summary": "Analyzed 30 document(s) from the last 2 day(s).",
    "key_topics": ["Design", "Meeting", "Review", "Components"],
    "document_type_breakdown": {
      "NOTION_CONNECTOR": 10,
      "SLACK_CONNECTOR": 15,
      "FILE": 5
    }
  },
  "message": "This is a preview. Use /insights/generate to create a full plan."
}
```

## Use Cases

### 1. Daily/Weekly Planning

Generate a plan at the start of your day or week based on recent activity:

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

### 2. Project Context Understanding

Focus on recent uploaded files to understand what the user is actively working on:

```bash
curl -X POST "http://localhost:8002/api/v1/insights/generate" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "search_space_id": 1,
    "num_documents": 30,
    "include_connectors": false,
    "include_files": true
  }'
```

### 3. Information Consumption Analysis

Focus on connector documents to see what information the user is gathering:

```bash
curl -X POST "http://localhost:8002/api/v1/insights/generate" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "search_space_id": 1,
    "num_documents": 100,
    "include_connectors": true,
    "include_files": false
  }'
```

## How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Request                          │
│             POST /api/v1/insights/generate              │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              InsightsService                             │
│  ┌────────────────────────────────────────────────┐    │
│  │  1. Fetch Recent Documents                      │    │
│  │     - Query database for latest docs           │    │
│  │     - Filter by type (connectors/files)        │    │
│  │     - Order by created_at DESC                 │    │
│  └────────────────────────────────────────────────┘    │
│                     ▼                                    │
│  ┌────────────────────────────────────────────────┐    │
│  │  2. Generate Activity Insights                  │    │
│  │     - Count documents by type                  │    │
│  │     - Extract key topics from titles           │    │
│  │     - Analyze time period                      │    │
│  │     - Create activity summary                  │    │
│  └────────────────────────────────────────────────┘    │
│                     ▼                                    │
│  ┌────────────────────────────────────────────────┐    │
│  │  3. Generate Plan with LLM                      │    │
│  │     - Prepare document context                 │    │
│  │     - Create strategic prompt                  │    │
│  │     - Call user's strategic LLM                │    │
│  │     - Parse JSON response                      │    │
│  │     - Generate action items with priorities    │    │
│  └────────────────────────────────────────────────┘    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  JSON Response                           │
│         insights + plan + metadata                       │
└─────────────────────────────────────────────────────────┘
```

### Document Type Analysis

The service intelligently categorizes documents:

#### Connector Documents (*_CONNECTOR types)
These documents represent **information consumption** - what the user is reading, receiving, or gathering:

- `SLACK_CONNECTOR`: Team communications and discussions
- `NOTION_CONNECTOR`: Knowledge base pages and documentation
- `GITHUB_CONNECTOR`: Code repositories and development activity
- `GMAIL_CONNECTOR`: Email communications
- `GOOGLE_CALENDAR_CONNECTOR`: Meetings and events
- `JIRA_CONNECTOR`: Project management and issues
- `CONFLUENCE_CONNECTOR`: Team documentation
- `CLICKUP_CONNECTOR`: Tasks and project tracking
- `AIRTABLE_CONNECTOR`: Database records
- `DISCORD_CONNECTOR`: Community discussions
- `LINEAR_CONNECTOR`: Issue tracking
- `LUMA_CONNECTOR`: Events

#### File Documents (FILE type)
These documents represent **work output** - what the user is creating or actively working on:

- Uploaded PDF documents
- Word documents
- Presentations
- Spreadsheets
- Code files
- Design files

### LLM-Powered Planning

The service uses the user's configured **strategic LLM** to:

1. **Analyze Patterns**: Identify common themes and focus areas across documents
2. **Prioritize Actions**: Determine what tasks are most important based on activity
3. **Generate Context-Aware Plans**: Create specific, actionable items tied to actual document content
4. **Estimate Timeframes**: Suggest realistic timelines for plan completion

### Fallback Mechanism

If the LLM fails or is not configured, the service provides a rule-based fallback plan:

- Suggests reviewing uploaded files if present
- Recommends following up on connector data
- Proposes deep-diving into key topics
- Ensures users always get actionable output

## Configuration

### Prerequisites

1. **LLM Configuration**: Users must have a strategic LLM configured in their search space
   - Navigate to LLM settings in the search space
   - Configure at least one LLM with the "strategic" role
   - The service uses this LLM to generate intelligent plans

2. **Search Space Setup**: Users need at least one search space with documents
   - Documents can be from connectors or uploaded files
   - More documents = better insights (recommended: 30-100 documents)

### Optimal Settings

- **num_documents**: 50-100 for balanced analysis
- **Include both types**: Set both `include_connectors` and `include_files` to `true` for comprehensive insights
- **Regular usage**: Generate insights daily or weekly for best results

## Error Handling

### Common Errors

1. **404 - No documents found**
   ```json
   {
     "detail": "No documents found in the specified search space"
   }
   ```
   **Solution**: Ensure the search space has documents, or adjust filters

2. **500 - LLM not configured**
   ```json
   {
     "detail": "Failed to generate plan: No strategic LLM configured for user..."
   }
   ```
   **Solution**: Configure a strategic LLM in search space settings

3. **403 - Unauthorized**
   ```json
   {
     "detail": "Not enough permissions"
   }
   ```
   **Solution**: Verify the user owns the search space

## Integration Examples

### Python Client

```python
import requests

class SurfSenseInsightsClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def generate_insights(
        self,
        search_space_id: int,
        num_documents: int = 50,
        include_connectors: bool = True,
        include_files: bool = True
    ):
        """Generate insights and plan."""
        response = requests.post(
            f"{self.base_url}/api/v1/insights/generate",
            headers=self.headers,
            json={
                "search_space_id": search_space_id,
                "num_documents": num_documents,
                "include_connectors": include_connectors,
                "include_files": include_files
            }
        )
        response.raise_for_status()
        return response.json()
    
    def preview_activity(self, search_space_id: int, num_documents: int = 30):
        """Preview recent activity."""
        response = requests.get(
            f"{self.base_url}/api/v1/insights/preview/{search_space_id}",
            headers=self.headers,
            params={"num_documents": num_documents}
        )
        response.raise_for_status()
        return response.json()

# Usage
client = SurfSenseInsightsClient("http://localhost:8002", "your_jwt_token")

# Generate full insights
result = client.generate_insights(search_space_id=1, num_documents=50)
print(f"Plan: {result['plan']['title']}")
for item in result['plan']['action_items']:
    print(f"- [{item['priority']}] {item['title']}")

# Preview activity
preview = client.preview_activity(search_space_id=1)
print(f"Found {preview['total_documents_found']} documents")
```

### TypeScript/JavaScript Client

```typescript
interface InsightRequest {
  search_space_id: number;
  num_documents?: number;
  include_connectors?: boolean;
  include_files?: boolean;
}

class SurfSenseInsightsAPI {
  constructor(private baseUrl: string, private token: string) {}
  
  async generateInsights(request: InsightRequest) {
    const response = await fetch(`${this.baseUrl}/api/v1/insights/generate`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(request)
    });
    
    if (!response.ok) throw new Error('Failed to generate insights');
    return response.json();
  }
  
  async previewActivity(searchSpaceId: number, numDocuments: number = 30) {
    const response = await fetch(
      `${this.baseUrl}/api/v1/insights/preview/${searchSpaceId}?num_documents=${numDocuments}`,
      {
        headers: { 'Authorization': `Bearer ${this.token}` }
      }
    );
    
    if (!response.ok) throw new Error('Failed to preview activity');
    return response.json();
  }
}

// Usage
const api = new SurfSenseInsightsAPI('http://localhost:8002', 'your_jwt_token');

const result = await api.generateInsights({
  search_space_id: 1,
  num_documents: 50,
  include_connectors: true,
  include_files: true
});

console.log('Plan:', result.plan.title);
result.plan.action_items.forEach(item => {
  console.log(`[${item.priority}] ${item.title}`);
});
```

## Performance Considerations

- **Document Limit**: Higher `num_documents` values increase analysis time and LLM token usage
- **LLM Latency**: Plan generation depends on LLM response time (typically 3-10 seconds)
- **Caching**: Consider caching results for a short period (e.g., 1 hour) if generating frequent insights
- **Preview First**: Use the preview endpoint to verify data before generating expensive LLM-based plans

## Future Enhancements

Potential improvements for this service:

1. **Trend Analysis**: Compare current activity to previous periods
2. **Collaborative Insights**: Generate team-level insights across multiple users
3. **Custom Templates**: Allow users to define custom planning templates
4. **Scheduled Generation**: Automatically generate insights on a schedule
5. **Export Options**: Export plans to various formats (PDF, Notion, etc.)
6. **Feedback Loop**: Learn from user actions on previous plans to improve recommendations

## Troubleshooting

### Service returns fallback plans

**Cause**: LLM is generating invalid JSON or failing
**Solution**: 
- Check LLM configuration and API keys
- Try a different LLM model
- Check logs for detailed error messages

### No key topics identified

**Cause**: Document titles are too generic or short
**Solution**: This is normal; the LLM still generates useful plans based on document content

### Analysis is too slow

**Cause**: Too many documents or slow LLM
**Solution**:
- Reduce `num_documents` parameter
- Use a faster LLM model
- Enable LLM caching if supported

## Contributing

To enhance this service:

1. Improve topic extraction algorithm in `_generate_activity_insights`
2. Add more sophisticated document clustering
3. Implement ML-based priority prediction
4. Add support for custom planning templates

## License

This service is part of the SurfSense backend and follows the same license as the main project.
