"""The reference database, loaded once at import."""
import json
import os
import re

from core.config import ROOT, settings

OPERATOR_WORDS = ("mcdonald", "mcdonalds", "mccafe")

# Last-resort label lookup. Categories like HLZ and ABS are internal acronyms a
# model will not volunteer, so it describes the machine instead and the
# detection is thrown away. Checked in order; the specific ones come first.
CATEGORY_ALIASES = (
    ("soft serve", "Shake / Sundae"), ("ice cream", "Shake / Sundae"),
    ("milkshake", "Shake / Sundae"), ("sundae", "Shake / Sundae"),
    ("shake", "Shake / Sundae"),
    ("blended ice", "Blended Ice"), ("frappe", "Blended Ice"),
    ("smoothie", "Blended Ice"), ("ice beverage", "Blended Ice"),
    ("holding cabinet", "UHC"), ("universal holding", "UHC"),
    ("warming cabinet", "UHC"),
    ("fry holding", "HLZ"), ("fry bag", "HLZ"), ("fry/bag", "HLZ"),
    ("bagging station", "HLZ"), ("holding station", "HLZ"),
    ("holding zone", "HLZ"), ("landing zone", "HLZ"), ("fry dump", "HLZ"),
    ("fry warmer", "HLZ"), ("fry station", "HLZ"), ("bag station", "HLZ"),
    ("deep fry", "Fryer"), ("vat fry", "Fryer"),
    ("clamshell", "Grill"), ("griddle", "Grill"), ("platen", "Grill"),
    ("espresso", "Coffee / Espresso"), ("coffee", "Coffee / Espresso"),
    ("brewer", "Coffee / Espresso"),
    ("orange juice", "OJ Dispenser"), ("cold brew", "OJ Dispenser"),
    ("juice", "OJ Dispenser"),
    ("sweetener", "Cream Dispenser"), ("sugar dispenser", "Cream Dispenser"),
    ("cream", "Cream Dispenser"),
    ("hot water", "Hot Water"), ("water tower", "Hot Water"),
    ("beverage system", "ABS"), ("drink tower", "ABS"),
    ("beverage dispenser", "ABS"), ("soda", "ABS"),
    ("combi", "Oven"), ("convection oven", "Oven"),
    ("bun steamer", "Steamer"), ("steam", "Steamer"),
    ("refrigerat", "Refrigeration"), ("freezer", "Refrigeration"),
    ("fridge", "Refrigeration"), ("cooler", "Refrigeration"),
    ("reach-in", "Refrigeration"), ("reach in", "Refrigeration"),
    ("undercounter", "Refrigeration"),
)


def _key(text):
    return re.sub(r"[^a-z0-9]", "", (text or "").lower())


class Catalog:
    def __init__(self, path=None):
        with open(os.path.join(ROOT, path or settings.catalog_path)) as f:
            self.data = json.load(f)

        self.equipment = self.data["equipment"]
        self.by_id = {e["equipment_id"]: e for e in self.equipment}

        self.by_category = {}
        for e in self.equipment:
            self.by_category.setdefault(e["category"], []).append(e)

        self.images = {}
        for e in self.equipment:
            for img in e["reference_images"]:
                p = os.path.join(ROOT, img["path"])
                if os.path.exists(p):
                    with open(p, "rb") as f:
                        self.images[img["path"]] = f.read()

        self.brands = self._index_brands()

    def _index_brands(self):
        """Map wordmarks to manufacturers, e.g. LOV -> Henny Penny.

        text_features also holds button labels, so only trust an entry the
        equipment_id or manufacturer name backs up.
        """
        brands = {}
        for e in self.equipment:
            maker, eid = _key(e["manufacturer"]), _key(e["equipment_id"])
            for text in [e["manufacturer"]] + e["identification_features"]["text_features"]:
                key = _key(text)
                if len(key) < 3 or any(w in key for w in OPERATOR_WORDS):
                    continue
                if key.startswith(maker) or key in eid:
                    brands.setdefault(key, e["manufacturer"])
        return brands

    def categories(self):
        return sorted(self.by_category)

    def models_for(self, category):
        return [{"equipment_id": e["equipment_id"], "manufacturer": e["manufacturer"],
                 "model": e["model"], "display_name": e["display_name"]}
                for e in self.by_category.get(category, [])]

    def category_for_label(self, label):
        """Fallback lookup: equipment_type, then display name, then aliases.

        Aliases run last, so they can only rescue a label that would otherwise
        be dropped - they never override a match found above.
        """
        low = (label or "").lower()
        words = re.sub(r"[^a-z0-9]", " ", low).split()
        if not words:
            return None
        for e in self.equipment:
            target = re.sub(r"[^a-z0-9]", " ", e["equipment_type"].lower()).split()
            if target and all(w in words for w in target):
                return e["category"]
        for e in self.equipment:
            if e["display_name"].lower().startswith(low[:12]):
                return e["category"]
        for keyword, category in CATEGORY_ALIASES:
            if keyword in low and category in self.by_category:
                return category
        return None

    def resolve_brand(self, text):
        return self.brands.get(_key(text))


catalog = Catalog()
