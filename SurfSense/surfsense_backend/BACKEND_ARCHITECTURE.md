# SurfSense Backend - Complete Architecture Analysis

This document provides a comprehensive overview of the SurfSense backend architecture, including database schema, API endpoints, services, and use cases.

## 🗄️ Database & Entities

### Database Technology
- **PostgreSQL** with **pgvector** extension for vector embeddings
- **SQLAlchemy** (async) for ORM
- **Alembic** for migrations
- Database URL configured via `DATABASE_URL` environment variable

### Core Entities (Database Models)

#### 1. User ([db.py:396-415](db.py#L396-L415))
- UUID-based ID
- Supports two auth modes:
  - Standard: Email/password authentication
  - Google OAuth: With linked OAuth accounts
- **Fields:** email, hashed_password, is_active, is_superuser, is_verified
- **Relationships:** search_spaces, search_space_preferences

#### 2. SearchSpace ([db.py:217-269](db.py#L217-L269))
Central organizational unit for all user data
- **Fields:**
  - `id` (Integer, PK)
  - `name` (String, 100)
  - `description` (String, 500)
  - `user_id` (UUID, FK to User)
  - `created_at` (Timestamp)
- **Relationships:**
  - `documents` (one-to-many with Document)
  - `podcasts` (one-to-many with Podcast)
  - `chats` (one-to-many with Chat)
  - `logs` (one-to-many with Log)
  - `search_source_connectors` (one-to-many)
  - `llm_configs` (one-to-many)
  - `user_preferences` (one-to-many with UserSearchSpacePreference)

#### 3. Document ([db.py:171-190](db.py#L171-L190))
Stores indexed content from various sources
- **Fields:**
  - `id`, `title`, `content`, `content_hash`
  - `document_type` (Enum: EXTENSION, FILE, CRAWLED_URL, YOUTUBE_VIDEO, etc.)
  - `document_metadata` (JSON)
  - `unique_identifier_hash` (for deduplication)
  - `embedding` (Vector - pgvector)
  - `search_space_id` (FK)
  - `created_at`
- **Indexes:**
  - HNSW index on embedding (vector similarity)
  - GIN index on content (full-text search)
- **Relationships:**
  - `chunks` (one-to-many with Chunk)
  - `search_space` (many-to-one)

#### 4. Chunk ([db.py:192-202](db.py#L192-L202))
Smaller text segments from documents for RAG
- **Fields:**
  - `id`, `content`
  - `embedding` (Vector)
  - `document_id` (FK)
  - `created_at`
- **Indexes:**
  - HNSW index on embedding
  - GIN index on content (full-text search)

#### 5. Chat ([db.py:157-169](db.py#L157-L169))
Conversation history
- **Fields:**
  - `id`, `title`
  - `type` (Enum: QNA, REPORT_GENERAL, REPORT_DEEP, REPORT_DEEPER)
  - `messages` (JSON - stores full conversation)
  - `initial_connectors` (Array of strings)
  - `search_space_id` (FK)
  - `created_at`

#### 6. Podcast ([db.py:204-215](db.py#L204-L215))
Generated audio content
- **Fields:**
  - `id`, `title`
  - `podcast_transcript` (JSON)
  - `file_location` (String, 500 - path to audio file)
  - `search_space_id` (FK)
  - `created_at`

#### 7. SearchSourceConnector ([db.py:271-303](db.py#L271-L303))
External data source integrations
- **Fields:**
  - `id`, `name`
  - `connector_type` (Enum - 14 types)
  - `is_indexable` (Boolean)
  - `last_indexed_at` (Timestamp)
  - `config` (JSON - connector-specific settings)
  - `periodic_indexing_enabled` (Boolean)
  - `indexing_frequency_minutes` (Integer)
  - `next_scheduled_at` (Timestamp)
  - `search_space_id`, `user_id` (FKs)
- **Unique Constraint:** (search_space_id, user_id, connector_type)

#### 8. LLMConfig ([db.py:305-328](db.py#L305-L328))
Custom LLM configurations per search space
- **Fields:**
  - `id`, `name`
  - `provider` (Enum: 30+ providers including OPENAI, ANTHROPIC, GROQ, OLLAMA, DEEPSEEK, etc.)
  - `custom_provider` (String, for CUSTOM type)
  - `model_name`, `api_key`, `api_base`
  - `language` (String, default "English")
  - `litellm_params` (JSON)
  - `search_space_id` (FK)
  - `created_at`

