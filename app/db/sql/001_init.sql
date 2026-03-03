-- =====================================================
-- MULTI-TENANT DATA PLATFORM INITIAL DATABASE SETUP
-- =====================================================
-- This script creates schemas, raw/curated tables, auth tables, indexes,
-- and a read-only stored procedure used by the Python API.

-- ===============================
-- SCHEMA CREATION
-- ===============================
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS analytics;

-- ===============================
-- AUTH TABLE FOR API KEYS
-- ===============================
CREATE TABLE IF NOT EXISTS auth.api_keys (
    id BIGSERIAL PRIMARY KEY,
    tenant_id UUID NOT NULL,
    api_key TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL DEFAULT 'INGESTION_CLIENT',
    can_ingest BOOLEAN NOT NULL DEFAULT TRUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ===============================
-- RAW APPEND-ONLY INGESTION TABLE
-- ===============================
-- Partitioned by created_at to support high-volume retention/deletion.
CREATE TABLE IF NOT EXISTS raw.ingestion_events (
    id BIGSERIAL,
    tenant_id UUID NOT NULL,
    source TEXT NOT NULL,
    view_name TEXT NOT NULL,
    database_name TEXT NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- Example monthly partition for local use.
CREATE TABLE IF NOT EXISTS raw.ingestion_events_2026_01
    PARTITION OF raw.ingestion_events
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

CREATE INDEX IF NOT EXISTS idx_raw_ingestion_tenant_created
    ON raw.ingestion_events (tenant_id, created_at);

-- ===============================
-- CURATED CORE TABLE
-- ===============================
CREATE TABLE IF NOT EXISTS core.teams (
    id BIGSERIAL PRIMARY KEY,
    tenant_id UUID NOT NULL,
    team_id INTEGER NOT NULL,
    team_name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, team_id)
);

CREATE INDEX IF NOT EXISTS idx_core_teams_tenant ON core.teams (tenant_id);

-- ===============================
-- ANALYTICS EXAMPLE TABLE
-- ===============================
CREATE TABLE IF NOT EXISTS analytics.team_counts_daily (
    tenant_id UUID NOT NULL,
    event_date DATE NOT NULL,
    team_count INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, event_date)
);

-- ===============================
-- STORED PROCEDURE (READ LAYER)
-- ===============================
-- SECURITY DEFINER is intentionally NOT used in this prototype.
-- The API calls this function with explicit tenant_id.
CREATE OR REPLACE FUNCTION core.sp_get_teams(p_tenant_id UUID)
RETURNS TABLE(team_id INTEGER, team_name TEXT)
LANGUAGE plpgsql
AS $$
BEGIN
    -- Explicit tenant filter to enforce isolation in DB read layer.
    RETURN QUERY
    SELECT t.team_id, t.team_name
    FROM core.teams t
    WHERE t.tenant_id = p_tenant_id
    ORDER BY t.team_id;
END;
$$;

-- ===============================
-- OPTIONAL LOCAL TEST SEED SECTION
-- ===============================
-- Uncomment for local testing convenience.
-- INSERT INTO auth.api_keys (tenant_id, api_key, role, can_ingest, is_active)
-- VALUES
-- ('00000000-0000-0000-0000-000000000001', 'local-dev-api-key', 'INGESTION_CLIENT', TRUE, TRUE)
-- ON CONFLICT (api_key) DO NOTHING;
