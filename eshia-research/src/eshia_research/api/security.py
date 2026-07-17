"""Security dependencies for editorial API operations."""

from secrets import compare_digest
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from eshia_research.config import Settings, get_settings


def require_admin_api_token(
    x_admin_token: Annotated[str | None, Header()] = None,
    settings: Settings = Depends(get_settings),
) -> None:
    """Fail closed unless an explicit administrator secret is configured."""

    expected = settings.api_admin_token.strip()
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Editorial writes are disabled on this deployment.",
        )
    if not x_admin_token or not compare_digest(x_admin_token, expected):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A valid administrator token is required.",
        )
