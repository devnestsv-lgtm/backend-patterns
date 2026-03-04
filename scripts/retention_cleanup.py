"""
Retention cleanup script for raw ingestion data.

Usage:
    python scripts/retention_cleanup.py --days 60

This script deletes old raw events by timestamp. In high-volume systems, you can
replace row-level deletion with partition dropping for better performance.
"""

# ===============================
# STANDARD LIBRARY IMPORTS
# ===============================
import argparse
from datetime import datetime, timedelta, timezone

# ===============================
# THIRD-PARTY IMPORTS
# ===============================
from sqlalchemy import create_engine, text

# ===============================
# LOCAL IMPORTS
# ===============================
from app.core.config import get_settings


def run_retention(days: int) -> int:
    """
    Deletes raw rows older than configured retention threshold.

    Architectural note:
    - Keeps raw storage bounded and cost-controlled.
    - Should be scheduled via cron/Kubernetes/DigitalOcean jobs.
    """

    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    query = text(
        """
        DELETE FROM raw.ingestion_events
        WHERE created_at < :cutoff
        """
    )

    with engine.begin() as conn:
        result = conn.execute(query, {"cutoff": cutoff})

    return result.rowcount or 0


def main() -> None:
    """CLI entrypoint for local/manual retention execution."""

    parser = argparse.ArgumentParser(description="Raw data retention cleanup")
    parser.add_argument("--days", type=int, default=60, help="Retention window in days")
    args = parser.parse_args()

    deleted = run_retention(days=args.days)
    print(f"Deleted rows: {deleted}")


if __name__ == "__main__":
    main()
