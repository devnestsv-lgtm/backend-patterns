"""
Pydantic request/response schemas.

These schemas validate ingestion payload structure and response contracts,
preventing malformed data from reaching persistence layers.
"""

# ===============================
# STANDARD LIBRARY IMPORTS
# ===============================
from typing import Any

# ===============================
# THIRD-PARTY IMPORTS
# ===============================
from pydantic import BaseModel, Field, field_validator


class IngestionRequest(BaseModel):
    """
    Payload received from external ingestion clients.

    Validation goals:
    - Ensure expected contract keys exist.
    - Keep ETLData flexible as list[dict[str, Any]] for heterogeneous sources.
    - Reject empty batches.
    """

    ViewName: str = Field(..., description="Logical target name, e.g. team_view")
    Database: str = Field(..., description="Logical database/schema alias, e.g. core")
    ETLData: list[dict[str, Any]] = Field(
        ..., description="Flexible event list from source systems"
    )

    @field_validator("ETLData")
    @classmethod
    def validate_non_empty_batch(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Rejects ingestion requests that contain zero records."""

        if len(value) == 0:
            raise ValueError("ETLData must contain at least one record")
        return value


class IngestionResponse(BaseModel):
    """Response for ingestion requests."""

    status: str
    inserted_raw_count: int


class TeamReadResponse(BaseModel):
    """Read response model for curated team records."""

    team_id: int
    team_name: str
