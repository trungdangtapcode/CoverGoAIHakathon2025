# User Activity Insights & Planning Service

## 📋 Overview

A complete AI-powered service for SurfSense that analyzes user document activity and generates strategic action plans. The service intelligently distinguishes between:

- **Information Consumption** (connector documents): What the user is reading/gathering
- **Work Output** (file documents): What the user is creating/working on

It then uses AI to generate personalized, actionable recommendations.

---

## 🎯 What This Service Does

1. **Analyzes Recent Activity**: Fetches and examines the last 50-200 documents
2. **Identifies Patterns**: Extracts key topics and activity trends
3. **Generates Insights**: Summarizes what the user has been focused on
4. **Creates Plans**: Uses AI to generate 3-7 prioritized action items
5. **Provides Context**: Explains why each action is recommended

---

## 📁 Files Created

### Core Implementation (3 files)

1. **`app/services/insights_service.py`** (442 lines)
   - Main business logic
   - Document fetching and filtering
   - Activity analysis
   - LLM-powered planning
   - Fallback mechanisms

2. **`app/routes/insights_routes.py`** (161 lines)
   - RESTful API endpoints
   - Authentication & authorization
   - Error handling
   - Two endpoints: generate & preview

3. **`app/schemas/insights.py`** (71 lines)
   - Pydantic models for type safety
   - Request/response validation
   - 5 data models with full validation

### Documentation (3 files)

4. **`INSIGHTS_SERVICE_README.md`** (693 lines)
   - Complete user guide
   - API documentation
   - Integration examples (Python, TypeScript)
   - Troubleshooting
   - Performance tips

5. **`IMPLEMENTATION_SUMMARY.md`** (453 lines)
   - Technical overview
   - Architecture explanation
   - How it works
   - Integration points
   - Use cases

6. **`API_ENDPOINTS_INSIGHTS.md`** (428 lines)
   - API endpoint reference
   - Request/response schemas
   - Example requests/responses
   - Error handling
   - Best practices

### Testing & Demo (2 files)

7. **`tests/test_insights.py`** (355 lines)
   - Comprehensive test suite
   - Unit tests
   - Integration tests
   - Edge case testing

8. **`demo_insights.py`** (390 lines)
   - Interactive CLI demo
   - Beautiful formatted output
   - Usage examples
   - Two modes: preview & generate

### Integration Files (2 files)

9. **`app/app.py`** (modified)
   - Registered new route
   - Added insights router

10. **`app/schemas/__init__.py`** (modified)
    - Exported new schemas
    - Type system integration

---

## 🚀 Quick Start

### 1. Preview Recent Activity
```bash
python demo_insights.py preview \
  --search-space-id 1 \
  --token YOUR_JWT_TOKEN
```

### 2. Generate Full Insights & Plan
```bash
python demo_insights.py generate \
  --search-space-id 1 \
  --token YOUR_JWT_TOKEN \
  --num-docs 50
```

### 3. API Call
```bash
curl -X POST "http://localhost:8002/api/v1/insights/generate" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "search_space_id": 1,
    "num_documents": 50,
    "include_connectors": true,
    "include_files": true
  }'
```

---

## 🎨 Key Features

### ✅ Smart Document Analysis
- Analyzes 10-200 recent documents (configurable)
- Separates information consumption vs. work output
- Extracts key topics automatically
- Identifies activity patterns

### 🤖 AI-Powered Planning
- Uses user's configured strategic LLM
- Generates 3-7 actionable items
- Prioritizes tasks (HIGH/MEDIUM/LOW)
- Provides rationale for each recommendation
- Estimates completion timeframes

### 🛡️ Robust Error Handling
- Fallback plans when LLM unavailable
- Graceful handling of edge cases
- Detailed error messages
- Input validation

### 🔧 Flexible Configuration
- Adjustable document count
- Toggle connector/file documents
- Per-search-space analysis
- Preview mode for quick checks

---

## 📊 Example Output

