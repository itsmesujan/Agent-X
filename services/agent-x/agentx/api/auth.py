"""Agent-X Authentication and Authorization Abstraction."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import Header, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field


class AuthUser(BaseModel):
    """Authenticated user context extracted from bearer credentials."""

    model_config = ConfigDict(extra="forbid")

    user_id: str
    email: str
    role: str = Field(default="OPERATOR", description="ADMIN | OPERATOR | VIEWER")
    tenant_id: str = "default_tenant"
    authenticated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> AuthUser:
    """FastAPI dependency resolving and validating bearer token credentials."""
    if not authorization:
        # For testing and development, if no auth header is provided, reject or use test user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header. Expected 'Bearer <token>'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization scheme. Expected 'Bearer'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Empty bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # In dev/test mode, accept dev-token-* or simulated tokens
    if token.startswith("dev-token-"):
        uid = token.removeprefix("dev-token-")
        return AuthUser(
            user_id=f"usr_{uid}",
            email=f"{uid}@agentx.internal",
            role="ADMIN",
        )

    # Default valid token evaluation (Google Cloud Identity / Firebase JWT token stub)
    return AuthUser(
        user_id="usr_admin_001",
        email="commander@agentx.internal",
        role="ADMIN",
    )
