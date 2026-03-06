"""
Read service that calls stored procedures for tenant-scoped data access.

Important rule: API never exposes direct table reads for UI consumption.
"""

# ===============================
# THIRD-PARTY IMPORTS
# ===============================
from sqlalchemy import text
from sqlalchemy.orm import Session

# ===============================
# LOCAL IMPORTS
# ===============================
from app.models.schemas import GenericReadRequest


def get_records_for_tenant(db: Session, tenant_id: str, payload: GenericReadRequest) -> list[dict]:
    """
    Calls tenant-scoped generic stored procedure `core.sp_read_records`.

    Security reasoning:
    - tenant_id is mandatory input sourced from authentication.
    - table_name is handled inside the stored procedure and constrained by DB logic.
    - date/range filters are passed as typed parameters (no dynamic query concat in API).
    """

    query = text(
        """
        SELECT *
        FROM core.sp_read_records(
            :tenant_id,
            :table_name,
            :last_updated_start,
            :last_updated_end,
            :created_start,
            :created_end,
            :record_id
        )
        """
    )

    rows = db.execute(
        query,
        {
            "tenant_id": tenant_id,
            "table_name": payload.table_name,
            "last_updated_start": payload.last_updated_start,
            "last_updated_end": payload.last_updated_end,
            "created_start": payload.created_start,
            "created_end": payload.created_end,
            "record_id": payload.record_id,
        },
    ).mappings().all()
    return [dict(row) for row in rows]
