"""Tests for the static catalog lookups."""

from __future__ import annotations

from app.domain import catalog


def test_all_products_has_expected_menu() -> None:
    ids = {p.id for p in catalog.all_products()}
    assert ids == {
        "croissant",
        "pain-au-chocolat",
        "chouquette",
        "eclair",
        "brioche",
        "mille-feuille",
    }


def test_get_product_known_and_unknown() -> None:
    assert catalog.get_product("croissant") is not None
    assert catalog.get_product("nope") is None


def test_find_products_without_filter_returns_full_menu() -> None:
    assert len(catalog.find_products()) == len(catalog.all_products())


def test_find_products_matches_by_name_fragment() -> None:
    results = catalog.find_products("chocolat")
    assert any(p.id == "pain-au-chocolat" for p in results)


def test_find_products_matches_by_id() -> None:
    results = catalog.find_products("mille")
    assert [p.id for p in results] == ["mille-feuille"]


def test_find_products_unmatched_falls_back_to_full_menu() -> None:
    # A customer asking for something we don't carry still gets to see options.
    results = catalog.find_products("danish")
    assert len(results) == len(catalog.all_products())


def test_product_to_view_formats_price() -> None:
    croissant = catalog.get_product("croissant")
    assert croissant is not None
    view = croissant.to_view()
    assert view["price"] == "€3.20"
    assert view["price_cents"] == 320
    assert view["shape"] == "croissant"
