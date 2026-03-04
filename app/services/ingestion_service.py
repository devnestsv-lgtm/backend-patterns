"""
Service layer for ingestion workflow.

This module validates domain-level ingestion constraints and writes raw events
using only parameterized SQLAlchemy operations.
"""

# ===============================
# THIRD-PARTY IMPORTS
# ===============================
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

# ===============================
# LOCAL IMPORTS
# ===============================
from app.core.config import get_settings
from app.core.security import AuthContext
from app.models.db_models import RawIngestionEvent
from app.models.schemas import IngestionRequest

settings = get_settings()


def ingest_raw_events(db: Session, auth: AuthContext, payload: IngestionRequest) -> int:
    """
    Inserts ingestion data into append-only raw table.

    Multi-tenant security reasoning:
    - tenant_id is sourced from auth context, never from request body.
    - Each raw row is tagged with tenant_id for downstream isolation.
    """

    if payload.ViewName not in settings.ALLOWED_VIEW_NAMES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported ViewName: {payload.ViewName}",
        )

    if payload.Database not in settings.ALLOWED_DATABASE_NAMES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported Database: {payload.Database}",
        )

    batch_size = len(payload.ETLData)
    if batch_size > settings.MAX_INGEST_BATCH_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Batch too large. Max allowed: {settings.MAX_INGEST_BATCH_SIZE}",
        )

    raw_rows = [
        RawIngestionEvent(
            tenant_id=auth.tenant_id,
            source="external_service",
            view_name=payload.ViewName,
            database_name=payload.Database,
            payload=item,
        )
        for item in payload.ETLData
    ]

    db.add_all(raw_rows)
    db.commit()

    return len(raw_rows)
