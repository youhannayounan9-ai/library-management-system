import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.database import Base, get_db
from unittest.mock import AsyncMock, patch
from app.models.user import User
from app.models.book import Book

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class AsyncSessionWrapper:
    def __init__(self, sync_session):
        self.sync_session = sync_session

    async def execute(self, *args, **kwargs):
        return self.sync_session.execute(*args, **kwargs)

    async def commit(self):
        self.sync_session.commit()

    async def rollback(self):
        self.sync_session.rollback()

    async def refresh(self, instance):
        self.sync_session.refresh(instance)

    async def get(self, *args, **kwargs):
        return self.sync_session.get(*args, **kwargs)

    def add(self, instance):
        self.sync_session.add(instance)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield AsyncSessionWrapper(db)
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session", autouse=True)
def create_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="session")
def client():
    return TestClient(app)

@pytest.fixture(autouse=True)
def mock_redis():
    # Prevents "RuntimeError: Event loop is closed" by intercepting Redis calls on the global client
    with patch("app.redis_client.redis_client.get", new_callable=AsyncMock, return_value=None), \
         patch("app.redis_client.redis_client.setex", new_callable=AsyncMock), \
         patch("app.redis_client.redis_client.delete", new_callable=AsyncMock), \
         patch("app.redis_client.redis_client.ping", new_callable=AsyncMock, return_value=True):
        yield

@pytest.fixture(scope="session")
def admin_token(client):
    client.post("/auth/register", json={"email": "admin@test.com", "password": "admin123", "role": "admin"})
    res = client.post("/auth/login", json={"email": "admin@test.com", "password": "admin123"})
    return res.json()["access_token"]

@pytest.fixture(scope="session")
def member_token(client):
    client.post("/auth/register", json={"email": "member@test.com", "password": "member123", "role": "member"})
    res = client.post("/auth/login", json={"email": "member@test.com", "password": "member123"})
    return res.json()["access_token"]