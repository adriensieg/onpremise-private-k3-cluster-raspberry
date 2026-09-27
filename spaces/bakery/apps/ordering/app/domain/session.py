"""Per-MCP-session state.

Each ChatGPT connection gets exactly one `BakerySession`. It owns the cart and
order history for that conversation, which is what makes the widget feel like a
real application instead of a series of disconnected tool calls.

The class is intentionally free of any transport concerns; the runtime layer
constructs one per session and hands it to the MCP application factory.
"""

from __future__ import annotations

import itertools
import threading

from . import catalog
from .models import CURRENCY, CURRENCY_SYMBOL, CartLine, Order, format_money

# Order numbers are global and monotonic across the process, so two customers
# never see the same ticket number. `count()` reads are atomic under the GIL,
# but we guard with a lock to stay correct if that ever changes.
_order_counter = itertools.count(1)
_counter_lock = threading.Lock()


def _next_order_number() -> str:
    with _counter_lock:
        n = next(_order_counter)
    return f"BK-{n:04d}"


class CartError(Exception):
    """Raised for cart operations the customer can meaningfully recover from."""


class BakerySession:
    """Holds one conversation's cart and completed orders."""

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        # product_id -> quantity, preserving insertion order for stable display.
        self._items: dict[str, int] = {}
        self.orders: list[Order] = []

    # -- cart mutations ---------------------------------------------------

    def add(self, product_id: str, quantity: int = 1) -> None:
        if quantity < 1:
            raise CartError("Quantity must be at least 1.")
        if catalog.get_product(product_id) is None:
            raise CartError(f"We don't have '{product_id}' on the menu today.")
        self._items[product_id] = self._items.get(product_id, 0) + quantity

    def set_quantity(self, product_id: str, quantity: int) -> None:
        if catalog.get_product(product_id) is None:
            raise CartError(f"We don't have '{product_id}' on the menu today.")
        if quantity <= 0:
            self._items.pop(product_id, None)
            return
        self._items[product_id] = quantity

    def remove(self, product_id: str) -> None:
        self._items.pop(product_id, None)

    def clear(self) -> None:
        self._items.clear()

    # -- derived views ----------------------------------------------------

    @property
    def lines(self) -> list[CartLine]:
        result: list[CartLine] = []
        for product_id, quantity in self._items.items():
            product = catalog.get_product(product_id)
            if product is not None:
                result.append(CartLine(product=product, quantity=quantity))
        return result

    @property
    def item_count(self) -> int:
        return sum(self._items.values())

    @property
    def total_cents(self) -> int:
        return sum(line.line_total_cents for line in self.lines)

    def cart_summary(self) -> dict:
        """A compact snapshot every widget can use to keep its cart badge fresh."""
        return {
            "count": self.item_count,
            "total_cents": self.total_cents,
            "total": format_money(self.total_cents),
            "currency": CURRENCY,
            "currency_symbol": CURRENCY_SYMBOL,
        }

    # -- checkout ---------------------------------------------------------

    def checkout(
        self, customer_name: str | None = None, pickup_time: str | None = None
    ) -> Order:
        if not self._items:
            raise CartError("Your cart is empty — add a pastry before checking out.")
        order = Order(
            number=_next_order_number(),
            lines=self.lines,
            total_cents=self.total_cents,
            customer_name=customer_name,
            pickup_time=pickup_time,
        )
        self.orders.append(order)
        self.clear()
        return order