```json
{
  "insights": {
    "summary": "Analyzed 50 documents from the last 3 days...",
    "key_topics": ["Project", "Design", "Development"],
    "connector_activity": {
      "SLACK_CONNECTOR": 20,
      "NOTION_CONNECTOR": 15,
      "FILE": 5
    }
  },
  "plan": {
    "title": "Weekly Productivity Plan",
    "action_items": [
      {
        "title": "Review design documents",
        "priority": "HIGH",
        "description": "Consolidate 5 design files...",
        "rationale": "Multiple design discussions indicate focus area"
      }
    ],
    "estimated_timeframe": "1-2 weeks"
  }
}
```

---

## 🏗️ Architecture

```
User Request
    ↓
Authentication (JWT)
    ↓
Fetch Recent Documents (DB Query)
    ↓
Generate Activity Insights
    ↓
Call LLM for Planning
    ↓
Return Structured Response
```

---

## 🔗 API Endpoints

### 1. Generate Insights & Plan
```
POST /api/v1/insights/generate
```
Analyzes documents and generates AI-powered plan

### 2. Preview Activity
```
GET /api/v1/insights/preview/{search_space_id}
```
Quick preview without LLM (faster, cheaper)

---

## 📦 Dependencies

**No new dependencies!** Uses existing packages:
- FastAPI (web framework)
- SQLAlchemy (database)
- Pydantic (validation)
- LiteLLM (via existing service)

---

## ✅ Testing

Run the test suite:
```bash
pytest tests/test_insights.py -v
```

Tests cover:
- ✅ Document fetching with filters
- ✅ Activity analysis
- ✅ Plan generation
- ✅ Fallback mechanisms
- ✅ API endpoints
- ✅ Edge cases

---

## 🎯 Use Cases

1. **Daily Planning**: Generate tasks at start of day
2. **Weekly Review**: Understand past week's activity
3. **Project Context**: See current focus areas
4. **Team Insights**: Analyze team patterns
5. **Productivity**: Get AI recommendations

---

## 📖 Documentation Files

All documentation is comprehensive and includes:

- **User Guide** (`INSIGHTS_SERVICE_README.md`): Complete usage instructions
- **Technical Summary** (`IMPLEMENTATION_SUMMARY.md`): Architecture & implementation
- **API Reference** (`API_ENDPOINTS_INSIGHTS.md`): Endpoint documentation
- **This Summary** (`FILES_CREATED_SUMMARY.md`): Quick overview

---

## 🔧 Configuration Required

Users need:
1. ✅ Strategic LLM configured in search space
2. ✅ At least one search space with documents
3. ✅ JWT token for authentication

No additional setup or environment variables required!

---

## 💡 Tips

- Use **50-100 documents** for balanced analysis
- Enable **both connectors and files** for comprehensive insights
- Use **preview endpoint** first to check data
- Generate insights **daily or weekly** for best results
- Cache results for **~1 hour** if generating frequently

---

## 🎉 Summary Statistics

- **Total Files Created**: 10 files
- **Total Lines of Code**: ~2,900 lines
- **Test Coverage**: Comprehensive
- **Documentation**: Complete
- **Dependencies**: None (uses existing)
- **API Endpoints**: 2
- **Supported Document Types**: 14+

---

## 📝 Next Steps

1. Start the backend: `uvicorn main:app --reload`
2. Run the demo: `python demo_insights.py preview --search-space-id 1 --token TOKEN`
3. Try the API: Use the examples in the documentation
4. Run tests: `pytest tests/test_insights.py -v`
5. Read the docs: Start with `INSIGHTS_SERVICE_README.md`

---

## 🙏 Credits

Built for the SurfSense project as a complete, production-ready feature that helps users transform their document activity into actionable insights and strategic plans.

---

## 📞 Support

- Check `INSIGHTS_SERVICE_README.md` for detailed usage
- Review `IMPLEMENTATION_SUMMARY.md` for technical details
- See `API_ENDPOINTS_INSIGHTS.md` for API reference
- Run `demo_insights.py` for interactive examples

**Ready to use!** 🚀
