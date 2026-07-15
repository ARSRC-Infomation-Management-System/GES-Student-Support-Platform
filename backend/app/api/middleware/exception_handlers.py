from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from app.exceptions.auth import AuthenticationException, PermissionDeniedException
from app.exceptions.complaint import ComplaintNotFoundException, ScopeMismatchException
from app.exceptions.storage import StorageException

def register_exception_handlers(app: FastAPI):
    @app.exception_handler(AuthenticationException)
    async def auth_exception_handler(request: Request, exc: AuthenticationException):
        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "error": {
                    "code": "AUTHENTICATION_FAILED",
                    "message": str(exc)
                }
            }
        )

    @app.exception_handler(PermissionDeniedException)
    async def permission_exception_handler(request: Request, exc: PermissionDeniedException):
        return JSONResponse(
            status_code=403,
            content={
                "success": False,
                "error": {
                    "code": "PERMISSION_DENIED",
                    "message": str(exc)
                }
            }
        )

    @app.exception_handler(ComplaintNotFoundException)
    async def not_found_exception_handler(request: Request, exc: ComplaintNotFoundException):
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": str(exc)
                }
            }
        )

    @app.exception_handler(ScopeMismatchException)
    async def scope_exception_handler(request: Request, exc: ScopeMismatchException):
        return JSONResponse(
            status_code=403,
            content={
                "success": False,
                "error": {
                    "code": "SCOPE_MISMATCH",
                    "message": str(exc)
                }
            }
        )

    @app.exception_handler(StorageException)
    async def storage_exception_handler(request: Request, exc: StorageException):
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": {
                    "code": "STORAGE_ERROR",
                    "message": str(exc)
                }
            }
        )
