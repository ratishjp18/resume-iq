"""Structured error responses: {"error": {"code", "message", "details"?}}."""
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.services.document_parser import DocumentError

logger = logging.getLogger("resumeiq.api")


def _body(code: str, message: str, details=None) -> dict:
    return {"error": {"code": code, "message": message, "details": details}}


class NotFound(HTTPException):
    def __init__(self, what: str):
        super().__init__(status_code=404, detail=f"{what} not found.")


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DocumentError)
    async def _doc(_: Request, exc: DocumentError):
        return JSONResponse(status_code=exc.status, content=_body(exc.code, exc.message))

    @app.exception_handler(HTTPException)
    async def _http(_: Request, exc: HTTPException):
        code = {404: "not_found", 405: "method_not_allowed"}.get(exc.status_code, "http_error")
        return JSONResponse(status_code=exc.status_code, content=_body(code, str(exc.detail)))

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError):
        # Never echo submitted values (they may contain personal data): only location + message.
        details = [{"field": ".".join(str(p) for p in e["loc"] if p != "body"), "message": e["msg"]} for e in exc.errors()]
        return JSONResponse(status_code=422, content=_body("validation_error", "The request is invalid.", details))

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception):
        logger.error("Unhandled error: %s", type(exc).__name__)  # no request bodies / resume text in logs
        return JSONResponse(status_code=500, content=_body("internal_error", "An unexpected error occurred."))