#### 9. UserSearchSpacePreference ([db.py:330-372](db.py#L330-L372))
User-specific LLM preferences for each search space
- **Fields:**
  - `user_id`, `search_space_id` (Composite unique key)
  - `long_context_llm_id` (FK to LLMConfig)
  - `fast_llm_id` (FK to LLMConfig)
  - `strategic_llm_id` (FK to LLMConfig)
  - Future RBAC fields planned

#### 10. Log ([db.py:374-389](db.py#L374-L389))
Activity and error tracking
- **Fields:**
  - `id`, `message`
  - `level` (Enum: DEBUG, INFO, WARNING, ERROR, CRITICAL)
  - `status` (Enum: IN_PROGRESS, SUCCESS, FAILED)
  - `source` (String, 200)
  - `log_metadata` (JSON)
  - `search_space_id` (FK)
  - `created_at`

### Enums

#### DocumentType ([db.py:36-54](db.py#L36-L54))
- `EXTENSION` - Browser extension data
- `CRAWLED_URL` - Web pages
- `FILE` - Uploaded files
- `YOUTUBE_VIDEO` - YouTube transcripts
- `SLACK_CONNECTOR` - Slack messages
- `NOTION_CONNECTOR` - Notion pages
- `GITHUB_CONNECTOR` - GitHub repositories
- `LINEAR_CONNECTOR` - Linear issues
- `DISCORD_CONNECTOR` - Discord messages
- `JIRA_CONNECTOR` - Jira issues
- `CONFLUENCE_CONNECTOR` - Confluence pages
- `CLICKUP_CONNECTOR` - ClickUp tasks
- `GOOGLE_CALENDAR_CONNECTOR` - Calendar events
- `GOOGLE_GMAIL_CONNECTOR` - Gmail messages
- `AIRTABLE_CONNECTOR` - Airtable records
- `LUMA_CONNECTOR` - Luma events
- `ELASTICSEARCH_CONNECTOR` - Elasticsearch documents

#### SearchSourceConnectorType ([db.py:56-75](db.py#L56-L75))
- Search APIs: `SERPER_API`, `TAVILY_API`, `SEARXNG_API`, `LINKUP_API`, `BAIDU_SEARCH_API`
- All connector types listed above

#### ChatType ([db.py:77-82](db.py#L77-L82))
- `QNA` - Question and Answer
- `REPORT_GENERAL` - General report
- `REPORT_DEEP` - Deep research report
- `REPORT_DEEPER` - Deeper research report

#### LiteLLMProvider ([db.py:84-119](db.py#L84-L119))
30+ LLM providers including:
- Major providers: OPENAI, ANTHROPIC, GROQ, COHERE, GOOGLE, AWS_BEDROCK, OLLAMA
- Chinese providers: DEEPSEEK, ALIBABA_QWEN, MOONSHOT, ZHIPU
- Others: MISTRAL, TOGETHER_AI, OPENROUTER, REPLICATE, PERPLEXITY, etc.

#### LogLevel & LogStatus ([db.py:121-133](db.py#L121-L133))
- LogLevel: DEBUG, INFO, WARNING, ERROR, CRITICAL
- LogStatus: IN_PROGRESS, SUCCESS, FAILED

---

## 🔌 API Endpoints

### Authentication ([app.py:40-78](app.py#L40-L78))
- `POST /auth/jwt/login` - JWT login
- `POST /auth/register` - User registration (can be disabled)
- `POST /auth/forgot-password` - Password reset
- `POST /auth/verify` - Email verification
- `POST /auth/google` - Google OAuth (if enabled)
- `GET /verify-token` - Token validation

### Users ([app.py:59-63](app.py#L59-L63))
- `GET /users/me` - Current user info
- `PATCH /users/me` - Update user profile

### Search Spaces
**Base path:** `/api/v1/searchspaces/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/` | Create search space |
| GET | `/` | List user's search spaces |
| GET | `/{id}` | Get specific search space |
| PUT | `/{id}` | Update search space |
| DELETE | `/{id}` | Delete search space |

### Documents
**Base path:** `/api/v1/documents/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/` | Create documents (Extension, Crawled URL, YouTube) |
| POST | `/fileupload` | Upload files |
| GET | `/` | List documents (paginated, filterable by type) |
| GET | `/search/` | Search documents by title |
| GET | `/{id}` | Get document |
| PUT | `/{id}` | Update document |
| DELETE | `/{id}` | Delete document |
| GET | `/type-counts/` | Document counts by type |
| GET | `/by-chunk/{chunk_id}` | Get document from chunk |

