"""
Basic tests for schema validation.

These tests verify empty payload rejection, successful parsing,
and generic read payload validation rules.
"""

from pydantic import ValidationError
import pytest

from app.models.schemas import GenericReadRequest, IngestionRequest


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


def test_generic_read_schema_accepts_alias_contract() -> None:
    payload = GenericReadRequest(
        Table_Name="teams",
        LastUpdatedDateStart="2026-01-01T00:00:00Z",
        LastUpdatedDateEnd="2026-01-31T00:00:00Z",
        RecordID=10,
    )
    assert payload.table_name == "teams"
    assert payload.record_id == 10


def test_generic_read_schema_rejects_invalid_date_range() -> None:
    with pytest.raises(ValidationError):
        GenericReadRequest(
            Table_Name="teams",
            CreatedDateStart="2026-02-01T00:00:00Z",
            CreatedDateEnd="2026-01-01T00:00:00Z",
        )
