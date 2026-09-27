"""The bakery menu.

In a real deployment this would come from a database or a POS system; here it is
a static list so the prototype has zero infrastructure dependencies.
"""

from __future__ import annotations

from .models import Product

PRODUCTS: list[Product] = [
    Product(
        id="croissant",
        name="Croissant",
        description="72-hour laminated butter dough, baked until shattering-crisp.",
        price_cents=320,
        shape="croissant",
        emoji="🥐",
    ),
    Product(
        id="pain-au-chocolat",
        name="Pain au Chocolat",
        description="Two batons of dark Valrhona folded into flaky pastry.",
        price_cents=380,
        shape="pain-au-chocolat",
        emoji="🍫",
    ),
    Product(
        id="chouquette",
        name="Chouquette",
        description="Airy choux puffs showered in crunchy pearl sugar. Sold by the six.",
        price_cents=450,
        shape="chouquette",
        emoji="⚪",
    ),
    Product(
        id="eclair",
        name="Éclair",
        description="Choux filled with vanilla-bean crème, finished with a chocolate glaze.",
        price_cents=490,
        shape="eclair",
        emoji="🍩",
    ),
    Product(
        id="brioche",
        name="Brioche",
        description="A tender, buttery loaf with a golden topknot. Best still warm.",
        price_cents=350,
        shape="brioche",
        emoji="🥖",
    ),
    Product(
        id="mille-feuille",
        name="Mille-feuille",
        description="Three layers of caramelised puff pastry and crème pâtissière.",
        price_cents=560,
        shape="mille-feuille",
        emoji="🍰",
    ),
]

_BY_ID: dict[str, Product] = {product.id: product for product in PRODUCTS}


def all_products() -> list[Product]:
    return list(PRODUCTS)


def find_products(category: str | None = None) -> list[Product]:
    """Return products, optionally filtered by a fuzzy category/name match."""
    if not category:
        return all_products()
    needle = category.strip().lower()
    matches = [
        product
        for product in PRODUCTS
        if needle in product.category.lower()
        or needle in product.name.lower()
        or needle in product.id.lower()
    ]
    # If nothing matched the filter, fall back to the full menu rather than an
    # empty catalog — a customer asking for "danishes" should still see options.
    return matches or all_products()


def get_product(product_id: str) -> Product | None:
    return _BY_ID.get(product_id)
