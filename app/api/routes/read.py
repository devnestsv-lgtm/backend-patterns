"""
Generic read API routes.

These endpoints are intended for UI/backend consumer access and always use
stored procedures (not direct table select statements).
"""

# ===============================
# THIRD-PARTY IMPORTS
# ===============================
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# ===============================
# LOCAL IMPORTS
# ===============================
from app.api.deps import get_authenticated_context
from app.core.config import get_settings
from app.core.database import get_db_session
from app.core.security import AuthContext
from app.models.schemas import GenericReadRequest, GenericReadResponseRow
from app.services.read_service import get_records_for_tenant

router = APIRouter(prefix="/read", tags=["read"])
settings = get_settings()


@router.post("/query", response_model=list[GenericReadResponseRow])
def query_curated_data(
    payload: GenericReadRequest,
    auth: AuthContext = Depends(get_authenticated_context),
    db: Session = Depends(get_db_session),
) -> list[GenericReadResponseRow]:
    """
    Returns tenant-scoped records from a caller-specified curated table.

    Tenant enforcement:
    - tenant_id is always sourced from auth context.
    - if Tenant_ID is supplied in payload, it must exactly match auth tenant.
    """

    if payload.table_name not in settings.ALLOWED_READ_TABLE_NAMES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported Table_Name: {payload.table_name}",
        )

    if payload.tenant_id and payload.tenant_id != str(auth.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant_ID does not match authenticated tenant context",
        )

    rows = get_records_for_tenant(db=db, tenant_id=str(auth.tenant_id), payload=payload)
    return [GenericReadResponseRow(**row) for row in rows]
