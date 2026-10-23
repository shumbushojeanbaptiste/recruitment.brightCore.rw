import os

import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# The application is imported below and loads settings at module import time.
os.environ.setdefault("DATABASE_URL", "sqlite:///./test-bootstrap.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("JWT_SECRET_KEY", "test-only-secret-not-for-production")

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app import models  # Ensure every model is registered with Base.metadata


class FakeRedis:
    def __init__(self):
        self.counts: dict[str, int] = {}

    async def eval(
        self,
        _script: str,
        _numkeys: int,
        key: str,
        window_seconds: int,
    ) -> tuple[int, int]:
        count = self.counts.get(key, 0) + 1
        self.counts[key] = count
        return count, window_seconds


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    previous_redis = getattr(app.state, "redis", None)
    app.state.redis = FakeRedis()
    app.dependency_overrides[get_db] = override_get_db

    # Not using the TestClient context manager avoids starting application
    # lifespan services for these isolated API tests.
    test_client = TestClient(app)

    yield test_client

    app.dependency_overrides.clear()
    test_client.close()
    if previous_redis is None:
        del app.state.redis
    else:
        app.state.redis = previous_redis
