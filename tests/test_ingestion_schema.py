"""
Basic tests for ingestion schema validation.

These tests verify empty payload rejection and successful parsing.
"""

import pytest
from pydantic import ValidationError

from app.models.schemas import IngestionRequest


def test_ingestion_schema_accepts_valid_payload() -> None:
    payload = IngestionRequest(
        ViewName="team_view",
        Database="core",
        ETLData=[{"teamId": 1, "teamName": "Admin"}],
    )
    assert payload.ViewName == "team_view"
    assert len(payload.ETLData) == 1


def test_ingestion_schema_rejects_empty_etldata() -> None:
    with pytest.raises(ValidationError):
        IngestionRequest(ViewName="team_view", Database="core", ETLData=[])
