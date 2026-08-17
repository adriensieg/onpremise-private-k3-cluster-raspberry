"""Gemini vision calls. Auth is a Gemini API key - no Vertex AI, no gcloud ADC.

"""
import base64
import io
import json
import re
import time

from PIL import Image, ImageOps

from core.cache import detect_cache, identify_cache, key_for, version
from core.catalog import catalog
from core.config import settings

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    HEIC_SUPPORTED = True
except ImportError:
    HEIC_SUPPORTED = False

_client = None


def client():
    global _client
    if _client is None:
        from google import genai
        if not settings.api_key:
            raise RuntimeError("GEMINI_API_KEY is not set in .env "
                               "(get one at https://aistudio.google.com/apikey)")
        _client = genai.Client(api_key=settings.api_key)
        print("Gemini: %s" % settings.gemini_model)
    return _client


def _config(types, max_tokens):
    # Thinking tokens count against max_output_tokens, and on a prompt that
    # lists the whole catalog they ate the budget and the reply came back empty.
    return types.GenerateContentConfig(
        temperature=0.0,
        max_output_tokens=max_tokens,
        response_mime_type="application/json",
        thinking_config=types.ThinkingConfig(thinking_budget=0))


# ==== images ==========================================================================
def load_image(raw):
    return ImageOps.exif_transpose(Image.open(io.BytesIO(raw)))


def encode(im, side=None):
    out = im.copy()
    out.thumbnail((side or settings.detect_side,) * 2)
    buf = io.BytesIO()
    out.convert("RGB").save(buf, "JPEG", quality=85)
    return buf.getvalue()


def to_jpeg(raw, side=None):
    """Normalise any upload to JPEG. Kept for callers that only have bytes."""
    return encode(load_image(raw), side)


def decode_data_url(url):
    return base64.b64decode((url or "").split(",", 1)[-1])


def _as_data_url(jpeg):
    return "data:image/jpeg;base64," + base64.b64encode(jpeg).decode()


def preview(jpeg_bytes, side=640):
    """Browser-renderable copy, so the client can show a HEIC it cannot open."""
    return _as_data_url(to_jpeg(jpeg_bytes, side))


def crop(source_im, box, pad=0.04):
    w, h = source_im.size
    x0, y0 = max(0, int((box[0] - pad) * w)), max(0, int((box[1] - pad) * h))
    x1, y1 = min(w, int((box[2] + pad) * w)), min(h, int((box[3] + pad) * h))
    if x1 <= x0 or y1 <= y0:
        return None
    c = source_im.crop((x0, y0, x1, y1))
    c.thumbnail((settings.crop_side,) * 2)
    buf = io.BytesIO()
    c.convert("RGB").save(buf, "JPEG", quality=88)
    return _as_data_url(buf.getvalue())


def parse_json(text):
    text = re.sub(r"^```(?:json)?|```$", "", (text or "").strip(), flags=re.M).strip()
    span = re.search(r"[\[{].*[\]}]", text, re.S)
    for candidate in [text] + ([span.group(0)] if span else []):
        try:
            return json.loads(candidate)
        except ValueError:
            pass
    salvaged = []
    for chunk in re.findall(r"\{[^{}]*\}", text, re.S):
        try:
            salvaged.append(json.loads(chunk))
        except ValueError:
            pass
    return salvaged


