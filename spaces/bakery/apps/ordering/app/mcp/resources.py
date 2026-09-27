"""Widget resource registration.

Apps SDK widgets are MCP *resources* whose content is HTML served with the
special MIME type ``text/html+skybridge``. That MIME type is what tells ChatGPT
to render the resource as an interactive, sandboxed iframe (via OpenAI's
"Skybridge" runtime) rather than as plain text.

A tool points at one of these resources through its
``_meta["openai/outputTemplate"]`` (see ``tools.py``); ChatGPT then fetches the
HTML behind that ``ui://`` URI and renders it.
"""

from __future__ import annotations

import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.lowlevel.helper_types import ReadResourceContents

from ..widgets import render_widget
from . import metadata

SKYBRIDGE_MIME = "text/html+skybridge"

# uri -> (widget file, human title, widget _meta)
_WIDGETS: dict[str, tuple[str, str, dict]] = {
    metadata.CATALOG_URI: (
        "catalog.html",
        "Bakery catalog",
        metadata.widget_meta(
            "An interactive gallery of the bakery's pastries with add-to-cart controls."
        ),
    ),
    metadata.CART_URI: (
        "cart.html",
        "Shopping cart",
        metadata.widget_meta(
            "The current shopping cart with quantity steppers, removal, and a running total."
        ),
    ),
    metadata.CONFIRMATION_URI: (
        "confirmation.html",
        "Order confirmation",
        metadata.widget_meta(
            "A confirmation receipt shown after a successful checkout."
        ),
    ),
}


def register_resources(server: Server) -> None:
    """Attach the widget resources to a low-level MCP ``Server``."""

    @server.list_resources()
    async def list_resources() -> list[types.Resource]:
        return [
            types.Resource(
                uri=uri,  # type: ignore[arg-type]
                name=title,
                title=title,
                description=meta.get("openai/widgetDescription"),
                mimeType=SKYBRIDGE_MIME,
                _meta=meta,
            )
            for uri, (_file, title, meta) in _WIDGETS.items()
        ]

    @server.read_resource()
    async def read_resource(uri: types.AnyUrl):
        key = str(uri)
        entry = _WIDGETS.get(key)
        if entry is None:
            raise ValueError(f"Unknown resource: {key}")
        widget_file, _title, _meta = entry
        html = render_widget(widget_file)
        # Returning ReadResourceContents lets us set the Skybridge MIME type;
        # a bare string would default to text/plain and ChatGPT would not render
        # it as a widget.
        return [ReadResourceContents(content=html, mime_type=SKYBRIDGE_MIME)]
