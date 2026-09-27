"""End-to-end smoke test of the MCP server over an in-memory transport.

This exercises the application factory the same way ChatGPT would over the wire
(initialize -> list tools/resources -> call tools), but without any HTTP, using
the SDK's in-memory client/server helper.
"""

from __future__ import annotations

import json

import pytest

from app.domain.session import BakerySession
from app.mcp.factory import create_mcp_server
from app.mcp.metadata import CART_URI, CATALOG_URI, CONFIRMATION_URI

# The in-memory helper lives in the MCP SDK's shared module.
create_connected = pytest.importorskip(
    "mcp.shared.memory"
).create_connected_server_and_client_session


def _structured(result) -> dict:
    """Pull the structuredContent dict out of a CallToolResult across SDK versions."""
    structured = getattr(result, "structuredContent", None)
    if structured is not None:
        return structured
    # Fall back to parsing the text content as JSON if needed.
    for block in getattr(result, "content", []) or []:
        text = getattr(block, "text", None)
        if text:
            try:
                return json.loads(text)
            except ValueError:
                pass
    return {}


@pytest.mark.anyio
async def test_initialize_and_list() -> None:
    server = create_mcp_server(BakerySession("smoke"))
    async with create_connected(server) as client:
        await client.initialize()

        tools = await client.list_tools()
        names = {t.name for t in tools.tools}
        assert {
            "show_menu",
            "add_to_cart",
            "set_cart_quantity",
            "remove_from_cart",
            "view_cart",
            "checkout",
        } <= names

        resources = await client.list_resources()
        uris = {str(r.uri) for r in resources.resources}
        assert {CATALOG_URI, CART_URI, CONFIRMATION_URI} <= uris


@pytest.mark.anyio
async def test_show_menu_outputs_catalog_widget() -> None:
    server = create_mcp_server(BakerySession("smoke"))
    async with create_connected(server) as client:
        await client.initialize()

        tools = await client.list_tools()
        show_menu = next(t for t in tools.tools if t.name == "show_menu")
        meta = show_menu.meta or {}
        assert meta.get("openai/outputTemplate") == CATALOG_URI

        result = await client.call_tool("show_menu", {})
        data = _structured(result)
        assert data.get("view") == "catalog"
        assert len(data.get("products", [])) == 6


@pytest.mark.anyio
async def test_cart_flow_is_stateful() -> None:
    server = create_mcp_server(BakerySession("smoke"))
    async with create_connected(server) as client:
        await client.initialize()

        await client.call_tool("add_to_cart", {"product_id": "croissant", "quantity": 2})
        result = await client.call_tool("add_to_cart", {"product_id": "eclair"})
        data = _structured(result)

        assert data["view"] == "cart"
        assert data["cart"]["count"] == 3
        by_id = {item["id"]: item for item in data["items"]}
        assert by_id["croissant"]["quantity"] == 2
        assert by_id["eclair"]["quantity"] == 1


@pytest.mark.anyio
async def test_checkout_returns_confirmation_widget() -> None:
    server = create_mcp_server(BakerySession("smoke"))
    async with create_connected(server) as client:
        await client.initialize()

        await client.call_tool("add_to_cart", {"product_id": "brioche"})

        tools = await client.list_tools()
        checkout = next(t for t in tools.tools if t.name == "checkout")
        assert (checkout.meta or {}).get("openai/outputTemplate") == CONFIRMATION_URI

        result = await client.call_tool("checkout", {"name": "Ada"})
        data = _structured(result)
        assert data["view"] == "confirmation"
        assert data["order"]["number"].startswith("BK-")
        assert data["order"]["customer_name"] == "Ada"

        # Cart is empty again after checkout.
        view = _structured(await client.call_tool("view_cart", {}))
        assert view["cart"]["count"] == 0


@pytest.mark.anyio
async def test_read_catalog_resource_is_skybridge_html() -> None:
    server = create_mcp_server(BakerySession("smoke"))
    async with create_connected(server) as client:
        await client.initialize()

        result = await client.read_resource(CATALOG_URI)
        contents = result.contents
        assert contents, "expected resource contents"
        first = contents[0]
        assert first.mimeType == "text/html+skybridge"
        assert "<!doctype html>" in first.text.lower()
