"""ChatGPT Apps SDK metadata helpers.

The Apps SDK is driven almost entirely by `_meta` keys under the `openai/*`
namespace. These small builders keep the exact key strings in one place so the
tool and resource registrations stay readable and consistent.

References:
  - openai/outputTemplate .......... links a tool to the widget it renders
  - openai/toolInvocation/invoking . status text shown while the tool runs
  - openai/toolInvocation/invoked .. status text shown once it finishes
  - openai/widgetAccessible ........ lets the widget call this tool itself
  - openai/widgetCSP ............... connect/resource domains for the iframe
  - openai/widgetDescription ....... human description of the widget
  - openai/widgetPrefersBorder ..... hint that the widget looks best framed
"""

from __future__ import annotations

# ui:// resource URIs for each widget. ChatGPT fetches the HTML behind these.
CATALOG_URI = "ui://widget/catalog.html"
CART_URI = "ui://widget/cart.html"
CONFIRMATION_URI = "ui://widget/confirmation.html"

# Domains the sandboxed iframe is allowed to reach. We render pastries as inline
# SVG (no image host needed) and only pull optional web fonts, so the CSP stays
# tight. Widen `connect_domains` only if a widget needs to fetch at runtime.
_WIDGET_CSP = {
    "connect_domains": [],
    "resource_domains": [
        "https://fonts.googleapis.com",
        "https://fonts.gstatic.com",
    ],
}


def tool_meta(
    output_template: str,
    *,
    invoking: str,
    invoked: str,
    widget_accessible: bool = True,
) -> dict:
    """Metadata attached to a *tool descriptor* so ChatGPT renders its widget."""
    return {
        "openai/outputTemplate": output_template,
        "openai/toolInvocation/invoking": invoking,
        "openai/toolInvocation/invoked": invoked,
        # Allow the rendered widget to invoke this tool (e.g. an "Add" button
        # calling `add_to_cart`). Without this, only the model can call it.
        "openai/widgetAccessible": widget_accessible,
        "openai/resultCanProduceWidget": True,
    }


def widget_meta(description: str, *, prefers_border: bool = True) -> dict:
    """Metadata attached to a *resource* (the widget HTML itself)."""
    return {
        "openai/widgetDescription": description,
        "openai/widgetPrefersBorder": prefers_border,
        "openai/widgetCSP": _WIDGET_CSP,
    }
