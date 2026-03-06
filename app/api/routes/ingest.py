"""
Ingestion API routes.

These endpoints are designed for external systems and ingestion clients.
"""

# ===============================
# THIRD-PARTY IMPORTS
# ===============================
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

# ===============================
# LOCAL IMPORTS
# ===============================
from app.api.deps import get_authenticated_context
from app.core.database import get_db_session
from app.core.security import AuthContext
from app.models.schemas import IngestionRequest, IngestionResponse
from app.services.ingestion_service import ingest_raw_events
from app.services.processing_service import process_team_events

router = APIRouter(prefix="/ingest", tags=["ingestion"])


@router.post("", response_model=IngestionResponse)
def ingest_data(
    payload: IngestionRequest,
    auth: AuthContext = Depends(get_authenticated_context),
    db: Session = Depends(get_db_session),
) -> IngestionResponse:
    """
    Receives ingestion payload and writes to raw append-only table.

    Additional behavior for prototype:
    - Immediately triggers processing of team_view to demonstrate end-to-end flow.
    - In production, this processing call should move to async worker/queue.
    """

    inserted_count = ingest_raw_events(db=db, auth=auth, payload=payload)

    # ===============================
    # OPTIONAL SYNCHRONOUS PROCESSING SECTION
    # ===============================
    # Comment out this block if you want ingestion to stay strictly raw-only
    # and run processing from a scheduler/worker process instead.
    if payload.ViewName == "team_view":
        process_team_events(db=db, tenant_id=str(auth.tenant_id))

    return IngestionResponse(status="accepted", inserted_raw_count=inserted_count)
