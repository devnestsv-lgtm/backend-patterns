-- =====================================================
-- MULTI-TENANT DATA PLATFORM INITIAL DATABASE SETUP
-- =====================================================
-- This script creates schemas, raw/curated tables, auth tables, indexes,
-- and stored procedures used by the Python API.

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
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, team_id)
);

CREATE INDEX IF NOT EXISTS idx_core_teams_tenant ON core.teams (tenant_id);
CREATE INDEX IF NOT EXISTS idx_core_teams_updated ON core.teams (tenant_id, updated_at);
CREATE INDEX IF NOT EXISTS idx_core_teams_created ON core.teams (tenant_id, created_at);

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
-- GENERIC READ STORED PROCEDURE
-- ===============================
-- This procedure avoids free-form SQL table injection by branching explicitly
-- on supported table names.
CREATE OR REPLACE FUNCTION core.sp_read_records(
    p_tenant_id UUID,
    p_table_name TEXT,
    p_last_updated_start TIMESTAMPTZ DEFAULT NULL,
    p_last_updated_end TIMESTAMPTZ DEFAULT NULL,
    p_created_start TIMESTAMPTZ DEFAULT NULL,
    p_created_end TIMESTAMPTZ DEFAULT NULL,
    p_record_id INTEGER DEFAULT NULL
)
RETURNS TABLE(record_id INTEGER, record_name TEXT, created_at TIMESTAMPTZ, updated_at TIMESTAMPTZ)
LANGUAGE plpgsql
AS $$
BEGIN
    -- Explicitly allow listed curated tables only.
    IF p_table_name = 'teams' THEN
        RETURN QUERY
        SELECT
            t.team_id AS record_id,
            t.team_name AS record_name,
            t.created_at,
            t.updated_at
        FROM core.teams t
        WHERE t.tenant_id = p_tenant_id
          AND (p_record_id IS NULL OR t.team_id = p_record_id)
          AND (p_last_updated_start IS NULL OR t.updated_at >= p_last_updated_start)
          AND (p_last_updated_end IS NULL OR t.updated_at <= p_last_updated_end)
          AND (p_created_start IS NULL OR t.created_at >= p_created_start)
          AND (p_created_end IS NULL OR t.created_at <= p_created_end)
        ORDER BY t.team_id;
    ELSE
        RAISE EXCEPTION 'Unsupported table requested: %', p_table_name;
    END IF;
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
