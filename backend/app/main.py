from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError

from app.api.v1.routes import router as v1_router
from app.core.config import settings
from app.core.errors import error_response
from app.db.session import Base, SessionLocal, engine
from app.services.repository import seed_data

app = FastAPI(title=settings.app_name)
app.include_router(v1_router)


@app.exception_handler(HTTPException)
async def http_exception_handler(_, exc: HTTPException):
    code = "BAD_REQUEST"
    if exc.status_code == 404:
        code = "NOT_FOUND"
    elif exc.status_code == 422:
        code = "VALIDATION_ERROR"
    return error_response(code, str(exc.detail), exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_, exc: RequestValidationError):
    return error_response("VALIDATION_ERROR", str(exc), 422)


@app.on_event("startup")
def startup():
    if settings.auto_create_tables:
        Base.metadata.create_all(bind=engine)
    if settings.bootstrap_demo_data:
        db = SessionLocal()
        try:
            seed_data(db)
        finally:
            db.close()


@app.get("/healthz")
def healthz():
    return {"status": "ok", "app": settings.app_name}
