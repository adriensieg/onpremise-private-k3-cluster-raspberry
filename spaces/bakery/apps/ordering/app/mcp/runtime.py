"""Runtime Hosting Layer.

This owns everything the MCP Application Factory does not: the streamable-HTTP
transport, per-session lifecycle, and request routing. It deliberately mirrors
the pattern used by the SDK's own ``StreamableHTTPSessionManager`` so the
behaviour matches a standard Apps SDK server, while keeping the session map
explicit (as the project brief asks for).

Lifecycle of a stateful session
--------------------------------
1. ChatGPT POSTs an ``initialize`` request with no ``mcp-session-id`` header.
2. We mint a session id, build a `BakerySession`, ask the factory for a fresh
   `Server`, and create a `StreamableHTTPServerTransport` for that id.
3. We start a background task running ``server.run(...)`` over the transport's
   streams; it stays alive for the life of the session.
4. We dispatch the current request to the transport, which replies with the
   session id in the ``Mcp-Session-Id`` response header.
5. Subsequent POST / GET / DELETE requests carry that header and are routed to
   the same transport, preserving the cart across calls. DELETE ends the session.

The manager exposes:
  * ``lifespan()``  — an async context manager that runs the background task
    group; enter it from the FastAPI lifespan.
  * ``asgi_app``    — a raw ASGI callable to mount at ``/mcp``.
"""

from __future__ import annotations

import contextlib
import json
import logging
from collections.abc import AsyncIterator
from uuid import uuid4

import anyio
from mcp.server.lowlevel import Server
from mcp.server.streamable_http import (
    MCP_SESSION_ID_HEADER,
    StreamableHTTPServerTransport,
)

from ..domain.session import BakerySession
from .factory import create_mcp_server

logger = logging.getLogger("bakery.runtime")

ServerFactory = "callable"  # documented below via type hint on __init__


class SessionManager:
    """Tracks one `StreamableHTTPServerTransport` per MCP session."""

    def __init__(self, *, json_response: bool = False) -> None:
        # If True, POSTs get a single JSON body instead of an SSE stream. SSE
        # (the default) is what ChatGPT expects, so we keep it off.
        self._json_response = json_response
        self._transports: dict[str, StreamableHTTPServerTransport] = {}
        self._task_group: anyio.abc.TaskGroup | None = None

    # -- lifecycle --------------------------------------------------------

    @contextlib.asynccontextmanager
    async def lifespan(self) -> AsyncIterator[None]:
        """Run the background task group that hosts every session's server loop."""
        async with anyio.create_task_group() as task_group:
            self._task_group = task_group
            logger.info("Session manager started")
            try:
                yield
            finally:
                logger.info("Session manager shutting down")
                task_group.cancel_scope.cancel()
                self._task_group = None
                self._transports.clear()

    # -- ASGI entry point -------------------------------------------------

    async def asgi_app(self, scope, receive, send) -> None:
        """ASGI callable to mount at ``/mcp``."""
        if scope["type"] != "http":
            # Only HTTP is served here; ignore other scope types (e.g. websocket)
            # without emitting an invalid response.
            return

        headers = {k.decode().lower(): v.decode() for k, v in scope["headers"]}
        session_id = headers.get(MCP_SESSION_ID_HEADER.lower())
        method: str = scope["method"]

        if session_id:
            transport = self._transports.get(session_id)
            if transport is None:
                await _json_response(
                    send, 404, _rpc_error("Session not found or expired")
                )
                return
            await transport.handle_request(scope, receive, send)
            if method == "DELETE":
                # The transport tears down its streams on DELETE, which ends the
                # server loop; drop our reference so the id can't be reused.
                self._transports.pop(session_id, None)
                logger.info("Session %s terminated", session_id)
            return

        # No session id: this must be a new connection (an ``initialize`` POST).
        if method != "POST":
            await _json_response(
                send, 400, _rpc_error("Missing mcp-session-id header")
            )
            return

        await self._create_session(scope, receive, send)

    # -- session creation -------------------------------------------------

    async def _create_session(self, scope, receive, send) -> None:
        if self._task_group is None:
            raise RuntimeError(
                "SessionManager.lifespan() is not active; enter it from the app lifespan."
            )

        session_id = uuid4().hex
        state = BakerySession(session_id=session_id)
        server: Server = create_mcp_server(state)
        transport = StreamableHTTPServerTransport(
            mcp_session_id=session_id,
            is_json_response_enabled=self._json_response,
        )

        async def run_server(*, task_status=anyio.TASK_STATUS_IGNORED) -> None:
            async with transport.connect() as (read_stream, write_stream):
                # Signal readiness only once the streams exist, so the request
                # below is dispatched into a live server loop.
                task_status.started()
                await server.run(
                    read_stream,
                    write_stream,
                    server.create_initialization_options(),
                )

        # `start()` waits for task_status.started() before returning.
        await self._task_group.start(run_server)
        self._transports[session_id] = transport
        logger.info("Session %s created", session_id)

        await transport.handle_request(scope, receive, send)


# -- tiny ASGI response helpers ------------------------------------------


async def _json_response(send, status: int, payload: dict) -> None:
    body = json.dumps(payload).encode("utf-8")
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode()),
            ],
        }
    )
    await send({"type": "http.response.body", "body": body})


def _rpc_error(message: str) -> dict:
    # Shape mirrors a JSON-RPC error so MCP clients surface it cleanly.
    return {
        "jsonrpc": "2.0",
        "error": {"code": -32000, "message": message},
        "id": None,
    }
