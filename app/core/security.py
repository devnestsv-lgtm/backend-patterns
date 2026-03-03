"""
Authentication and authorization helpers.

This module supports:
1) JWT authentication for human users.
2) API key authentication for ingestion clients.

Important multi-tenant rule:
- tenant_id always comes from validated auth credentials, never from UI input.
"""

# ===============================
# STANDARD LIBRARY IMPORTS
# ===============================
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

# ===============================
# THIRD-PARTY IMPORTS
# ===============================
from fastapi import Depends, Header, HTTPException, status
from jose import jwt, JWTError
from sqlalchemy import text
from sqlalchemy.orm import Session

# ===============================
# LOCAL IMPORTS
# ===============================
from app.core.config import get_settings
from app.core.database import get_db_session

settings = get_settings()


@dataclass
class AuthContext:
    """
    Canonical authenticated context injected into endpoint handlers.

    Why this object exists:
    - Unifies JWT and API-key auth outputs.
    - Carries tenant_id and role to every service layer.
    """

    user_id: UUID
    tenant_id: UUID
    role: str
    auth_type: str


def decode_jwt_token(token: str) -> AuthContext:
    """
    Validates and decodes a JWT then maps it to AuthContext.

    Security reasoning:
    - Signature verification ensures the token was issued by trusted auth service.
    - tenant_id extracted from token enforces tenant isolation at Python layer.
    """

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid JWT token",
        ) from exc

    required = ["user_id", "tenant_id", "role"]
    if any(key not in payload for key in required):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="JWT missing required claims",
        )

    return AuthContext(
        user_id=UUID(payload["user_id"]),
        tenant_id=UUID(payload["tenant_id"]),
        role=payload["role"],
        auth_type="jwt",
    )


def authenticate_ingestion_api_key(db: Session, api_key: str) -> AuthContext:
    """
    Authenticates ingestion API keys and returns tenant-scoped context.

    Security reasoning:
    - API keys are limited to ingestion use-cases.
    - Key metadata table stores tenant mapping and permission scope.
    """

    query = text(
        """
        SELECT tenant_id, role
        FROM auth.api_keys
        WHERE api_key = :api_key
          AND is_active = TRUE
          AND can_ingest = TRUE
        """
    )
    row = db.execute(query, {"api_key": api_key}).mappings().first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or unauthorized API key",
        )

    return AuthContext(
        user_id=UUID("00000000-0000-0000-0000-000000000000"),
        tenant_id=row["tenant_id"],
        role=row["role"],
        auth_type="api_key",
    )


def get_auth_context(
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(default=None),
    x_api_key: Optional[str] = Header(default=None),
) -> AuthContext:
    """
    Resolves auth context from either JWT or API key.

    Local development note:
    - Optional JWT bypass can be enabled for rapid local testing.
    - This block is clearly isolated and can be commented out when not needed.
    """

    # ===============================
    # LOCAL DEVELOPMENT ONLY SECTION (OPTIONAL)
    # ===============================
    if settings.ENABLE_LOCAL_JWT_BYPASS and not authorization and not x_api_key:
        return AuthContext(
            user_id=UUID(settings.LOCAL_TEST_USER_ID),
            tenant_id=UUID(settings.LOCAL_TEST_TENANT_ID),
            role=settings.LOCAL_TEST_ROLE,
            auth_type="local_bypass",
        )

    if x_api_key:
        return authenticate_ingestion_api_key(db, x_api_key)

    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", maxsplit=1)[1]
        return decode_jwt_token(token)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing authentication credentials",
    )
