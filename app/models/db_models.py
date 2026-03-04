"""
SQLAlchemy ORM models for key tables.

Even though reads use stored procedures, models are still useful for inserts,
metadata generation, and future migrations.
"""

# ===============================
# THIRD-PARTY IMPORTS
# ===============================
from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""


class RawIngestionEvent(Base):
    """
    Append-only raw ingestion table.

    Architectural reason:
    - Raw zone preserves source payloads for replay/debug/compliance.
    - JSONB enables schema-flexible ingestion from many external providers.
    """

    __tablename__ = "ingestion_events"
    __table_args__ = {"schema": "raw"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    view_name: Mapped[str] = mapped_column(String(100), nullable=False)
    database_name: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )


class CuratedTeam(Base):
    """
    Curated structured table consumed by downstream reads.

    Tenant-specific uniqueness prevents cross-tenant collisions while allowing
    same external IDs to appear in different tenants.
    """

    __tablename__ = "teams"
    __table_args__ = {"schema": "core"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    team_id: Mapped[int] = mapped_column(Integer, nullable=False)
    team_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ApiKey(Base):
    """
    API key metadata table used to authorize ingestion clients.

    Security decisions:
    - `can_ingest` scope limits key capability.
    - `is_active` supports immediate key revocation.
    """

    __tablename__ = "api_keys"
    __table_args__ = {"schema": "auth"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    api_key: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="INGESTION_CLIENT")
    can_ingest: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
