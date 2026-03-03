"""
FastAPI dependency wrappers.

This module composes authentication and DB dependencies into reusable helpers
for route handlers.
"""

# ===============================
# THIRD-PARTY IMPORTS
# ===============================
from fastapi import Depends

# ===============================
# LOCAL IMPORTS
# ===============================
from app.core.security import get_auth_context, AuthContext


def get_authenticated_context(
    auth_context: AuthContext = Depends(get_auth_context),
) -> AuthContext:
    """
    Injects authenticated context for endpoints.

    Design reasoning:
    - Keeps route functions clean.
    - Ensures all protected routes share same auth logic.
    """

    return auth_context