### Chats
**Base path:** `/api/v1/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chat` | Streaming chat with RAG (AI SDK compatible) |
| POST | `/chats/` | Save chat |
| GET | `/chats/` | List chats |
| GET | `/chats/{id}` | Get specific chat |
| PUT | `/chats/{id}` | Update chat |
| DELETE | `/chats/{id}` | Delete chat |

### Search Source Connectors
**Base path:** `/api/v1/search-source-connectors/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/github/repositories/` | List GitHub repos (validation) |
| POST | `/` | Create connector |
| GET | `/` | List connectors |
| GET | `/{id}` | Get connector |
| PUT | `/{id}` | Update connector |
| DELETE | `/{id}` | Delete connector |
| POST | `/{id}/index` | Trigger indexing (with date range params) |

### LLM Configs
**Base path:** `/api/v1/llm-configs/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/` | Create LLM config |
| GET | `/` | List configs for search space |
| GET | `/{id}` | Get config |
| PUT | `/{id}` | Update config |
| DELETE | `/{id}` | Delete config |
| GET | `/search-spaces/{id}/llm-preferences` | Get user's LLM preferences |
| PUT | `/search-spaces/{id}/llm-preferences` | Update user's LLM preferences |

### Podcasts
**Base path:** `/api/v1/podcasts/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/` | Create podcast |
| GET | `/` | List podcasts |
| GET | `/{id}` | Get podcast |
| PUT | `/{id}` | Update podcast |
| DELETE | `/{id}` | Delete podcast |
| POST | `/generate/` | Generate podcast from chat |
| GET | `/{id}/stream` | Stream podcast audio |

### Logs
**Base path:** `/api/v1/logs/`
- Standard CRUD operations for logs

---

## 🔧 Services & Business Logic

### Core Services ([app/services/](app/services/))

| Service | Description |
|---------|-------------|
| `llm_service.py` | LLM interaction via LiteLLM |
| `connector_service.py` | Connector management |
| `query_service.py` | Query processing |
| `streaming_service.py` | Streaming responses |
| `reranker_service.py` | Result reranking |
| `docling_service.py` | Document processing |
| `stt_service.py` | Speech-to-text |
| `kokoro_tts_service.py` | Text-to-speech |
| `task_logging_service.py` | Task logging |

### External Connectors ([app/connectors/](app/connectors/))

14 connector types for data ingestion:

| Connector | File | Description |
|-----------|------|-------------|
| Slack | `slack_history.py` | Slack messages and threads |
| Notion | `notion_history.py` | Notion pages and databases |
| GitHub | `github_connector.py` | GitHub repos, code, documentation |
| Linear | `linear_connector.py` | Linear issues and comments |
| Jira | `jira_connector.py` | Jira issues and comments |
| Confluence | `confluence_connector.py` | Confluence pages |
| ClickUp | `clickup_connector.py` | ClickUp tasks |
| Discord | `discord_connector.py` | Discord messages |
| Google Calendar | `google_calendar_connector.py` | Calendar events |
| Gmail | `google_gmail_connector.py` | Gmail messages |
| Airtable | `airtable_connector.py` | Airtable records |
| Luma | `luma_connector.py` | Luma events |
| Elasticsearch | `elasticsearch_connector.py` | Elasticsearch documents |

---

## ⚙️ Background Tasks (Celery)

### Task Categories

#### 1. Document Processing ([app/tasks/celery_tasks/document_tasks.py](app/tasks/celery_tasks/document_tasks.py))
- `process_extension_document_task` - Process browser extension data
- `process_crawled_url_task` - Process web pages
- `process_youtube_video_task` - Process YouTube videos
- `process_file_upload_task` - Process uploaded files

#### 2. Connector Indexing ([app/tasks/celery_tasks/connector_tasks.py](app/tasks/celery_tasks/connector_tasks.py))
Individual tasks for each connector type:
- `index_slack_messages_task`
- `index_notion_pages_task`
- `index_github_repos_task`
- `index_linear_issues_task`
- `index_jira_issues_task`
- `index_confluence_pages_task`
- `index_clickup_tasks_task`
- `index_discord_messages_task`
- `index_google_calendar_events_task`
- `index_google_gmail_messages_task`
- `index_airtable_records_task`
- `index_luma_events_task`
- `index_elasticsearch_documents_task`

