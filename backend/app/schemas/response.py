from typing import Any, Dict, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(default=None)


class APIError(BaseModel):
    error: ErrorDetail


class APIResponse(BaseModel, Generic[T]):
    """Standard envelope for successful API responses."""

    success: bool = True
    data: T
    meta: Optional[Dict[str, Any]] = None
