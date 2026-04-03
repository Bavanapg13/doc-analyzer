from typing import Annotated

from fastapi import Header, HTTPException, status

from .config import get_settings


def verify_api_key(
    x_api_key: Annotated[str | None, Header(alias="x-api-key")] = None,
) -> None:
    settings = get_settings()
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )
