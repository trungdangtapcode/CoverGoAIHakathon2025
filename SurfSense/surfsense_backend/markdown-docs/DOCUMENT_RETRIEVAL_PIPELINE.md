# SurfSense Document Retrieval Pipeline - Complete Guide

## Overview

This guide provides a comprehensive understanding of how SurfSense retrieves documents from the database, showing the complete data flow from API endpoints to database queries. This will help you build third-party integrations that interact with the system.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Database Schema](#database-schema)
3. [Retrieval Pipeline Flow](#retrieval-pipeline-flow)
4. [API Endpoints](#api-endpoints)
5. [Search & Retrieval Services](#search--retrieval-services)
6. [Integration Examples](#integration-examples)
7. [Third-Party Integration Guide](#third-party-integration-guide)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client/Third-Party                        │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP/REST API
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Application                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Authentication Layer (JWT/OAuth)                         │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                            ▼                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  API Routes Layer                                         │  │
│  │  - /api/v1/documents/ (CRUD)                              │  │
│  │  - /api/v1/chats/ (Q&A, Research)                         │  │
│  │  - /api/v1/search-source-connectors/ (Connector Search)   │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                            ▼                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Service Layer                                            │  │
│  │  - ConnectorService: Orchestrates multi-source search     │  │
│  │  - QueryService: Handles chat/research queries            │  │
│  │  - LLMService: Manages AI model interactions              │  │
│  │  - RerankerService: Re-ranks search results               │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                            ▼                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Retrieval Layer                                          │  │
│  │  - ChucksHybridSearchRetriever                            │  │
│  │  - DocumentHybridSearchRetriever                          │  │
│  │  - Methods: vector_search, text_search, hybrid_search     │  │
│  └────────────────────────┬─────────────────────────────────┘  │
└───────────────────────────┼─────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              PostgreSQL Database (with pgvector)                 │
│                                                                  │
│  Tables:                                                         │
│  - users: User accounts                                          │
│  - searchspaces: User's search spaces/workspaces                 │
│  - documents: Indexed documents with embeddings                  │
│  - chunks: Document chunks with embeddings                       │
│  - searchsourceconnectors: External data source configs          │
│  - chats: Chat history and Q&A sessions                          │
│                                                                  │
│  Indexes:                                                        │
│  - HNSW vector indexes on embeddings (for similarity search)     │
│  - B-tree indexes on foreign keys                                │
│  - GIN indexes on text content (for full-text search)            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Database Schema

### Core Tables

#### 1. **users**
```sql
- id: UUID (PK)
- email: String
- hashed_password: String
- is_active: Boolean
- is_verified: Boolean
- created_at: Timestamp
```

#### 2. **searchspaces** (User Workspaces)
```sql
- id: Integer (PK)
- user_id: UUID (FK -> users.id)
- name: String
- created_at: Timestamp
- updated_at: Timestamp
```

#### 3. **documents** (Main document storage)
```sql
- id: Integer (PK)
- search_space_id: Integer (FK -> searchspaces.id)
- title: String
- content: Text (full document content)
- embedding: Vector(384) (document-level embedding)
- document_type: Enum (EXTENSION, FILE, SLACK_CONNECTOR, NOTION_CONNECTOR, etc.)
- document_metadata: JSON (flexible metadata storage)
- content_hash: String (for deduplication)
- unique_identifier_hash: String (for tracking)
- created_at: Timestamp
- updated_at: Timestamp
```

#### 4. **chunks** (Document chunks for RAG)
```sql
- id: Integer (PK)
- document_id: Integer (FK -> documents.id)
- content: Text (chunk content)
- embedding: Vector(384) (chunk-level embedding)
- created_at: Timestamp
```

#### 5. **searchsourceconnectors** (External data sources)
```sql
- id: Integer (PK)
- search_space_id: Integer (FK -> searchspaces.id)
- connector_type: Enum (SLACK_CONNECTOR, NOTION_CONNECTOR, GITHUB_CONNECTOR, etc.)
- credentials: JSON (encrypted credentials)
- config: JSON (connector-specific configuration)
- is_active: Boolean
- created_at: Timestamp
```

#### 6. **chats** (Conversation history)
```sql
- id: Integer (PK)
- search_space_id: Integer (FK -> searchspaces.id)
- chat_type: Enum (QNA, REPORT_GENERAL, REPORT_DEEP, REPORT_DEEPER)
- user_query: Text
- ai_response: Text
- metadata: JSON (includes sources, processing time, etc.)
- created_at: Timestamp
```

### Relationships

```
users (1) ──────> (N) searchspaces
searchspaces (1) ──> (N) documents
searchspaces (1) ──> (N) searchsourceconnectors
searchspaces (1) ──> (N) chats
documents (1) ────> (N) chunks
```

---

## Retrieval Pipeline Flow

### Flow 1: Simple Document Retrieval

```
1. Client Request
   ↓
   GET /api/v1/documents/?search_space_id=1&page=0&page_size=50
   Header: Authorization: Bearer <JWT_TOKEN>

2. Authentication
   ↓
   JWT token verified → user.id extracted

3. Route Handler (documents_routes.py)
   ↓
   async def read_documents(...)
   
4. Database Query Construction
   ↓
   query = select(Document)
           .join(SearchSpace)
           .filter(SearchSpace.user_id == user.id)
           .filter(Document.search_space_id == search_space_id)
           .offset(page * page_size)
           .limit(page_size)

5. Query Execution
   ↓
   result = await session.execute(query)
   documents = result.scalars().all()

6. Response Serialization
   ↓
   return PaginatedResponse(items=documents, total=count)
```

### Flow 2: Hybrid Search (Vector + Full-Text)

```
1. Client Request
   ↓
   POST /api/v1/chats/qna
   {
     "query": "What are the key features?",
     "search_space_id": 1,
     "configuration": {...}
   }

2. Authentication & Routing
   ↓
   JWT → user.id → QueryService

3. QueryService.qna_chat()
   ↓
   - Extracts search sources from configuration
   - Calls ConnectorService for each source

4. ConnectorService Search Methods
   ↓
   For each connector type:
   - search_crawled_urls()
   - search_slack()
   - search_notion()
   - search_github()
   etc.

5. ChucksHybridSearchRetriever.hybrid_search()
   ↓
   Step 5a: Vector Search
   ├─ Embed query using embedding_model
   ├─ Query: SELECT * FROM chunks
   │         WHERE search_space_id = ?
   │         ORDER BY embedding <=> query_embedding
   │         LIMIT top_k*2
   │
   Step 5b: Full-Text Search (PostgreSQL)
   ├─ Query: SELECT * FROM chunks
   │         WHERE search_space_id = ?
   │         AND to_tsvector('english', content) @@ plainto_tsquery('english', query)
   │         ORDER BY ts_rank(to_tsvector(content), plainto_tsquery(query)) DESC
   │         LIMIT top_k*2
   │
   Step 5c: RRF (Reciprocal Rank Fusion)
   ├─ Combine vector + text results using formula:
   │  score(doc) = Σ (1 / (k + rank_in_method))
   │  where k=60, rank_in_method is position in each result set
   │
   └─ Return top_k results sorted by combined score

6. Reranker Service (Optional)
   ↓
   - Takes hybrid search results
   - Uses reranker model (e.g., ms-marco-MiniLM-L-12-v2)
   - Reranks based on semantic relevance to query
   - Returns top results

7. LLM Service
   ↓
   - Assembles context from retrieved chunks
   - Constructs prompt with context + query
   - Calls LLM (OpenAI, Anthropic, etc.)
   - Streams response back to client

8. Response with Sources
   ↓
   {
     "response": "Based on the documents...",
     "sources": [
       {
         "id": 1,
         "type": "NOTION_CONNECTOR",
         "documents": [...],
         "score": 0.95
       }
     ]
   }
```

### Flow 3: Document Indexing (Background)

```
1. Document Upload/Connector Sync
   ↓
   POST /api/v1/documents/fileupload
   or
   Celery periodic task triggers connector sync

2. Celery Task Queue
   ↓
   Task: process_file_document_task(file_path, search_space_id, user_id)

3. Document Processing
   ↓
   - Extract text (Unstructured.io, LlamaCloud, Docling)
   - Generate summary using LLM
   - Create document metadata

4. Embedding Generation
   ↓
   - Load embedding model (e.g., all-MiniLM-L6-v2)
   - Generate document-level embedding
   - embedding = embedding_model.embed(summary)

5. Chunking
   ↓
   - Use chunking strategy (RecursiveChunker or CodeChunker)
   - Split document into semantic chunks
   - chunks = chunker.chunk(content)

6. Chunk Embedding
   ↓
   For each chunk:
   - chunk_embedding = embedding_model.embed(chunk.text)

7. Database Storage
   ↓
   BEGIN TRANSACTION
   ├─ INSERT INTO documents (title, content, embedding, ...)
   ├─ Get document.id
   ├─ INSERT INTO chunks (document_id, content, embedding, ...)
   └─ COMMIT

8. Vector Index Update
   ↓
   PostgreSQL automatically updates HNSW indexes
```

---

## API Endpoints

### Document CRUD Endpoints

#### 1. List Documents
```http
GET /api/v1/documents/
Authorization: Bearer <JWT_TOKEN>

Query Parameters:
- skip: int (absolute offset, optional)
- page: int (zero-based page index, optional)
- page_size: int (default: 50, use -1 for all)
- search_space_id: int (optional filter)
- document_types: string (comma-separated, e.g., "FILE,SLACK_CONNECTOR")

Response:
{
  "items": [
    {
      "id": 1,
      "title": "Document Title",
      "document_type": "FILE",
      "content": "...",
      "document_metadata": {...},
      "search_space_id": 1,
      "created_at": "2025-01-01T00:00:00Z"
    }
  ],
  "total": 100
}
```

#### 2. Get Single Document
```http
GET /api/v1/documents/{document_id}
Authorization: Bearer <JWT_TOKEN>

Response:
{
  "id": 1,
  "title": "Document Title",
  "document_type": "FILE",
  "content": "Full content...",
  "document_metadata": {...},
  "search_space_id": 1,
  "created_at": "2025-01-01T00:00:00Z",
  "chunks": [
    {
      "id": 1,
      "content": "Chunk 1 content...",
      "created_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

#### 3. Update Document
```http
PATCH /api/v1/documents/{document_id}
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
  "title": "Updated Title",
  "content": "Updated content..."
}
```

#### 4. Delete Document
```http
DELETE /api/v1/documents/{document_id}
Authorization: Bearer <JWT_TOKEN>
```

### Search & Query Endpoints

#### 5. Q&A Chat (Hybrid Search + LLM)
```http
POST /api/v1/chats/qna
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
  "query": "What are the main features of this product?",
  "search_space_id": 1,
  "configuration": {
    "connectors_to_search": ["NOTION_CONNECTOR", "SLACK_CONNECTOR"],
    "llm_config_id": 1,
    "top_k": 20,
    "stream": false
  }
}

Response (Streaming):
data: {"type": "sources", "data": {...}}
data: {"type": "response", "chunk": "Based on..."}
data: {"type": "done"}
```

#### 6. Search Connectors
```http
GET /api/v1/search-source-connectors/
Authorization: Bearer <JWT_TOKEN>

Query Parameters:
- search_space_id: int (required)

Response:
[
  {
    "id": 1,
    "connector_type": "NOTION_CONNECTOR",
    "config": {...},
    "is_active": true
  }
]
```

---

## Search & Retrieval Services

### 1. ChucksHybridSearchRetriever

**Location:** `app/retriver/chunks_hybrid_search.py`

**Key Methods:**

```python
class ChucksHybridSearchRetriever:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
    
    async def vector_search(
        self,
        query_text: str,
        top_k: int,
        user_id: str,
        search_space_id: int | None = None
    ) -> list:
        """
        Pure vector similarity search using pgvector.
        
        SQL Query:
        SELECT * FROM chunks
        JOIN documents ON chunks.document_id = documents.id
        JOIN searchspaces ON documents.search_space_id = searchspaces.id
        WHERE searchspaces.user_id = ?
          AND searchspaces.id = ? (if provided)
        ORDER BY chunks.embedding <=> ?  -- cosine similarity operator
        LIMIT ?
        """
    
    async def text_search(
        self,
        query_text: str,
        top_k: int,
        user_id: str,
        search_space_id: int | None = None
    ) -> list:
        """
        Full-text search using PostgreSQL tsvector.
        
        SQL Query:
        SELECT *, ts_rank(to_tsvector('english', content), 
                          plainto_tsquery('english', ?)) as rank
        FROM chunks
        JOIN documents ON chunks.document_id = documents.id
        JOIN searchspaces ON documents.search_space_id = searchspaces.id
        WHERE searchspaces.user_id = ?
          AND to_tsvector('english', content) @@ plainto_tsquery('english', ?)
        ORDER BY rank DESC
        LIMIT ?
        """
    
    async def hybrid_search(
        self,
        query_text: str,
        top_k: int,
        user_id: str,
        search_space_id: int | None = None,
        document_type: str | None = None
    ) -> list:
        """
        Combines vector and text search using RRF (Reciprocal Rank Fusion).
        
        Algorithm:
        1. Get top_k*2 results from vector_search
        2. Get top_k*2 results from text_search
        3. Apply RRF formula:
           score(doc) = Σ (1 / (k + rank_in_method))
           where k=60 (constant), rank_in_method is position
        4. Sort by combined score, return top_k
        """
```

### 2. DocumentHybridSearchRetriever

**Location:** `app/retriver/documents_hybrid_search.py`

Similar to chunks retriever but operates on document-level embeddings.

### 3. ConnectorService

**Location:** `app/services/connector_service.py`

**Key Methods:**

```python
class ConnectorService:
    def __init__(self, session: AsyncSession, user_id: str):
        self.session = session
        self.chunk_retriever = ChucksHybridSearchRetriever(session)
        self.document_retriever = DocumentHybridSearchRetriever(session)
    
    async def search_crawled_urls(self, user_query, user_id, search_space_id, top_k):
        """Search crawled web pages."""
    
    async def search_slack(self, user_query, user_id, search_space_id, top_k):
        """Search Slack messages."""
    
    async def search_notion(self, user_query, user_id, search_space_id, top_k):
        """Search Notion pages."""
    
    async def search_github(self, user_query, user_id, search_space_id, top_k):
        """Search GitHub repositories."""
    
    # ... many more connector-specific search methods
```

---

## Integration Examples

### Example 1: Python Third-Party Client

```python
import requests
from typing import List, Dict, Any

class SurfSenseClient:
    def __init__(self, base_url: str, email: str, password: str):
        self.base_url = base_url
        self.token = self._authenticate(email, password)
    
    def _authenticate(self, email: str, password: str) -> str:
        """Get JWT token."""
        response = requests.post(
            f"{self.base_url}/auth/jwt/login",
            data={"username": email, "password": password}
        )
        response.raise_for_status()
        return response.json()["access_token"]
    
    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def list_documents(
        self,
        search_space_id: int,
        page: int = 0,
        page_size: int = 50,
        document_types: List[str] = None
    ) -> Dict[str, Any]:
        """Retrieve documents from a search space."""
        params = {
            "search_space_id": search_space_id,
            "page": page,
            "page_size": page_size
        }
        if document_types:
            params["document_types"] = ",".join(document_types)
        
        response = requests.get(
            f"{self.base_url}/api/v1/documents/",
            headers=self._headers(),
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def get_document(self, document_id: int) -> Dict[str, Any]:
        """Get a single document with chunks."""
        response = requests.get(
            f"{self.base_url}/api/v1/documents/{document_id}",
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()
    
    def search_documents(
        self,
        query: str,
        search_space_id: int,
        connectors: List[str] = None,
        top_k: int = 20
    ) -> Dict[str, Any]:
        """Perform semantic search on documents."""
        payload = {
            "query": query,
            "search_space_id": search_space_id,
            "configuration": {
                "connectors_to_search": connectors or ["CRAWLED_URL"],
                "top_k": top_k,
                "stream": False
            }
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/chats/qna",
            headers=self._headers(),
            json=payload
        )
        response.raise_for_status()
        return response.json()

# Usage
client = SurfSenseClient(
    base_url="http://localhost:8002",
    email="user@example.com",
    password="your_password"
)

# List all documents in search space
docs = client.list_documents(search_space_id=1, page_size=100)
print(f"Found {docs['total']} documents")

# Get specific document
doc = client.get_document(document_id=42)
print(f"Document: {doc['title']}")
print(f"Content length: {len(doc['content'])}")
print(f"Number of chunks: {len(doc['chunks'])}")

# Semantic search
results = client.search_documents(
    query="What are the pricing plans?",
    search_space_id=1,
    connectors=["NOTION_CONNECTOR", "CRAWLED_URL"]
)
print(f"AI Response: {results['response']}")
print(f"Sources: {len(results['sources'])}")
```

### Example 2: JavaScript/TypeScript Integration

```typescript
interface SurfSenseDocument {
  id: number;
  title: string;
  content: string;
  document_type: string;
  document_metadata: Record<string, any>;
  search_space_id: number;
  created_at: string;
}

interface PaginatedResponse<T> {
  items: T[];
  total: number;
}

class SurfSenseAPI {
  private token: string | null = null;
  
  constructor(private baseUrl: string) {}
  
  async authenticate(email: string, password: string): Promise<void> {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);
    
    const response = await fetch(`${this.baseUrl}/auth/jwt/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData
    });
    
    if (!response.ok) throw new Error('Authentication failed');
    
    const data = await response.json();
    this.token = data.access_token;
  }
  
  private headers(): HeadersInit {
    return {
      'Authorization': `Bearer ${this.token}`,
      'Content-Type': 'application/json'
    };
  }
  
  async listDocuments(
    searchSpaceId: number,
    page: number = 0,
    pageSize: number = 50
  ): Promise<PaginatedResponse<SurfSenseDocument>> {
    const params = new URLSearchParams({
      search_space_id: searchSpaceId.toString(),
      page: page.toString(),
      page_size: pageSize.toString()
    });
    
    const response = await fetch(
      `${this.baseUrl}/api/v1/documents/?${params}`,
      { headers: this.headers() }
    );
    
    if (!response.ok) throw new Error('Failed to fetch documents');
    return response.json();
  }
  
  async getDocument(documentId: number): Promise<SurfSenseDocument> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/documents/${documentId}`,
      { headers: this.headers() }
    );
    
    if (!response.ok) throw new Error('Failed to fetch document');
    return response.json();
  }
  
  async searchDocuments(
    query: string,
    searchSpaceId: number,
    connectors: string[] = ['CRAWLED_URL']
  ): Promise<any> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/chats/qna`,
      {
        method: 'POST',
        headers: this.headers(),
        body: JSON.stringify({
          query,
          search_space_id: searchSpaceId,
          configuration: {
            connectors_to_search: connectors,
            top_k: 20,
            stream: false
          }
        })
      }
    );
    
    if (!response.ok) throw new Error('Search failed');
    return response.json();
  }
}

// Usage
const api = new SurfSenseAPI('http://localhost:8002');
await api.authenticate('user@example.com', 'password');

const documents = await api.listDocuments(1, 0, 100);
console.log(`Found ${documents.total} documents`);

const doc = await api.getDocument(42);
console.log(`Document: ${doc.title}`);

const searchResults = await api.searchDocuments(
  'pricing information',
  1,
  ['NOTION_CONNECTOR', 'SLACK_CONNECTOR']
);
console.log('AI Response:', searchResults.response);
```

### Example 3: Direct Database Access (Advanced)

```python
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, and_
from pgvector.sqlalchemy import Vector

# Import SurfSense models
from app.db import Document, Chunk, SearchSpace

async def direct_database_query():
    """
    Example of directly querying the database.
    Only use this if you have direct database access.
    """
    # Create engine
    engine = create_async_engine(
        "postgresql+asyncpg://user:password@localhost:5432/surfsense"
    )
    
    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # Query documents for a specific user and search space
        query = (
            select(Document)
            .join(SearchSpace)
            .where(
                and_(
                    SearchSpace.user_id == "user-uuid-here",
                    Document.search_space_id == 1,
                    Document.document_type == "NOTION_CONNECTOR"
                )
            )
            .limit(10)
        )
        
        result = await session.execute(query)
        documents = result.scalars().all()
        
        for doc in documents:
            print(f"Document: {doc.title}")
            print(f"Type: {doc.document_type}")
            print(f"Content preview: {doc.content[:100]}...")
            print("---")
        
        # Vector similarity search
        # First, get query embedding (you'd use your embedding model here)
        query_embedding = [0.1] * 384  # Placeholder
        
        # Find similar chunks
        similar_chunks_query = (
            select(Chunk)
            .join(Document)
            .join(SearchSpace)
            .where(SearchSpace.user_id == "user-uuid-here")
            .order_by(Chunk.embedding.cosine_distance(query_embedding))
            .limit(5)
        )
        
        result = await session.execute(similar_chunks_query)
        chunks = result.scalars().all()
        
        for chunk in chunks:
            print(f"Chunk: {chunk.content[:100]}...")
            print("---")

# Run
asyncio.run(direct_database_query())
```

---

## Third-Party Integration Guide

### Authentication Flow

1. **Get JWT Token**
   ```http
   POST /auth/jwt/login
   Content-Type: application/x-www-form-urlencoded
   
   username=user@example.com&password=your_password
   
   Response:
   {
     "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
     "token_type": "bearer"
   }
   ```

2. **Use Token in Requests**
   ```http
   GET /api/v1/documents/
   Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
   ```

3. **Refresh Token (if needed)**
   - Tokens expire after a certain period
   - Re-authenticate to get a new token

### Best Practices for Integration

1. **Rate Limiting**
   - Implement exponential backoff for failed requests
   - Cache frequently accessed data
   - Use pagination for large datasets

2. **Error Handling**
   ```python
   try:
       response = requests.get(url, headers=headers)
       response.raise_for_status()
   except requests.exceptions.HTTPError as e:
       if e.response.status_code == 401:
           # Re-authenticate
           token = authenticate()
       elif e.response.status_code == 429:
           # Rate limited, wait and retry
           time.sleep(60)
       else:
           # Handle other errors
           log_error(e)
   ```

3. **Pagination**
   ```python
   def get_all_documents(client, search_space_id):
       page = 0
       all_docs = []
       
       while True:
           response = client.list_documents(
               search_space_id=search_space_id,
               page=page,
               page_size=100
           )
           all_docs.extend(response['items'])
           
           if len(all_docs) >= response['total']:
               break
           page += 1
       
       return all_docs
   ```

4. **Streaming Responses**
   ```python
   def stream_chat_response(query, search_space_id):
       response = requests.post(
           f"{base_url}/api/v1/chats/qna",
           headers=headers,
           json={
               "query": query,
               "search_space_id": search_space_id,
               "configuration": {"stream": True}
           },
           stream=True
       )
       
       for line in response.iter_lines():
           if line:
               data = line.decode('utf-8').replace('data: ', '')
               event = json.loads(data)
               
               if event['type'] == 'sources':
                   print("Sources:", event['data'])
               elif event['type'] == 'response':
                   print(event['chunk'], end='', flush=True)
               elif event['type'] == 'done':
                   break
   ```

### Common Use Cases

#### Use Case 1: Document Sync to External System
```python
# Sync SurfSense documents to your CRM/knowledge base
def sync_documents_to_external_system():
    client = SurfSenseClient(...)
    
    # Get all documents updated in last 24 hours
    docs = client.list_documents(
        search_space_id=1,
        page_size=-1  # Get all
    )
    
    for doc in docs['items']:
        # Check if document is new/updated
        if is_recent(doc['updated_at']):
            # Sync to external system
            external_api.create_or_update(
                id=doc['id'],
                title=doc['title'],
                content=doc['content'],
                metadata=doc['document_metadata']
            )
```

#### Use Case 2: Custom Search Interface
```python
# Build a custom search UI on top of SurfSense
def custom_search(user_query):
    client = SurfSenseClient(...)
    
    # Perform search
    results = client.search_documents(
        query=user_query,
        search_space_id=get_user_workspace(),
        connectors=['NOTION_CONNECTOR', 'SLACK_CONNECTOR', 'GITHUB_CONNECTOR']
    )
    
    # Format results for your UI
    return {
        'answer': results['response'],
        'sources': format_sources(results['sources']),
        'related_docs': extract_related_docs(results)
    }
```

#### Use Case 3: Analytics Dashboard
```python
# Build analytics on document usage
def get_document_analytics(search_space_id):
    client = SurfSenseClient(...)
    
    # Get all documents
    docs = client.list_documents(search_space_id, page_size=-1)
    
    # Analyze
    analytics = {
        'total_documents': docs['total'],
        'by_type': {},
        'by_date': {},
        'total_size': 0
    }
    
    for doc in docs['items']:
        # Count by type
        doc_type = doc['document_type']
        analytics['by_type'][doc_type] = analytics['by_type'].get(doc_type, 0) + 1
        
        # Size
        analytics['total_size'] += len(doc.get('content', ''))
    
    return analytics
```

---

## Performance Optimization Tips

### 1. Use Pagination
- Always paginate large result sets
- Use `page_size=-1` only when absolutely necessary

### 2. Filter Early
- Use `search_space_id` to narrow scope
- Use `document_types` filter to reduce dataset

### 3. Cache Frequently Accessed Data
```python
from functools import lru_cache
from datetime import datetime, timedelta

cache_ttl = {}

@lru_cache(maxsize=100)
def get_document_cached(document_id, timestamp):
    return client.get_document(document_id)

def get_document_with_ttl(document_id, ttl_minutes=10):
    now = datetime.now()
    cache_key = document_id
    
    if cache_key in cache_ttl:
        if now - cache_ttl[cache_key] < timedelta(minutes=ttl_minutes):
            return get_document_cached(document_id, cache_ttl[cache_key])
    
    cache_ttl[cache_key] = now
    return get_document_cached(document_id, now)
```

### 4. Batch Operations
- Retrieve multiple documents in one request when possible
- Use bulk endpoints if available

---

## Troubleshooting

### Issue 1: Authentication Fails
**Solution:** Check credentials, ensure user is verified and active

### Issue 2: Empty Results
**Solution:** Verify `search_space_id` ownership, check filters

### Issue 3: Slow Queries
**Solution:** 
- Reduce `top_k` parameter
- Use more specific filters
- Check database indexes

### Issue 4: Vector Search Not Working
**Solution:** Ensure pgvector extension is installed and embeddings are generated

---

## Conclusion

This guide provides a comprehensive overview of the SurfSense document retrieval pipeline. Key takeaways:

1. **Multi-layered architecture**: API → Services → Retrievers → Database
2. **Hybrid search**: Combines vector similarity and full-text search
3. **Secure access**: JWT authentication with user-scoped queries
4. **Flexible integration**: RESTful API with streaming support
5. **Scalable design**: Pagination, caching, and efficient indexing

For questions or support, refer to the API documentation at `/docs` or review the source code in the repository.
