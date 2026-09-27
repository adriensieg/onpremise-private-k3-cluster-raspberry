"""FastAPI application.

Wires the Runtime Hosting Layer into an HTTP server:

  * mounts the MCP streamable-HTTP endpoint at ``/mcp``
  * runs the session manager's background task group via the app lifespan
    (FastAPI does *not* propagate lifespan to mounted sub-apps, so we drive it
    here explicitly)
  * adds CORS so ChatGPT's browser-side widgets can reach the endpoint, and
    exposes the ``Mcp-Session-Id`` response header the client needs to read
"""

from __future__ import annotations

import contextlib
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mcp.server.streamable_http import MCP_SESSION_ID_HEADER

from . import __version__
from .config import settings
from .logging_config import configure_logging
from .mcp.runtime import SessionManager

configure_logging(settings.log_level)

# One session manager for the process; it owns all live MCP sessions.
session_manager = SessionManager(json_response=settings.json_response)


@contextlib.asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    async with session_manager.lifespan():
        yield


app = FastAPI(
    title="Bakery MCP",
    version=__version__,
    summary="A ChatGPT Apps SDK storefront served over MCP.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    # The client must read the session id from the response to keep the session.
    expose_headers=[MCP_SESSION_ID_HEADER],
    allow_credentials=False,
)


@app.get("/", include_in_schema=False)
async def root() -> JSONResponse:
    return JSONResponse(
        {
            "name": "bakery-mcp",
            "version": __version__,
            "mcp_endpoint": "/mcp",
            "transport": "streamable-http",
            "docs": "/docs",
        }
    )


@app.get("/healthz", include_in_schema=False)
@app.get("/health", include_in_schema=False)
async def healthz() -> JSONResponse:
    # Both paths are served so the Kubernetes probes can use either convention.
    return JSONResponse({"status": "ok"})


# Mount the raw ASGI MCP app. Mounting (rather than a route) lets the transport
# own the full request/response cycle, including SSE streaming for GET.
app.mount("/mcp", session_manager.asgi_app)
