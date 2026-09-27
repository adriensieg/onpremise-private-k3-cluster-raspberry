"""MCP Application Factory.

Given a session's state, build a fully-configured low-level MCP ``Server`` with
all tools, resources, and widgets registered. This layer is pure application
logic: it has no idea how requests arrive or how sessions are tracked. The
runtime layer (``runtime.py``) calls this once per session.
"""

from __future__ import annotations

from mcp.server.lowlevel import Server

from ..domain.session import BakerySession
from .resources import register_resources
from .tools import register_tools

SERVER_NAME = "bakery-mcp"
SERVER_VERSION = "0.1.0"


def create_mcp_server(session: BakerySession) -> Server:
    """Create and configure an MCP server bound to ``session``.

    A new server is created per session so the tool handlers can close over the
    session's cart — giving each ChatGPT conversation its own isolated state.
    """
    server: Server = Server(SERVER_NAME, version=SERVER_VERSION)
    register_resources(server)
    register_tools(server, session)
    return server
