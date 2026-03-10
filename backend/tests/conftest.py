import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.session import Base, get_db
from app.main import app
from app.services.repository import seed_data


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        seed_data(db)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    old_auto_create = settings.auto_create_tables
    old_bootstrap = settings.bootstrap_demo_data
    settings.auto_create_tables = False
    settings.bootstrap_demo_data = False
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        settings.auto_create_tables = old_auto_create
        settings.bootstrap_demo_data = old_bootstrap
        app.dependency_overrides.clear()
        engine.dispose()