# ==== detect ==========================================================================
DETECT_PROMPT = """Find every piece of commercial kitchen equipment in this photo.

Report a machine as a WHOLE UNIT. A control panel, door, drawer or display is
part of a machine, never an item of its own. Ventilation hoods, bare counters,
shelves, racks, trolleys, sinks and the stand a machine sits on are not
equipment - leave them out.

One exception: a holding or staging station counts as equipment even though it
looks like a counter with racks. If a counter or rack assembly has its own
timer, controller or display mounted on it or on a canopy above it, report it,
and box the whole assembly from the floor to the top of that controller.

Only report a machine that is SUBSTANTIALLY VISIBLE: most of the unit is in
frame and you could identify it from what you can see. Skip anything in the far
background, anything mostly hidden behind another machine, and anything you are
inferring rather than seeing.

box_2d must enclose the ENTIRE machine - from its base or legs to the top of its
housing, and the full width including the control panel. Do not box only the
part carrying a logo, a single column of cups, or one door: a box around a
fragment cannot be identified.

The machine is the assembly that carries the CONTROL PANEL - keypad, buttons or
display. Cup dispensers, hoppers, drip trays and racks attached to it belong
inside the same box. If a column of cups or a hopper stands apart from any
control panel, it is not a machine of its own - leave it out.

Give each one the closest category:
{categories}

Return a JSON list. Each entry:
  "box_2d": [y0, x0, y1, x1] normalised 0-1000
  "label":  a category from the list above - nothing else
  "why":    at most 8 words of visual evidence
  "is_appliance": true for a self-contained machine that cooks, holds, chills or
                  dispenses, and for a holding or staging station that has its
                  own timer or controller
"""

# Same string as before, formatted once instead of on every request.
_DETECT_PROMPT = DETECT_PROMPT.format(
    categories="\n".join("  - " + c for c in catalog.categories()))


def detect(jpeg_bytes, source_im=None):
    ck = key_for(jpeg_bytes, version(_DETECT_PROMPT))
    items = detect_cache.get(ck)
    if items is None:
        items = _detect_boxes(jpeg_bytes)
        if items:                      # never cache a failure - it would stick
            detect_cache.put(ck, items)
    else:
        print("  detect: cached, %d item(s)" % len(items))

    for it in items:
        it["crop"] = crop(source_im, it["box"])
    return items


def _detect_boxes(jpeg_bytes):
    """One Gemini call, then the box filters. Logic unchanged."""
    from google.genai import types
    t0 = time.time()
    resp = client().models.generate_content(
        model=settings.gemini_model,
        contents=[types.Part.from_bytes(data=jpeg_bytes, mime_type="image/jpeg"),
                  _DETECT_PROMPT],
        config=_config(types, 8192))

    entries = parse_json(resp.text)
    if isinstance(entries, dict):
        entries = [entries]

    items = []
    for e in entries:
        if not isinstance(e, dict) or e.get("is_appliance") is False:
            continue
        box = e.get("box_2d")
        if not isinstance(box, (list, tuple)) or len(box) != 4:
            continue
        y0, x0, y1, x1 = [max(0.0, min(1000.0, float(v))) / 1000.0 for v in box]
        if x1 <= x0 or y1 <= y0 or (x1 - x0) * (y1 - y0) > 0.985:
            continue
        label = str(e.get("label") or "").strip()
        category = match_category(label)
        if category is None:
            print("     skipped unknown label %r" % label)
            continue
        items.append({"box": [x0, y0, x1, y1], "category": category,
                      "why": str(e.get("why") or "")[:120]})

    whole = [it for it in items if not is_fragment(it["box"])]
    if len(whole) < len(items):
        print("     dropped %d fragment box(es)" % (len(items) - len(whole)))

    # If every box is a clipped sliver the photo is a close-up shot edge to
    # edge, so keep the first one rather than come back with nothing.
    items = [it for it in whole if not is_edge_sliver(it["box"])] or whole[:1]
    items = drop_support_bases(items)

    print("  detect: %.2fs, %d item(s)" % (time.time() - t0, len(items)))
    return items


def match_category(label):

    low = (label or "").lower()
    if not low:
        return None
    known = catalog.categories()
    exact = next((c for c in known if c.lower() == low), None)
    partial = next((c for c in known if c.lower() in low or low in c.lower()), None)
    return exact or partial or catalog.category_for_label(label)


def is_fragment(box, min_side=0.12, max_aspect=4.0):

    w, h = box[2] - box[0], box[3] - box[1]
    if w <= 0 or h <= 0:
        return True
    return min(w, h) < min_side or max(w / h, h / w) > max_aspect


