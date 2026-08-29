from collections.abc import Callable
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse


class BackendError(Exception):
    """Base exception for expected application errors."""

    def __init__(
        self, message: str, *, code: str = "application_error", status_code: int = 400
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


async def backend_error_handler(request: Request, exc: BackendError) -> JSONResponse:
    del request
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


def exception_handlers() -> dict[type[Exception], Callable[..., Any]]:
    return {BackendError: backend_error_handler}
