"""
Read service that calls stored procedures for tenant-scoped data access.

Important rule: API never exposes direct table reads for UI consumption.
"""

# ===============================
# THIRD-PARTY IMPORTS
# ===============================
from sqlalchemy import text
from sqlalchemy.orm import Session


def get_teams_for_tenant(db: Session, tenant_id: str) -> list[dict]:
    """
    Calls `core.sp_get_teams` stored procedure.

    Security reasoning:
    - tenant_id is mandatory input.
    - stored procedure also enforces tenant filtering in DB layer.
    """

    query = text("SELECT * FROM core.sp_get_teams(:tenant_id)")
    rows = db.execute(query, {"tenant_id": tenant_id}).mappings().all()
    return [dict(row) for row in rows]
