"""
Main FastAPI application entrypoint.

This service exposes ingestion and read endpoints for a multi-tenant data platform.
"""

# ===============================
# THIRD-PARTY IMPORTS
# ===============================
from fastapi import FastAPI

# ===============================
# LOCAL IMPORTS
# ===============================
from app.api.routes.ingest import router as ingest_router
from app.api.routes.read import router as read_router


app = FastAPI(
    title="Multi-Tenant Data Ingestion Platform",
    description="Lightweight SaaS-ready backend using FastAPI + PostgreSQL",
    version="0.1.0",
)


# ===============================
# ROUTE REGISTRATION
# ===============================
app.include_router(ingest_router)
app.include_router(read_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Simple health endpoint for local/devops checks."""

    return {"status": "ok"}
