import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from pathlib import Path

from app.core.logging_config import configure_logging
from app.database import Base, engine
from app.routers import auth, booking, rooms

logger = configure_logging()

app = FastAPI()
static_dir = Path(__file__).resolve().parent / "static"

Base.metadata.create_all(bind=engine)

with engine.begin() as connection:
    connection.execute(
        text("ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR NOT NULL DEFAULT 'user'")
    )


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    start = time.perf_counter()
    client_ip = request.client.host if request.client else "-"
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.exception(
            "request failed method=%s path=%s client_ip=%s duration_ms=%.2f",
            request.method,
            request.url.path,
            client_ip,
            duration_ms
        )
        raise

    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "request completed method=%s path=%s status=%s client_ip=%s duration_ms=%.2f",
        request.method,
        request.url.path,
        response.status_code,
        client_ip,
        duration_ms
    )
    return response


app.include_router(auth.router)
app.include_router(booking.router)
app.include_router(rooms.router)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning("validation error path=%s errors=%s", request.url.path, exc.errors())
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning("http error path=%s status=%s detail=%s", request.url.path, exc.status_code, exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.exception("sqlalchemy error path=%s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Database error"})


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("unhandled exception path=%s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/")
def root():
    return FileResponse(static_dir / "index.html")


@app.get("/api")
def api_root():
    return {"message": "Booking API"}


@app.get("/test")
def test():
    return {"ok": True}
