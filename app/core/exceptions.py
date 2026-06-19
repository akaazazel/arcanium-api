from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


async def http_exception(request: Request, exec: HTTPException):
    return JSONResponse(
        status_code=exec.status_code,
        content={
            "success": False,
            "message": exec.detail,
        },
    )


async def validation_exception(request: Request, exec: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "Validation failed",
            "errors": exec.errors(),
        },
    )


async def internal_server_exception(request: Request, exec: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
        },
    )


class NoteNotFoundError(Exception):
    def __init__(self, message: str = "Note not found") -> None:
        super().__init__(message)


class DuplicateUserError(Exception):
    def __init__(self, message: str = "User already exists") -> None:
        super().__init__(message)
