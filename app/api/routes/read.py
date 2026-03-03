"""
Read API routes.

These endpoints are intended for UI/backend consumer access and always use
stored procedures (not direct table select statements).
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
from app.models.schemas import TeamReadResponse
from app.services.read_service import get_teams_for_tenant

router = APIRouter(prefix="/teams", tags=["read"])


@router.get("", response_model=list[TeamReadResponse])
def list_teams(
    auth: AuthContext = Depends(get_authenticated_context),
    db: Session = Depends(get_db_session),
) -> list[TeamReadResponse]:
    """
    Returns curated team records for the authenticated tenant.

    Tenant enforcement:
    - tenant_id derived from auth context.
    - tenant_id passed to stored procedure parameter.
    """

    rows = get_teams_for_tenant(db=db, tenant_id=str(auth.tenant_id))
    return [TeamReadResponse(**row) for row in rows]
