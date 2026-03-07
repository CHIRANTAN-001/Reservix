from typing import Annotated, Any, Mapping, Optional, Generic, TypeVar, List, Dict
from annotated_doc import Doc
from pydantic import BaseModel
from fastapi import HTTPException, FastAPI, Response
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from loguru import logger

T = TypeVar("T")

# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str
    data: Optional[T] = None


class ErrorDetails(BaseModel):
    field: Optional[str] = None
    message: str


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    errors: Optional[list[ErrorDetails]] = None


# ---------------------------------------------------------------------------
# Response builder functions
# ---------------------------------------------------------------------------


def success_response(
    message: str, 
    data: Any = None,
    cookies: Optional[List[Dict[str, Any]]] = None,
    status_code: int = 200
) -> JSONResponse:
    """Return a standardized success JSON response"""
    body = SuccessResponse(message=message, data=data.model_dump(mode="json") if data else None)
    response = JSONResponse(
        status_code=status_code, 
        content=body.model_dump(),
    )
    if cookies:
        for cookie in cookies:
            response.set_cookie(**cookie)
    return response


def created_response(
    message: str = "Created successfully",
    data: Any = None,
) -> JSONResponse:
    return success_response(message=message, data=data, status_code=201)


# ---------------------------------------------------------------------------
# Custom exception classes
# ---------------------------------------------------------------------------


class AppException(HTTPException):
    """Base app exception - extend this for domain specific errors."""

    def __init__(
        self,
        status_code: int,
        message: str,
        errors: Optional[list[ErrorDetails]] = None,
    ) -> None:
        super().__init__(status_code, detail=message)
        self.message = message
        self.errors = errors


class NotFoundException(AppException):
    def __init__(self, resource: str = "Resource", resource_id: Any = None) -> None:
        msg = f"{resource}"
        if resource_id is not None:
            msg = f"{resource} with id {resource_id} not found"
        super().__init__(status_code=404, message=msg)


class BadRequestError(AppException):
    def __init__(
        self,
        message: str = "Bad Request",
        errors: list[ErrorDetails] | None = None,
    ) -> None:
        super().__init__(status_code=400, message=message, errors=errors)


class ConflictRequestError(AppException):
    def __init__(
        self,
        message: str = "Resource already exists",
    ) -> None:
        super().__init__(status_code=409, message=message)


class UnauthorizedError(AppException):
    def __init__(
        self,
        message: str = "Unauthorized",
    ) -> None:
        super().__init__(status_code=401, message=message)


class ForbiddenError(AppException):
    def __init__(
        self,
        message: str = "Forbidden",
    ) -> None:
        super().__init__(status_code=403, message=message)


# ---------------------------------------------------------------------------
# Exception → JSON response handlers (register in main.py)
# ---------------------------------------------------------------------------


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(AppException)
    async def app_exception_handler(request, exc: AppException):
        body = ErrorResponse(message=exc.message, errors=exc.errors)

        return JSONResponse(
            status_code=exc.status_code,
            content=body.model_dump(),
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request, exc: Exception):
        body = ErrorResponse(message="Internal server error")

        return JSONResponse(
            status_code=500,
            content=body.model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc: RequestValidationError):
        print(exc.errors())
        errors = [
            ErrorDetails(
                field=str(err["loc"][1] if len(err["loc"]) > 1 else err["loc"][0]),
                message=err["msg"],
            )
            for err in exc.errors()
        ]
        body = ErrorResponse(message="Validation error", errors=errors)
        return JSONResponse(
            status_code=422,
            content=body.model_dump(),
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request, exc: ValueError):
        body = ErrorResponse(message=str(exc))
        return JSONResponse(
            status_code=400,
            content=body.model_dump(),
        )