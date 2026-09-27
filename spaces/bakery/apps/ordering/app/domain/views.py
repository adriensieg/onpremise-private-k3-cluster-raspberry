"""View builders.

These turn domain objects into the plain-dict `structuredContent` payloads that
each tool returns. ChatGPT hands that payload to the matching widget via
`window.openai.toolOutput`, so the shapes here are effectively the contract
between the server and the browser UI.

Keeping them in one place means the tools stay thin and the widgets always
receive a consistent envelope: every view carries a `cart` summary so any
surface can render an up-to-date cart badge.
"""

from __future__ import annotations

from . import catalog
from .models import CURRENCY, CURRENCY_SYMBOL, Order
from .session import BakerySession


def _envelope(view: str, session: BakerySession, **extra) -> dict:
    return {
        "view": view,
        "cart": session.cart_summary(),
        "currency": CURRENCY,
        "currency_symbol": CURRENCY_SYMBOL,
        **extra,
    }


def catalog_view(session: BakerySession, category: str | None = None) -> dict:
    products = catalog.find_products(category)
    return _envelope(
        "catalog",
        session,
        heading="Today at the counter" if not category else f"Our {category}",
        products=[product.to_view() for product in products],
    )


def cart_view(session: BakerySession) -> dict:
    return _envelope(
        "cart",
        session,
        items=[line.to_view() for line in session.lines],
        item_count=session.item_count,
        total_cents=session.total_cents,
        total=session.cart_summary()["total"],
    )


def confirmation_view(session: BakerySession, order: Order) -> dict:
    return _envelope("confirmation", session, order=order.to_view())