def is_edge_sliver(box, tol=0.02, span=0.22, area=0.03):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    if not (x0 <= tol or y0 <= tol or x1 >= 1 - tol or y1 >= 1 - tol):
        return False
    if w * h < area:
        return True
    return ((w < span and (x0 <= tol or x1 >= 1 - tol))
            or (h < span and (y0 <= tol or y1 >= 1 - tol)))


def drop_support_bases(items, overlap=0.6):
    kept = []
    for it in items:
        x0, y0, x1, _ = it["box"]
        carrying = False
        for other in items:
            if other is it:
                continue
            ox0, _, ox1, oy1 = other["box"]
            shared = min(x1, ox1) - max(x0, ox0)
            if y0 >= oy1 - 0.05 and shared > 0 and shared / max(1e-6, ox1 - ox0) >= overlap:
                carrying = True
                break
        if not carrying:
            kept.append(it)
    return kept or items


# ==== identify ==========================================================================
IDENTIFY_PROMPT = """The first image is one piece of equipment from a McDonald's
kitchen. The remaining images are every model we stock:
{listing}

STEP 1 - read the wordmark printed on the unit in the FIRST IMAGE ONLY: the
badge, the control panel, the data plate. Report a wordmark ONLY if you can make
out its individual letters. A badge, plate or blank oval whose text you cannot
resolve is NOT a wordmark - return "" for brand_read. Several units in the list
carry no brand name at all, so "" is a common and correct answer. Do not name a
manufacturer because the equipment looks like theirs, because a badge sits where
one would, or because the reference images show one. "McDonald's" and "McCafe"
are the operator, not the manufacturer.

STEP 2 - if you read a wordmark, only answer with a reference by that same
manufacturer. A unit marked TAYLOR is not a Garland, whatever the shape. If you
read nothing, prefer a reference whose "brand on unit" line says it carries no
brand name.

STEP 3 - otherwise compare the control panel layout and the number of
vats / platens / shelves / doors.

Reply with JSON only:
{{"brand_read": "<wordmark on the unit, or empty if none legible>",
  "equipment_id": "<an id from the list, or empty if none match>",
  "confidence": "high" | "medium" | "low",
  "why": "<a few words of visual evidence>"}}

An empty equipment_id is a valid answer - we do not stock everything."""

_ref_parts = None
_ref_count = 0


def _reference_parts():
    """Reference images and the id listing, built once - they never change."""
    global _ref_parts, _ref_count
    if _ref_parts is None:
        from google.genai import types
        parts, listing = [], []
        for e in catalog.equipment:
            data = catalog.images.get(e["reference_images"][0]["path"])
            if data is None:
                continue
            parts.append(types.Part.from_bytes(data=data, mime_type="image/webp"))
            parts.append("(previous image = %s)" % e["equipment_id"])
            f = e["identification_features"]
            marks = [t for t in f["text_features"] if catalog.resolve_brand(t)]
            listing.append(
                "  %s - %s [%s] (%s)\n      look for: %s\n      brand on unit: %s"
                % (e["equipment_id"], e["display_name"], e["category"],
                   e["manufacturer"], "; ".join(f["visual_features"][:4]) or "-",
                   ", ".join(marks) if marks
                   else "NONE - this unit carries no brand name"))
        parts.append(IDENTIFY_PROMPT.format(listing="\n".join(listing)))
        _ref_parts, _ref_count = parts, len(listing)
    return _ref_parts


def identify(jpeg_bytes):
    """Identify a crop. Cached, so a re-uploaded photo costs no calls."""
    ck = key_for(jpeg_bytes, version(IDENTIFY_PROMPT))
    hit = identify_cache.get(ck)
    if hit is not None:
        print("  identify: cached -> %s" % (hit.get("equipment_id") or "no match"))
        return hit
    result = _identify_record(jpeg_bytes)
    return identify_cache.put(ck, result) if result.get("model") else result


_STOP = set("the a an on of and or with in at to for both its this that is are no".split())


