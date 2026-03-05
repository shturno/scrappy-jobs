"""API key authentication dependency."""

import os

from fastapi import Header, HTTPException, status


def require_api_key(x_api_key: str = Header(...)) -> None:
    """Validate the X-API-Key header against the API_KEY env var.

    Raises 403 if the key is missing, not configured, or doesn't match.
    """
    api_key = os.getenv("API_KEY", "")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API key not configured on the server.",
        )
    if x_api_key != api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key.",
        )
