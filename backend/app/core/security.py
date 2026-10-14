"""API-key authentication.

Deployed environments require a shared secret passed as the ``X-API-Key`` header.
In local development the key can be left empty, in which case auth is disabled and
a warning is logged at startup. We use ``hmac.compare_digest`` for constant-time
comparison to avoid timing attacks.
"""

from __future__ import annotations

import hmac
import logging

from fastapi import Depends, Header, HTTPException, status

from app.api.deps import get_settings_dep
from app.core.config import Settings

logger = logging.getLogger(__name__)


async def require_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    settings: Settings = Depends(get_settings_dep),
) -> None:
    """FastAPI dependency enforcing the API key when one is configured."""
    expected = settings.api_key
    if not expected:
        # Auth disabled (development only). The startup banner warns about this.
        return
    if not x_api_key or not hmac.compare_digest(x_api_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
            headers={"WWW-Authenticate": "API-Key"},
        )
