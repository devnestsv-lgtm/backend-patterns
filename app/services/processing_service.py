"""
Service that processes raw events into curated core tables.

For the prototype, this supports team_view transformation logic.
In production, this would run asynchronously via worker/scheduler.
"""

# ===============================
# THIRD-PARTY IMPORTS
# ===============================
from sqlalchemy import text
from sqlalchemy.orm import Session


def process_team_events(db: Session, tenant_id: str) -> int:
    """
    Processes raw `team_view` events into `core.teams` table.

    Design decisions:
    - Uses SQL-side JSON extraction for performance and atomicity.
    - Applies tenant filter inside SQL to prevent cross-tenant processing.
    - Upserts by (tenant_id, team_id) to keep latest team name.
    """

    query = text(
        """
        INSERT INTO core.teams (tenant_id, team_id, team_name)
        SELECT
            r.tenant_id,
            (r.payload->>'teamId')::int AS team_id,
            r.payload->>'teamName' AS team_name
        FROM raw.ingestion_events r
        WHERE r.tenant_id = :tenant_id
          AND r.view_name = 'team_view'
          AND r.payload ? 'teamId'
          AND r.payload ? 'teamName'
        ON CONFLICT (tenant_id, team_id)
        DO UPDATE SET team_name = EXCLUDED.team_name
        """
    )

    result = db.execute(query, {"tenant_id": tenant_id})
    db.commit()
    return result.rowcount or 0
