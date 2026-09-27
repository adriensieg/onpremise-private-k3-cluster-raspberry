"""Tool registration for a single session's MCP server.

Each tool does three things:

  1. Mutates or reads the per-session cart (`BakerySession`).
  2. Returns a short *text* summary for the model to reason about.
  3. Returns `structuredContent` (a view dict) that the linked widget renders
     via `window.openai.toolOutput`.

The tool descriptor's ``_meta["openai/outputTemplate"]`` names which widget to
open, and ``openai/widgetAccessible`` lets the widget call the tool back (so an
"Add" button in the catalog can call ``add_to_cart`` directly).
"""

from __future__ import annotations

from typing import Any

import mcp.types as types
from mcp.server.lowlevel import Server

from ..domain import catalog, views
from ..domain.models import format_money
from ..domain.session import BakerySession, CartError
from . import metadata

# The (content, structuredContent) pair returned by every tool handler.
ToolResult = tuple[list[types.ContentBlock], dict[str, Any]]


def _text(message: str) -> list[types.ContentBlock]:
    return [types.TextContent(type="text", text=message)]


def _tool_descriptors() -> list[types.Tool]:
    """The static list of tools this server exposes."""
    return [
        types.Tool(
            name="show_menu",
            title="Show the bakery menu",
            description=(
                "Show the bakery's pastry catalog as an interactive gallery. "
                "Use this whenever the customer wants to browse, see what's "
                "available, or asks about a kind of pastry. Optionally filter by "
                "a category or name such as 'croissant' or 'chocolate'."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Optional filter, e.g. 'croissant' or 'chocolate'.",
                    }
                },
            },
            _meta=metadata.tool_meta(
                metadata.CATALOG_URI,
                invoking="Warming the ovens…",
                invoked="Fresh from the oven",
            ),
        ),
        types.Tool(
            name="add_to_cart",
            title="Add a pastry to the cart",
            description=(
                "Add a pastry to the customer's cart by its product id. Increases "
                "the quantity if it is already in the cart. Returns the updated cart."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "string",
                        "description": "The product id, e.g. 'croissant' or 'mille-feuille'.",
                    },
                    "quantity": {
                        "type": "integer",
                        "minimum": 1,
                        "default": 1,
                        "description": "How many to add. Defaults to 1.",
                    },
                },
                "required": ["product_id"],
            },
            _meta=metadata.tool_meta(
                metadata.CART_URI,
                invoking="Adding to your box…",
                invoked="Added to your box",
            ),
        ),
        types.Tool(
            name="set_cart_quantity",
            title="Set a cart item's quantity",
            description=(
                "Set the exact quantity for a product already being considered. "
                "A quantity of 0 removes it. Returns the updated cart."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "product_id": {"type": "string"},
                    "quantity": {"type": "integer", "minimum": 0},
                },
                "required": ["product_id", "quantity"],
            },
            _meta=metadata.tool_meta(
                metadata.CART_URI,
                invoking="Updating your box…",
                invoked="Box updated",
            ),
        ),
        types.Tool(
            name="remove_from_cart",
            title="Remove a pastry from the cart",
            description="Remove a product from the cart entirely. Returns the updated cart.",
            inputSchema={
                "type": "object",
                "properties": {"product_id": {"type": "string"}},
                "required": ["product_id"],
            },
            _meta=metadata.tool_meta(
                metadata.CART_URI,
                invoking="Removing from your box…",
                invoked="Removed",
            ),
        ),
        types.Tool(
            name="view_cart",
            title="View the cart",
            description="Show the current contents of the cart with a running total.",
            inputSchema={"type": "object", "properties": {}},
            _meta=metadata.tool_meta(
                metadata.CART_URI,
                invoking="Opening your box…",
                invoked="Here's your box",
            ),
        ),
        types.Tool(
            name="checkout",
            title="Place the order",
            description=(
                "Check out the current cart and place the order. Optionally include "
                "the customer's name and a desired pickup time. Clears the cart and "
                "returns an order confirmation."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name for the order."},
                    "pickup_time": {
                        "type": "string",
                        "description": "Desired pickup time, e.g. 'tomorrow 9am'.",
                    },
                },
            },
            _meta=metadata.tool_meta(
                metadata.CONFIRMATION_URI,
                invoking="Placing your order…",
                invoked="Order confirmed",
            ),
        ),
    ]


def register_tools(server: Server, session: BakerySession) -> None:
    """Attach the tool list and dispatcher to a low-level MCP ``Server``.

    The handlers close over ``session`` so every tool call reads and writes the
    same per-conversation cart.
    """

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        return _tool_descriptors()

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> ToolResult:
        args = arguments or {}

        if name == "show_menu":
            category = args.get("category")
            view = views.catalog_view(session, category)
            count = len(view["products"])
            return _text(f"Showing {count} pastries."), view

        if name == "add_to_cart":
            product_id = args["product_id"]
            quantity = int(args.get("quantity", 1) or 1)
            try:
                session.add(product_id, quantity)
            except CartError as exc:
                return _cart_error(session, exc)
            product = catalog.get_product(product_id)
            label = product.name if product else product_id
            return (
                _text(f"Added {quantity}× {label} to the cart."),
                views.cart_view(session),
            )

        if name == "set_cart_quantity":
            product_id = args["product_id"]
            quantity = int(args["quantity"])
            try:
                session.set_quantity(product_id, quantity)
            except CartError as exc:
                return _cart_error(session, exc)
            return _text("Updated the cart."), views.cart_view(session)

        if name == "remove_from_cart":
            session.remove(args["product_id"])
            return _text("Removed from the cart."), views.cart_view(session)

        if name == "view_cart":
            summary = session.cart_summary()
            msg = (
                "The cart is empty."
                if session.item_count == 0
                else f"{session.item_count} item(s), total {summary['total']}."
            )
            return _text(msg), views.cart_view(session)

        if name == "checkout":
            try:
                order = session.checkout(
                    customer_name=args.get("name"),
                    pickup_time=args.get("pickup_time"),
                )
            except CartError as exc:
                return _cart_error(session, exc)
            return (
                _text(
                    f"Order {order.number} confirmed — {format_money(order.total_cents)}."
                ),
                views.confirmation_view(session, order),
            )

        raise ValueError(f"Unknown tool: {name}")


def _cart_error(session: BakerySession, exc: CartError) -> ToolResult:
    """Return a cart view carrying a friendly, recoverable error message."""
    view = views.cart_view(session)
    view["error"] = str(exc)
    return _text(str(exc)), view
