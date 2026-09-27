"""Immutable-ish value objects for the bakery domain.

Money is stored as integer cents to avoid floating-point drift, and formatted
for display at the edge (in the widgets / view builders).
"""

from __future__ import annotations

from pydantic import BaseModel, Field

CURRENCY = "EUR"
CURRENCY_SYMBOL = "€"


def format_money(cents: int) -> str:
    """Render integer cents as a display string, e.g. 320 -> '€3.20'."""
    return f"{CURRENCY_SYMBOL}{cents / 100:.2f}"


class Product(BaseModel):
    """A single item on the bakery menu."""

    id: str
    name: str
    description: str
    price_cents: int = Field(ge=0)
    category: str = "pastry"
    # `shape` selects the inline SVG illustration drawn by the widget, so the
    # UI never depends on remote images or a CDN.
    shape: str = "croissant"
    emoji: str = "🥐"

    def to_view(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price_cents": self.price_cents,
            "price": format_money(self.price_cents),
            "category": self.category,
            "shape": self.shape,
            "emoji": self.emoji,
        }


class CartLine(BaseModel):
    """A product plus the quantity the customer wants."""

    product: Product
    quantity: int = Field(ge=1)

    @property
    def line_total_cents(self) -> int:
        return self.product.price_cents * self.quantity

    def to_view(self) -> dict:
        return {
            **self.product.to_view(),
            "quantity": self.quantity,
            "line_total_cents": self.line_total_cents,
            "line_total": format_money(self.line_total_cents),
        }


class Order(BaseModel):
    """A completed checkout."""

    number: str
    lines: list[CartLine]
    total_cents: int
    customer_name: str | None = None
    pickup_time: str | None = None

    def to_view(self) -> dict:
        return {
            "number": self.number,
            "customer_name": self.customer_name,
            "pickup_time": self.pickup_time,
            "items": [line.to_view() for line in self.lines],
            "item_count": sum(line.quantity for line in self.lines),
            "total_cents": self.total_cents,
            "total": format_money(self.total_cents),
            "currency": CURRENCY,
            "currency_symbol": CURRENCY_SYMBOL,
        }
