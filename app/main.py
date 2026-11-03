import json
import os
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.errors import DomainError

app = FastAPI(
    title="Gather API",
    description="API for a lightweight group chat application.",
    version="0.1.0",
)


@app.middleware("http")
async def log_api_request(request: Request, call_next):
    started_at = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        log_api_metric(request, started_at, 500)
        raise

    log_api_metric(request, started_at, response.status_code)
    return response


def log_api_metric(request: Request, started_at: float, status_code: int) -> None:
    route = request.scope.get("route")
    path = getattr(route, "path", "unmatched")
    if request.url.path.startswith("/api/") and not path.startswith("/api/"):
        path = f"/api{path}"
    print(
        json.dumps(
            {
                "event": "http_request",
                "method": request.method,
                "path": path,
                "status_code": status_code,
                "duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
            },
            separators=(",", ":"),
        ),
        flush=True,
    )


cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(DomainError)
async def handle_domain_error(_: Request, error: DomainError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={"detail": error.detail},
    )


app.include_router(api_router)
