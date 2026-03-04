# Multi-Tenant Data Ingestion and Processing Platform (Prototype)

This repository contains a **working local prototype** of a lightweight SaaS-ready internal data platform built with FastAPI + PostgreSQL.

## Architecture Goals Implemented

- Multi-tenant data model in one PostgreSQL database (`tenant_id` on business tables).
- Ingestion endpoint accepting flexible ETL payloads and writing to raw append-only JSONB tables.
- Processing step from raw to curated/core structured tables.
- Read path exposed only via Python API calling generic stored procedures.
- JWT/API key auth model with tenant extraction and tenant-scoped access.
- Retention cleanup mechanism for raw data.

---

## Proposed Folder Structure

```text
app/
  api/
    deps.py                 # Shared FastAPI dependencies (auth context injection)
    routes/
      ingest.py             # POST /ingest endpoint
      read.py               # POST /read/query endpoint (stored-procedure backed)
  core/
    config.py               # Environment-driven settings
    database.py             # SQLAlchemy engine/session lifecycle
    security.py             # JWT and API key auth logic
  db/
    sql/
      001_init.sql          # SQL setup script: schemas, tables, indexes, SPs
  models/
    db_models.py            # ORM models for raw/curated/auth tables
    schemas.py              # Pydantic request/response models
  services/
    ingestion_service.py    # Raw ingestion workflow and validation
    processing_service.py   # Raw -> curated transformation logic
    read_service.py         # Stored-procedure calls for read layer
scripts/
  retention_cleanup.py      # Raw retention cleanup CLI script
tests/
  test_ingestion_schema.py  # Schema validation test
```

---

## Authentication and Authorization Concept

### Human user flow (JWT)
- UI calls API with `Authorization: Bearer <jwt>`.
- API validates signature and extracts `tenant_id`, `user_id`, `role`.
- Handlers/services always use tenant_id from auth context.

### Ingestion client flow (API key)
- External service calls ingestion endpoint with `X-API-Key`.
- API key is looked up in `auth.api_keys` with `can_ingest = true` and `is_active = true`.
- Key is mapped to a tenant and role (`INGESTION_CLIENT`).

### RBAC Roles
- `SUPER_ADMIN`, `ADMIN`, `ANALYST`, `CUSTOMER`, `INGESTION_CLIENT`
- Prototype includes role field propagation; add route-level role guards as your next extension.

---

## Tenant Isolation Enforcement

### Python layer
- `tenant_id` is never accepted from UI/client body payload.
- It is extracted from JWT/API key into `AuthContext` and used for all data operations.

### Stored procedure layer
- Stored procedures require `tenant_id` argument (e.g., `core.sp_read_records(...)`).
- Procedure SQL always filters by `tenant_id`.

---

## Ingestion Payload Contract

```json
{
  "ViewName": "team_view",
  "Database": "core",
  "ETLData": [
    { "teamId": 12345, "teamName": "Admin1" },
    { "teamId": 123456, "teamName": "Admin2" },
    { "teamId": 1234567, "teamName": "Admin3" }
  ]
}
```

Validation performed:
- `ViewName` allowed list check.
- `Database` allowed list check.
- `ETLData` cannot be empty.
- Batch size max enforced (`MAX_INGEST_BATCH_SIZE`).

No dynamic SQL string concatenation is used.


## Generic Read Payload Contract

```json
{
  "Tenant_ID": "optional-uuid-for-audit-only",
  "Table_Name": "teams",
  "LastUpdatedDateStart": "2026-01-01T00:00:00Z",
  "LastUpdatedDateEnd": "2026-12-31T23:59:59Z",
  "CreatedDateStart": "2026-01-01T00:00:00Z",
  "CreatedDateEnd": "2026-12-31T23:59:59Z",
  "RecordID": 12345
}
```

Notes:
- `Tenant_ID` is optional and must match auth tenant if supplied.
- Tenant filtering is enforced using auth-derived tenant_id, not payload trust.
- `Table_Name` is allow-listed inside the stored procedure to avoid dynamic SQL injection.

---

---

# HOW TO TEST LOCALLY

This section is intentionally command-by-command so you can copy/paste without guessing.

## 0) Prerequisites

- Python 3.10+
- Docker (recommended for local PostgreSQL)
- `psql` client installed locally
- Two terminals (one for API server, one for curl/tests)