def _expects_wordmark(e):
    """Does the catalog say this unit carries a readable brand name?"""
    return any(catalog.resolve_brand(t)
               for t in e["identification_features"]["text_features"])


def _feature_words(e):
    text = " ".join(e["identification_features"]["visual_features"]).lower()
    return {w for w in re.sub(r"[^a-z0-9]", " ", text).split()
            if len(w) > 2 and w not in _STOP}


def _looks_alike(a, b, threshold=0.35):

    wa, wb = _feature_words(a), _feature_words(b)
    return len(wa & wb) / max(1, len(wa | wb)) >= threshold


def _identify_record(jpeg_bytes):

    from google.genai import types
    parts = [types.Part.from_bytes(data=jpeg_bytes, mime_type="image/jpeg")]
    parts.extend(_reference_parts())

    t0 = time.time()
    resp = client().models.generate_content(model=settings.gemini_model,
                                            contents=parts,
                                            config=_config(types, 512))
    got = parse_json(resp.text)
    if isinstance(got, list):
        got = got[0] if got else {}

    record = catalog.by_id.get(str(got.get("equipment_id") or "").strip())
    brand = catalog.resolve_brand(str(got.get("brand_read") or ""))
    brand_read_raw = str(got.get("brand_read") or "").strip()

    # Nothing legible, but the chosen record should have shown a name. Switch to
    # an unbranded twin only if the catalog says the two look alike.
    if record and not brand_read_raw and _expects_wordmark(record):
        twins = [e for e in catalog.by_category.get(record["category"], [])
                 if not _expects_wordmark(e) and _looks_alike(record, e)]
        if len(twins) == 1:
            print("     no brand legible: %s -> %s"
                  % (record["display_name"], twins[0]["display_name"]))
            record = twins[0]
            got["why"] = "no brand legible; matches the unbranded variant"

    # A wordmark outranks a shape match: a Taylor and a Garland look alike.
    if record and brand and brand != record["manufacturer"]:
        print("     rejected %s: unit reads %s" % (record["display_name"], brand))
        record = None

    # One catalog entry for that brand settles it even on a partial view.
    if not record and brand:
        same = [e for e in catalog.equipment if e["manufacturer"] == brand]
        if len(same) == 1:
            record = same[0]
            got["why"] = "wordmark %s; only one in the catalog" % brand

    print("  identify: %d refs, %.2fs -> %s"
          % (_ref_count, time.time() - t0,
             record["equipment_id"] if record else "no match"))

    if not record:
        return _unmatched(jpeg_bytes, str(got.get("why") or ""), brand)
    return {"equipment_id": record["equipment_id"], "model": record["display_name"],
            "manufacturer": record["manufacturer"], "category": record["category"],
            "source": "catalog", "confidence": got.get("confidence", "medium"),
            "why": str(got.get("why") or "")[:120]}


READ_PROMPT = """Read what is printed on this equipment - brand badges, control
panel text, the data plate. Report only text you can actually see.

Reply with JSON only:
{"manufacturer": "<brand read off the unit, or empty>",
 "model": "<model text read off the unit, or empty>",
 "confidence": "high" | "medium" | "low"}"""


def _unmatched(jpeg_bytes, why, brand=None):
    """No match: report what is printed on the unit so it still gets a name."""
    name = brand or ""
    if not name:
        try:
            from google.genai import types
            resp = client().models.generate_content(
                model=settings.gemini_model,
                contents=[types.Part.from_bytes(data=jpeg_bytes, mime_type="image/jpeg"),
                          READ_PROMPT],
                config=_config(types, 512))
            got = parse_json(resp.text)
            if isinstance(got, list):
                got = got[0] if got else {}
            name = " ".join(x for x in [got.get("manufacturer"), got.get("model")] if x)
        except Exception as e:
            print("     read-from-unit failed: %s" % type(e).__name__)
            name = ""
    return {"equipment_id": None, "model": name or None, "manufacturer": brand,
            "source": "read_from_unit" if name else None,
            "confidence": "medium" if name else "low",
            "why": ("read off the unit: " + name) if name else why[:120]}