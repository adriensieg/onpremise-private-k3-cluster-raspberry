import io
import json
import os
import re
import sys
from collections import Counter

import pymupdf
from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(HERE, "data", "images")
DEFAULT_PDF = os.path.join(HERE, "data", "McDonalds_StoreEquipment_Identification.pdf")
IMAGE_MAX = 640

# equipment_type in the PDF -> the category the UI groups by. Add a line here
# when the PDF introduces a new type, or it falls through to "Other".
TYPE_TO_CATEGORY = {
    "fryer": "Fryer", "clamshell_grill": "Grill", "universal_holding_cabinet": "UHC",
    "steamer": "Steamer", "fry_bag_holding_station": "HLZ", "fry_holding_zone": "HLZ",
    "soft_serve_shake_freezer": "Shake / Sundae", "coffee_brewer": "Coffee / Espresso",
    "coffee_brewer_satellite": "Coffee / Espresso", "espresso_machine": "Coffee / Espresso",
    "automated_beverage_system": "ABS", "combi_oven": "Oven",
    "cream_dispenser": "Cream Dispenser", "sweetener_sugar_dispenser": "Cream Dispenser",
    "hot_water_dispenser": "Hot Water", "reach_in_refrigerator": "Refrigeration",
    "undercounter_refrigerator": "Refrigeration",
    "blended_ice_beverage_dispenser": "Blended Ice",
    "juice_cold_brew_dispenser": "OJ Dispenser",
}


def field(block, name):
    m = re.search(r'"%s":\s*"((?:[^"\\]|\\.)*)"' % name, block)
    return m.group(1).strip() if m else ""


def string_list(block, name):
    m = re.search(r'"%s":\s*\[(.*?)\]' % name, block, re.S)
    return [s.strip() for s in re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(1))] if m else []


def read_records(doc):
    """Rejoin the PDF's wrapped text, then split it on each equipment_id.

    Line wrapping breaks the JSON, so fields come out by regex, not json.loads.
    """
    text = "".join(p.get_text() for p in doc)
    text = re.sub(r'([",\[\{:])\n\s*', r"\1", text)
    text = re.sub(r'\n(?=[",\]\}])', "", text)
    text = re.sub(r"(?<=[A-Za-z0-9\-/\.\(\)])\n(?=[A-Za-z0-9])", "", text)
    text = re.sub(r"\s+", " ", text)

    records = []
    for block in re.split(r'(?=\{\s*"equipment_id")', text):
        eid = field(block, "equipment_id") if '"equipment_id"' in block else ""
        if not eid:
            continue
        etype = field(block, "equipment_type")
        imgs = re.findall(r'"image_id":\s*"([^"]+)",\s*"path":\s*"[^"]+",'
                          r'\s*"description":\s*"((?:[^"\\]|\\.)*)"', block)
        records.append({
            "equipment_id": eid,
            "equipment_type": etype,
            "category": TYPE_TO_CATEGORY.get(etype, "Other"),
            "manufacturer": field(block, "manufacturer"),
            "model": field(block, "model"),
            "display_name": field(block, "display_name"),
            "reference_images": [{"image_id": imgs[0][0] if imgs else eid + "-001",
                                  "path": "", "description": imgs[0][1] if imgs else ""}],
            "identification_features": {
                "visual_features": string_list(block, "visual_features"),
                "text_features": string_list(block, "text_features"),
            },
        })
    return records


def page_photos(doc):
    """Embedded photos in reading order, with the matrix each is placed by."""
    photos = []
    for page in doc:
        rows = []
        for info in page.get_images(full=True):
            for r in page.get_image_rects(info[0], transform=True):
                rect, matrix = r if isinstance(r, tuple) else (r, None)
                if rect.width > 60 and rect.height > 60:
                    rows.append((rect.y0, info[0], matrix))
        photos += [(xref, m) for _, xref, m in sorted(rows, key=lambda t: t[0])]
    return photos


def placement_turn(matrix):
    if matrix is None or (abs(matrix.b) < 1e-6 and abs(matrix.c) < 1e-6):
        return 0
    return -90 if matrix.b > 0 else 90


def save_images(doc, records, photos):
    os.makedirs(IMG_DIR, exist_ok=True)
    for rec, (xref, matrix) in zip(records, photos):
        pix = pymupdf.Pixmap(doc, xref)
        if pix.n - pix.alpha >= 4:
            pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
        im = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
        turn = placement_turn(matrix)
        if turn:
            im = im.rotate(turn, expand=True)
            print("   rotated %+d deg: %s" % (turn, rec["equipment_id"]))
        im.thumbnail((IMAGE_MAX, IMAGE_MAX))
        name = re.sub(r"[^A-Za-z0-9]+", "-", rec["equipment_id"]).strip("-") + ".webp"
        im.save(os.path.join(IMG_DIR, name), "WEBP", quality=86)
        rec["reference_images"][0]["path"] = "data/images/" + name


def check(records, photos):
    problems = []
    if len(records) != len(photos):
        problems.append("%d records but %d photos - they are paired in order, so "
                        "a mismatch mislabels every record after the gap"
                        % (len(records), len(photos)))
    seen = Counter(r["equipment_id"] for r in records)
    for eid, n in seen.items():
        if n > 1:
            problems.append("duplicate equipment_id: %s (x%d)" % (eid, n))
    for r in records:
        if not r["manufacturer"] or not r["display_name"]:
            problems.append("%s is missing manufacturer or display_name" % r["equipment_id"])
        if r["category"] == "Other":
            problems.append("%s: unmapped equipment_type %r - add it to TYPE_TO_CATEGORY"
                            % (r["equipment_id"], r["equipment_type"]))
    return problems


def main():
    pdf = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PDF
    doc = pymupdf.open(pdf)

    records = read_records(doc)
    photos = page_photos(doc)

    problems = check(records, photos)
    if problems:
        print("Catalog NOT written:")
        for p in problems:
            print("   - %s" % p)
        return 1

    save_images(doc, records, photos)
    catalog = {
        "schema_version": "1.0",
        "database_name": "restaurant_equipment_reference",
        "description": "Reference database for multimodal visual identification.",
        "source_document": os.path.basename(pdf),
        "equipment": records,
    }
    with open(os.path.join(HERE, "data", "equipment_catalog.json"), "w") as f:
        json.dump(catalog, f, indent=2)

    counts = Counter(r["category"] for r in records)
    print("%d records, %d categories, %d images" % (len(records), len(counts), len(photos)))
    for category, n in sorted(counts.items()):
        print("   %-18s %d" % (category, n))
    print("\nCache keys include the model and prompt, not the catalog - "
          "delete data/cache/ so old answers are not reused.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
