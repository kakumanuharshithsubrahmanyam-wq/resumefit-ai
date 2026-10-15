from typing import Dict, Optional

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.exceptions.api import APIRequestError
from app.schemas.response import APIError, ErrorDetail


def _error_response(
    status_code: int,
    *,
    code: str,
    message: str,
    details: Optional[Dict[str, object]] = None,
) -> JSONResponse:
    body = APIError(
        error=ErrorDetail(code=code, message=message, details=details),
    )
    return JSONResponse(status_code=status_code, content=body.model_dump())


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(APIRequestError)
    async def api_request_error_handler(
        _request: Request,
        exc: APIRequestError,
    ) -> JSONResponse:
        return _error_response(
            exc.status_code,
            code=exc.code,
            message=exc.message,
            details=exc.details,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        _request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        code = "http_error"
        if exc.status_code == status.HTTP_404_NOT_FOUND:
            code = "not_found"
        elif exc.status_code == status.HTTP_401_UNAUTHORIZED:
            code = "unauthorized"
        elif exc.status_code == status.HTTP_403_FORBIDDEN:
            code = "forbidden"

        detail = exc.detail
        if isinstance(detail, str):
            message = detail
        else:
            message = "Request failed"
            details = detail if isinstance(detail, dict) else None
            return _error_response(
                exc.status_code,
                code=code,
                message=message,
                details=details,
            )

        return _error_response(exc.status_code, code=code, message=message)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return _error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="validation_error",
            message="Request validation failed",
            details={"errors": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        _request: Request,
        _exc: Exception,
    ) -> JSONResponse:
        return _error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="internal_error",
            message="An unexpected error occurred",
        )
