import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# Import the app and database dependencies
from app.main import app
from app.database import get_db, Base
from app.redis_client import redis_client
from unittest.mock import AsyncMock


# --- 1. Sync Engine (Used ONLY for creating/dropping tables) ---
# This fixes the "MissingGreenlet" error by avoiding async drivers during setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

# --- 2. Async Engine (Used for the actual API tests) ---
ASYNC_SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
async_engine = create_async_engine(ASYNC_SQLALCHEMY_DATABASE_URL)
async_session = async_sessionmaker(bind=async_engine)

# --- 3. Dependency Override ---
# This replaces the app's database connection with our test connection
async def override_get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

# Apply the override so tests use our temporary database
app.dependency_overrides[get_db] = override_get_db

# --- 4. Mock Redis ---
@pytest.fixture(autouse=True)
def mock_redis(monkeypatch):
    mock = AsyncMock()
    # Mock basic redis methods
    mock.get.return_value = None
    mock.set.return_value = True
    mock.setex.return_value = True
    mock.delete.return_value = True
    mock.keys.return_value = []
    
    # Monkeypatch the redis_client instance in app.redis_client
    import app.redis_client
    monkeypatch.setattr(app.redis_client, "redis_client", mock)
    return mock

# --- 4. Fixtures ---

@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test, drop after"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="session")
def client():
    """Yields the TestClient for the FastAPI app"""
    with TestClient(app) as c:
        yield c

@pytest.fixture
def admin_token(client):
    """Creates an admin user and returns their JWT token"""
    email = "admin_test@example.com"
    # Register
    client.post("/auth/register", json={"email": email, "password": "password", "role": "admin"})
    # Login
    response = client.post("/auth/login", json={"email": email, "password": "password"})
    return response.json()["access_token"]

@pytest.fixture
def member_token(client):
    """Creates a member user and returns their JWT token"""
    email = "member_test@example.com"
    # Register
    client.post("/auth/register", json={"email": email, "password": "password", "role": "member"})
    # Login
    response = client.post("/auth/login", json={"email": email, "password": "password"})
    return response.json()["access_token"]