#### 3. Podcast Generation ([app/tasks/celery_tasks/podcast_tasks.py](app/tasks/celery_tasks/podcast_tasks.py))
- `generate_chat_podcast_task` - Convert chat to podcast

#### 4. Schedule Checker ([app/tasks/celery_tasks/schedule_checker_task.py](app/tasks/celery_tasks/schedule_checker_task.py))
- Manages periodic connector indexing
- Checks `next_scheduled_at` timestamps
- Triggers reindexing based on `indexing_frequency_minutes`

### Document Processors ([app/tasks/document_processors/](app/tasks/document_processors/))
- Handle different file types and content extraction
- Integration with ETL services (Unstructured, LlamaCloud, Docling)
- Support for: PDF, DOCX, HTML, Markdown, etc.

---

## 🤖 AI Agents

### Researcher Agent ([app/agents/researcher/](app/agents/researcher/))
- **QnA Agent** ([qna_agent/](app/agents/researcher/qna_agent/))
  - Question answering with RAG
  - Context-aware responses
- **Sub-section Writer** ([sub_section_writer/](app/agents/researcher/sub_section_writer/))
  - Report generation
  - Multi-section document creation

### Podcaster Agent ([app/agents/podcaster/](app/agents/podcaster/))
- Generates podcast scripts from chat history
- Converts text to audio using TTS service
- Creates engaging conversational content

---

## 🔍 Retrieval & Search

### Retrievers ([app/retriver/](app/retriver/))

1. **chunks_hybrid_search.py** - Hybrid search on chunks
   - Combines vector similarity and full-text search
   - Used for granular content retrieval

2. **documents_hybrid_search.py** - Hybrid search on documents
   - Document-level search
   - Returns complete documents

### Search Capabilities
- **Vector Similarity Search:** HNSW index on pgvector embeddings
- **Full-Text Search:** GIN index with PostgreSQL tsvector
- **Hybrid Search:** Weighted combination of both methods
- **Reranking:** Post-processing with reranker models for better results

### Search Workflow
1. User query → Generate embedding
2. Parallel execution:
   - Vector search (cosine similarity)
   - Full-text search (tsvector)
3. Merge and deduplicate results
4. Rerank using reranker model
5. Return top-k results

---

## 🛠️ Configuration

### Environment Variables ([app/config/__init__.py](app/config/__init__.py))

#### Database
- `DATABASE_URL` - PostgreSQL connection string

#### Frontend
- `NEXT_FRONTEND_URL` - Frontend URL for OAuth redirects

#### Authentication
- `AUTH_TYPE` - "GOOGLE" or standard email/password
- `REGISTRATION_ENABLED` - Enable/disable user registration
- `SECRET_KEY` - JWT secret key
- `GOOGLE_OAUTH_CLIENT_ID` - Google OAuth client ID
- `GOOGLE_OAUTH_CLIENT_SECRET` - Google OAuth secret

#### AI/ML Models
- `EMBEDDING_MODEL` - Model for generating embeddings
- `RERANKERS_MODEL_NAME` - Reranker model name
- `RERANKERS_MODEL_TYPE` - Reranker model type

#### Document Processing
- `ETL_SERVICE` - "UNSTRUCTURED", "LLAMACLOUD", or "DOCLING"
- `UNSTRUCTURED_API_KEY` - Unstructured.io API key
- `LLAMA_CLOUD_API_KEY` - LlamaCloud API key
- `FIRECRAWL_API_KEY` - Firecrawl API key for web crawling

#### Speech Services
- `TTS_SERVICE` - Text-to-speech service
- `TTS_SERVICE_API_BASE` - TTS API base URL
- `TTS_SERVICE_API_KEY` - TTS API key
- `STT_SERVICE` - Speech-to-text service
- `STT_SERVICE_API_BASE` - STT API base URL
- `STT_SERVICE_API_KEY` - STT API key

#### Connector OAuth
- `GOOGLE_CALENDAR_REDIRECT_URI` - Google Calendar OAuth redirect
- `GOOGLE_GMAIL_REDIRECT_URI` - Gmail OAuth redirect
- `AIRTABLE_CLIENT_ID` - Airtable OAuth client ID
- `AIRTABLE_CLIENT_SECRET` - Airtable OAuth secret
- `AIRTABLE_REDIRECT_URI` - Airtable OAuth redirect

### Key Dependencies

#### Web Framework
- **FastAPI** - Modern async web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation

