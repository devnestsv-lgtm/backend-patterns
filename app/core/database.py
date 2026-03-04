"""
Database connectivity and session lifecycle utilities.

This file intentionally keeps connection logic in one place so repository/service
layers can depend on a consistent SQLAlchemy session pattern.
"""

# ===============================
# THIRD-PARTY IMPORTS
# ===============================
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# ===============================
# LOCAL IMPORTS
# ===============================
from app.core.config import get_settings

settings = get_settings()

# SQLAlchemy engine configured for PostgreSQL.
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# Session factory used by FastAPI dependencies.
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


# ===============================
# FASTAPI DEPENDENCY
# ===============================
def get_db_session() -> Session:
    """
    Yields a transactional database session per request.

    Security/consistency reasoning:
    - Every request has isolated DB state.
    - Session is always closed to prevent connection leaks.
    """

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
