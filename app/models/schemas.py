"""
Pydantic request/response schemas.

These schemas validate ingestion payload structure and response contracts,
preventing malformed data from reaching persistence layers.
"""

# ===============================
# STANDARD LIBRARY IMPORTS
# ===============================
from datetime import datetime
from typing import Any, Optional

# ===============================
# THIRD-PARTY IMPORTS
# ===============================
from pydantic import BaseModel, Field, field_validator, model_validator


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


class GenericReadRequest(BaseModel):
    """
    Generic read request body used by POST /read/query.

    Important tenant isolation rule:
    - `tenant_id` is optional for auditing/debug compatibility, but is ignored for
      standard users and must match authenticated tenant if provided.
    """

    tenant_id: Optional[str] = Field(default=None, alias="Tenant_ID")
    table_name: str = Field(..., alias="Table_Name")

    last_updated_start: Optional[datetime] = Field(default=None, alias="LastUpdatedDateStart")
    last_updated_end: Optional[datetime] = Field(default=None, alias="LastUpdatedDateEnd")

    created_start: Optional[datetime] = Field(default=None, alias="CreatedDateStart")
    created_end: Optional[datetime] = Field(default=None, alias="CreatedDateEnd")

    record_id: Optional[int] = Field(default=None, alias="RecordID")

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def validate_date_ranges(self) -> "GenericReadRequest":
        """Ensures date start/end ranges are coherent when both values are supplied."""

        if self.last_updated_start and self.last_updated_end:
            if self.last_updated_start > self.last_updated_end:
                raise ValueError("LastUpdatedDateStart must be <= LastUpdatedDateEnd")

        if self.created_start and self.created_end:
            if self.created_start > self.created_end:
                raise ValueError("CreatedDateStart must be <= CreatedDateEnd")

        return self


class GenericReadResponseRow(BaseModel):
    """Generic row response for dynamic curated-table reads."""

    record_id: int
    record_name: str
    created_at: datetime
    updated_at: datetime
