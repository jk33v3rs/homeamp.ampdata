"""HomeAMP V2.0 - Database connection and session management."""

from contextlib import contextmanager
from typing import Generator

from homeamp_v2.core.config import get_settings
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

# SQLAlchemy Base for models
Base = declarative_base()

# Global engine and session factory (initialized on first use)
_engine: Engine | None = None
_SessionLocal: sessionmaker | None = None


def get_engine() -> Engine:
    """Get or create SQLAlchemy engine with connection pooling."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(
            settings.database_url,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_pre_ping=True,
            echo=settings.database_echo,
        )
        # Set charset to utf8mb4 for MariaDB
        @event.listens_for(_engine, "connect")
        def set_charset(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("SET NAMES utf8mb4")
            cursor.close()

    return _engine


def get_session_factory() -> sessionmaker:
    """Get or create session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _SessionLocal


def get_session() -> Generator[Session, None, None]:
    """Dependency injection for FastAPI routes - yields a database session."""
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Context manager for database sessions with automatic commit/rollback."""
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Initialize database - create all tables."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