#### Database
- **SQLAlchemy** - Async ORM
- **Alembic** - Database migrations
- **asyncpg** - PostgreSQL async driver
- **pgvector** - Vector similarity search

#### Background Tasks
- **Celery** - Distributed task queue
- **Redis** - Message broker for Celery

#### AI/ML
- **LiteLLM** - Universal LLM API wrapper (30+ providers)
- **Chonkie** - Text chunking library
- **Rerankers** - Result reranking models
- **langchain** - LLM orchestration

#### Authentication
- **FastAPI Users** - Complete authentication system
- **httpx-oauth** - OAuth2 client

#### Document Processing
- **Unstructured** - Document parsing
- **Docling** - Document processing
- **yt-dlp** - YouTube video/audio download

#### Audio Processing
- **static-ffmpeg** - Audio encoding/decoding
- **pydub** - Audio manipulation

---

## 📊 Use Cases

### 1. Personal Knowledge Base
**Scenario:** Individual storing and searching personal information

**Features Used:**
- Document ingestion (files, web pages, YouTube)
- Semantic search across all content
- Chat-based Q&A interface
- Browser extension for automatic capture

**Workflow:**
1. Create search space
2. Upload documents/add URLs
3. Configure LLM preferences
4. Search and chat with knowledge base

### 2. Multi-Source Enterprise Search
**Scenario:** Team searching across multiple tools

**Features Used:**
- Connect Slack, Notion, GitHub, Jira, Confluence
- Unified search across all sources
- Periodic auto-indexing
- User-specific configurations

**Workflow:**
1. Set up search space
2. Add connector credentials
3. Enable periodic indexing
4. Search across all connected sources
5. Monitor indexing logs

### 3. Research & Report Generation
**Scenario:** Creating comprehensive research reports

**Features Used:**
- Deep research mode with multiple sources
- AI-powered report generation
- Convert reports to podcasts
- Multiple LLM support

**Workflow:**
1. Configure research connectors
2. Ask research question
3. AI generates multi-section report
4. Convert report to audio podcast
5. Stream or download podcast

### 4. Team Collaboration
**Scenario:** Shared knowledge repository

**Features Used:**
- Shared search spaces
- Multiple LLM configurations
- Activity logging
- Document type filtering

**Workflow:**
1. Create team search space
2. Configure team LLM preferences
3. Connect team data sources
4. Monitor usage via logs
5. Share search results

### 5. Multilingual Knowledge Management
**Scenario:** Working with multiple languages

**Features Used:**
- Language-specific LLM configurations
- Support for Chinese LLM providers (Deepseek, Qwen, etc.)
- Language-specific search
- Per-user language preferences

**Workflow:**
1. Add LLM configs for different languages
2. Set user preferences per language
3. Ensure all LLMs in a context use same language
4. Search and chat in preferred language

---

## 🏗️ Architecture Highlights

### Key Design Patterns

1. **Multi-tenancy via Search Spaces**
   - Users can have multiple isolated search spaces
   - Each space has its own documents, configs, and connectors

2. **Hybrid RAG Architecture**
   - Vector search for semantic similarity
   - Full-text search for keyword matching
   - Reranking for optimal results

3. **Flexible LLM Configuration**
   - Support for 30+ LLM providers
   - Custom API endpoints
   - Per-space and per-user preferences
   - Three LLM roles: long_context, fast, strategic

4. **Async-First Design**
   - All I/O operations are async
   - Celery for background processing
   - Streaming responses for chat

5. **Connector Pattern**
   - Standardized interface for all data sources
   - Config stored as JSON for flexibility
   - Periodic indexing support

### Security Features

- JWT authentication with configurable lifetime
- OAuth2 support (Google)
- Optional registration control
- User ownership validation on all operations
- API key encryption for LLM configs

### Scalability Considerations

- Async database connections with pooling
- Background task processing with Celery
- Efficient vector search with HNSW indexes
- Pagination on all list endpoints
- Configurable chunk sizes for large documents

---

## 📝 Summary

SurfSense Backend is a **comprehensive RAG (Retrieval-Augmented Generation) platform** that combines:

- ✅ Multi-source data ingestion (14 connector types)
- ✅ Hybrid semantic + full-text search
- ✅ Flexible multi-LLM support (30+ providers)
- ✅ Background processing and periodic indexing
- ✅ Podcast generation from conversations
- ✅ Multi-user with search space isolation
- ✅ RESTful API with streaming support
- ✅ Multilingual capabilities

**Total Codebase:** 120+ Python files organized in a modular, maintainable structure.
