import hashlib
import logging
import os
from time import time
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_429_TOO_MANY_REQUESTS

from .db import query, query_one
from .models import LoginRequest

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("secdev")

APP_NAME = os.getenv("APP_NAME", "secdev-seed-s06-s08")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-real-projects")

WINDOW_SECONDS = 60
ATTEMPT_LIMIT = 5
_attempts: Dict[str, List[float]] = {}

app = FastAPI(title=APP_NAME, debug=DEBUG)
templates = Jinja2Templates(directory="app/templates")


def _generate_token(username: str) -> str:
    payload = f"{username}:{SECRET_KEY}".encode("utf-8", "ignore")
    return hashlib.sha256(payload).hexdigest()


def _too_many_attempts(key: str) -> bool:
    now = time()
    bucket = [ts for ts in _attempts.get(key, []) if now - ts < WINDOW_SECONDS]
    if len(bucket) >= ATTEMPT_LIMIT:
        _attempts[key] = bucket
        return True
    bucket.append(now)
    _attempts[key] = bucket
    return False


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response


@app.exception_handler(Exception)
async def _unhandled_exception(request: Request, exc: Exception):
    logger.error(
        "Unhandled error on %s %s: %s",
        request.method,
        request.url.path,
        exc.__class__.__name__,
    )
    return JSONResponse({"detail": "Internal error"}, status_code=500)


@app.get("/", response_class=HTMLResponse)
def index(request: Request, msg: Optional[str] = None):
    return templates.TemplateResponse(
        request, "index.html", {"message": msg or "Hello!"}
    )


@app.get("/echo", response_class=HTMLResponse)
def echo(request: Request, msg: Optional[str] = None):
    return templates.TemplateResponse(request, "index.html", {"message": msg or ""})


@app.get("/search")
def search(q: Optional[str] = Query(default=None, min_length=1, max_length=32)):
    if q is None:
        sql = "SELECT id, name, description FROM items LIMIT 10"
        items = query(sql, ())
    else:
        sql = "SELECT id, name, description FROM items WHERE name LIKE ?"
        pattern = f"%{q}%"
        items = query(sql, (pattern,))
    return JSONResponse(content={"items": items})


@app.post("/login")
def login(request: Request, payload: LoginRequest):
    client_host = request.client.host if request.client else "unknown"
    rate_key = f"{payload.username}:{client_host}"
    if _too_many_attempts(rate_key):
        raise HTTPException(
            status_code=HTTP_429_TOO_MANY_REQUESTS, detail="Too Many Attempts"
        )

    sql = "SELECT id, username FROM users WHERE username = ? AND password = ?"
    row = query_one(sql, (payload.username, payload.password))
    if not row:
        masked_user = payload.username[:3] + "***"
        logger.info("Failed login attempt for username=%s", masked_user)
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    token = _generate_token(row["username"])
    return {"status": "ok", "user": row["username"], "token": token}
