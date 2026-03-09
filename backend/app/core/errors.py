from datetime import datetime, timezone

from fastapi import Request
from fastapi.responses import JSONResponse


def error_response(code: str, message: str, status_code: int):
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            }
        },
    )


def not_found(_: Request, __):
    return error_response("NOT_FOUND", "resource not found", 404)
