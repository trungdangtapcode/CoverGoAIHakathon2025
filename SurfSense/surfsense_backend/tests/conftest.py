"""
Pytest configuration and fixtures for testing SurfSense backend.

This provides:
- Async database session fixtures
- Test client fixtures
- Mock user authentication
"""
import asyncio
import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.app import app
from app.db import Base, get_async_session, User

# Test database URL (use a separate test database)
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/surfsense_test"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def async_engine():
    """Create a test database engine"""
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session"""
    async_session_maker = async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session


@pytest.fixture(scope="function")
def override_get_async_session(async_session: AsyncSession):
    """Override the database session dependency"""
    async def _override_get_async_session():
        yield async_session

    return _override_get_async_session


@pytest.fixture(scope="function")
def test_client(override_get_async_session):
    """Create a test client with database override"""
    app.dependency_overrides[get_async_session] = override_get_async_session
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def test_user(async_session: AsyncSession) -> User:
    """Create a test user"""
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_password="$2b$12$test_hashed_password",
        is_active=True,
        is_verified=True,
        is_superuser=False,
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def test_search_space(async_session: AsyncSession, test_user: User):
    """Create a test search space"""
    from app.db import SearchSpace

    search_space = SearchSpace(
        name="Test Search Space",
        description="A test search space",
        user_id=test_user.id,
    )
    async_session.add(search_space)
    await async_session.commit()
    await async_session.refresh(search_space)
    return search_space


@pytest_asyncio.fixture(scope="function")
async def test_document(async_session: AsyncSession, test_search_space):
    """Create a test document"""
    from app.db import Document
    import numpy as np

    document = Document(
        title="Test Document",
        content="This is test content for studying",
        content_hash="test_hash_123",
        unique_identifier_hash="test_unique_123",
        embedding=np.zeros(384).tolist(),  # Assuming 384-dim embeddings
        search_space_id=test_search_space.id,
        document_type="FILE",
    )
    async_session.add(document)
    await async_session.commit()
    await async_session.refresh(document)
    return document


@pytest_asyncio.fixture(scope="function")
async def test_chat(async_session: AsyncSession, test_search_space):
    """Create a test chat"""
    from app.db import Chat, ChatType

    chat = Chat(
        search_space_id=test_search_space.id,
        type=ChatType.QNA,
        title="AI Discussion",
        messages=[
            {"role": "user", "content": "What is AI?"},
            {"role": "assistant", "content": "AI stands for Artificial Intelligence..."}
        ],
    )
    async_session.add(chat)
    await async_session.commit()
    await async_session.refresh(chat)
    return chat


# Auth mock helpers
@pytest.fixture
def mock_current_user(test_user):
    """Mock the current_active_user dependency"""
    from app.users import current_active_user

    async def _mock_current_user():
        return test_user

    app.dependency_overrides[current_active_user] = _mock_current_user
    yield test_user
    app.dependency_overrides.clear()
