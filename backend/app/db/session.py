import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings


class Base(DeclarativeBase):
    pass


def _normalize_db_url(url: str) -> str:
    normalized = url.strip()
    if normalized.startswith("postgres://"):
        normalized = normalized.replace("postgres://", "postgresql://", 1)
    if normalized.startswith("postgresql://") and "sslmode=" not in normalized:
        sep = "&" if "?" in normalized else "?"
        normalized = f"{normalized}{sep}sslmode=require"
    return normalized


engine_kwargs = {"future": True, "pool_pre_ping": True}
if os.getenv("VERCEL") == "1":
    # Serverless: avoid long-lived pooled connections between invocations.
    engine_kwargs["poolclass"] = NullPool

engine = create_engine(_normalize_db_url(settings.db_url), **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