## 1) Start PostgreSQL container

```bash
docker rm -f backend-patterns-pg 2>/dev/null || true
docker run --name backend-patterns-pg \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=backend_patterns \
  -p 5432:5432 -d postgres:16
```

Wait for PostgreSQL to become healthy:

```bash
docker logs -f backend-patterns-pg
```

When you see `database system is ready to accept connections`, stop following logs (`Ctrl+C`).

## 2) Create virtual environment and install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 3) (Optional but recommended) create `.env` for local settings

```bash
cat > .env <<'EOF'
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/backend_patterns
JWT_SECRET_KEY=change-me-in-real-env
JWT_ALGORITHM=HS256
ENABLE_LOCAL_JWT_BYPASS=true
LOCAL_TEST_TENANT_ID=00000000-0000-0000-0000-000000000001
LOCAL_TEST_USER_ID=00000000-0000-0000-0000-000000000002
LOCAL_TEST_ROLE=ADMIN
MAX_INGEST_BATCH_SIZE=1000
ALLOWED_VIEW_NAMES=["team_view"]
ALLOWED_DATABASE_NAMES=["core"]
ALLOWED_READ_TABLE_NAMES=["teams"]
EOF
```

## 4) Initialize database schemas, tables, and stored procedures

```bash
psql postgresql://postgres:postgres@localhost:5432/backend_patterns -f app/db/sql/001_init.sql
```

Quick check that required schemas exist:

```bash
psql postgresql://postgres:postgres@localhost:5432/backend_patterns -c "\dn"
```

You should see `auth`, `raw`, `core`, and `analytics`.

## 5) Insert local ingestion API key for test tenant

```bash
psql postgresql://postgres:postgres@localhost:5432/backend_patterns <<'SQL'
INSERT INTO auth.api_keys (tenant_id, api_key, role, can_ingest, is_active)
VALUES ('00000000-0000-0000-0000-000000000001', 'local-dev-api-key', 'INGESTION_CLIENT', TRUE, TRUE)
ON CONFLICT (api_key) DO NOTHING;
SQL
```

## 6) Start FastAPI (Terminal A)

```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```

Health check from Terminal B:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok"}
```

## 7) Call ingestion endpoint (Terminal B)

```bash
curl -X POST http://127.0.0.1:8000/ingest \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: local-dev-api-key' \
  -d '{
    "ViewName": "team_view",
    "Database": "core",
    "ETLData": [
      {"teamId": 12345, "teamName": "Admin1"},
      {"teamId": 123456, "teamName": "Admin2"}
    ]
  }'
```

Expected response shape:

```json
{"status":"accepted","inserted_raw_count":2}
```

## 8) Query curated data via generic read endpoint (Terminal B)

```bash
curl -X POST http://127.0.0.1:8000/read/query \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: local-dev-api-key' \
  -d '{
    "Table_Name": "teams",
    "CreatedDateStart": "2020-01-01T00:00:00Z",
    "CreatedDateEnd": "2030-01-01T00:00:00Z"
  }'
```

Expected response: JSON array of tenant-scoped records with fields:
- `record_id`
- `record_name`
- `created_at`
- `updated_at`

## 9) Run retention cleanup example

```bash
source .venv/bin/activate
python scripts/retention_cleanup.py --days 60
```

## 10) Troubleshooting quick checks

- If API cannot connect to DB, verify container is running:
  ```bash
  docker ps
  ```
- If read endpoint returns `Unsupported Table_Name`, verify payload uses:
  ```json
  {"Table_Name":"teams"}
  ```
- If auth fails, verify API key exists:
  ```bash
  psql postgresql://postgres:postgres@localhost:5432/backend_patterns -c "SELECT tenant_id, api_key, is_active, can_ingest FROM auth.api_keys;"
  ```
- If you want to temporarily bypass JWT/API-key for local dev, use the clearly marked optional block in `app/core/security.py` (`ENABLE_LOCAL_JWT_BYPASS=true`).

---

## Local Testing Optional Toggle Sections

The code includes clearly labeled optional blocks that can be disabled by commenting:
- Local JWT bypass in `app/core/security.py`.
- Optional synchronous processing call in `app/api/routes/ingest.py`.
- Optional local API key seed SQL in `app/db/sql/001_init.sql`.

