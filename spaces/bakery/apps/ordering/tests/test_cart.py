"""Tests for per-session cart behaviour (`BakerySession`)."""

from __future__ import annotations

import pytest

from app.domain.session import BakerySession, CartError


def make_session() -> BakerySession:
    return BakerySession(session_id="test")


def test_add_accumulates_quantity() -> None:
    s = make_session()
    s.add("croissant")
    s.add("croissant", 2)
    assert s.item_count == 3
    lines = {line.product.id: line.quantity for line in s.lines}
    assert lines == {"croissant": 3}


def test_add_unknown_product_raises() -> None:
    s = make_session()
    with pytest.raises(CartError):
        s.add("baguette-supreme")


def test_add_non_positive_quantity_raises() -> None:
    s = make_session()
    with pytest.raises(CartError):
        s.add("croissant", 0)


def test_set_quantity_zero_removes_line() -> None:
    s = make_session()
    s.add("eclair", 2)
    s.set_quantity("eclair", 0)
    assert s.item_count == 0
    assert s.lines == []


def test_set_quantity_replaces_value() -> None:
    s = make_session()
    s.add("brioche", 1)
    s.set_quantity("brioche", 5)
    assert s.item_count == 5


def test_remove_is_idempotent() -> None:
    s = make_session()
    s.add("chouquette")
    s.remove("chouquette")
    s.remove("chouquette")  # removing again is a no-op
    assert s.item_count == 0


def test_total_cents_matches_catalog_prices() -> None:
    s = make_session()
    s.add("croissant", 2)  # 320 * 2 = 640
    s.add("mille-feuille")  # 560
    assert s.total_cents == 640 + 560


def test_cart_summary_shape() -> None:
    s = make_session()
    s.add("croissant")
    summary = s.cart_summary()
    assert summary["count"] == 1
    assert summary["total_cents"] == 320
    assert summary["total"].startswith("€")


def test_checkout_produces_order_and_clears_cart() -> None:
    s = make_session()
    s.add("croissant", 2)
    s.add("eclair")
    order = s.checkout(customer_name="Ada", pickup_time="tomorrow 9am")

    assert order.number.startswith("BK-")
    assert order.customer_name == "Ada"
    assert order.pickup_time == "tomorrow 9am"
    assert order.total_cents == 320 * 2 + 490
    # Cart is emptied after checkout, and the order is retained.
    assert s.item_count == 0
    assert s.orders == [order]


def test_checkout_empty_cart_raises() -> None:
    s = make_session()
    with pytest.raises(CartError):
        s.checkout()


def test_order_numbers_are_monotonic() -> None:
    s = make_session()
    s.add("croissant")
    first = s.checkout()
    s.add("brioche")
    second = s.checkout()
    assert first.number != second.number
