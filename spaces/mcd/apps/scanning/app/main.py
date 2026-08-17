"""Restaurant Equipment Identification.

    GET    /                     UI
    GET    /api/health           service and catalog status
    GET    /api/catalog          categories and models
    GET    /api/equipment/{id}   one reference record
    POST   /api/detect           photo -> detected assets
    POST   /api/identify         crop  -> specific model
    GET    /api/inventory        every saved item
    POST   /api/inventory        save one or more items
    PATCH  /api/inventory/{id}   edit a saved item
    DELETE /api/inventory/{id}   remove a saved item
"""
import io
import os

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import Image
from pydantic import BaseModel, Field
from starlette.requests import Request

from core.catalog import catalog
from core.config import ROOT, settings
from core.store import store
from core.vision import (HEIC_SUPPORTED, decode_data_url, detect, encode,
                         identify, load_image, preview)

app = FastAPI(title="Restaurant Equipment Identification", version="1.1.0")
app.mount("/static", StaticFiles(directory=os.path.join(ROOT, "static")), name="static")
app.mount("/captures", StaticFiles(directory=store.captures), name="captures")
templates = Jinja2Templates(directory=os.path.join(ROOT, "templates"))


class DetectRequest(BaseModel):
    image: str = Field(..., description="Data URL or base64. HEIC, JPEG, PNG, WebP.")


class Detection(BaseModel):
    box: list = Field(..., description="[x0, y0, x1, y1] normalised 0-1")
    category: str
    why: str = ""
    crop: str | None = None


class DetectResponse(BaseModel):
    items: list[Detection]
    preview: str | None = None


class IdentifyRequest(BaseModel):
    image: str = Field(..., description="A crop returned by /api/detect.")
    # Sent by the client but ignored on purpose - detection's category is
    # unreliable. Declared so validation does not reject the payload.
    category: str | None = None
    hint: str | None = None


class IdentifyResponse(BaseModel):
    equipment_id: str | None = None
    model: str | None = None
    manufacturer: str | None = None
    category: str | None = None
    confidence: str = "low"
    why: str = ""
    source: str | None = Field(None, description="'catalog' or 'read_from_unit'")


class InventoryItem(BaseModel):
    type: str
    model: str = ""
    zone: str = ""
    status: str = "Needs review"
    photo: str | None = Field(None, description="Data URL; stored as a JPEG file.")
    equipment_id: str | None = None
    manufacturer: str | None = None
    source: str | None = None
    why: str = ""
    scanned: bool = False


class InventoryPatch(BaseModel):
    type: str | None = None
    model: str | None = None
    zone: str | None = None
    status: str | None = None
    why: str | None = None
    equipment_id: str | None = None


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {})


@app.get("/api/health")
def health():
    return {"status": "ok",
            "equipment_count": len(catalog.equipment),
            "categories": len(catalog.categories()),
            "reference_images": len(catalog.images),
            "inventory_count": len(store.items),
            "model": settings.gemini_model}


@app.get("/api/catalog")
def get_catalog():
    return {"categories": {c: catalog.models_for(c) for c in catalog.categories()}}


@app.get("/api/equipment/{equipment_id}")
def get_equipment(equipment_id: str):
    record = catalog.by_id.get(equipment_id)
    if not record:
        raise HTTPException(status_code=404, detail="unknown equipment_id")
    return record


@app.post("/api/detect", response_model=DetectResponse)
def api_detect(req: DetectRequest):
    raw = decode_data_url(req.image)
    try:
        # One decode, two copies: a small one to detect on, a source one to
        # cut crops from.
        image = load_image(raw)
        small = encode(image, settings.detect_side)
        source = Image.open(io.BytesIO(encode(image, settings.source_side)))
    except Exception as e:
        raise HTTPException(status_code=400,
                            detail="Could not read the image (%s). For .heic "
                                   "install pillow-heif." % type(e).__name__)
    try:
        return {"items": detect(small, source), "preview": preview(small)}
    except Exception as e:
        raise HTTPException(status_code=502, detail="%s: %s" % (type(e).__name__, e))


@app.post("/api/identify", response_model=IdentifyResponse)
def api_identify(req: IdentifyRequest):
    # Not downscaled - the crop is already sized to keep a badge legible.
    try:
        jpeg = decode_data_url(req.image)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    try:
        return identify(jpeg)
    except Exception as e:
        raise HTTPException(status_code=502, detail="%s: %s" % (type(e).__name__, e))


@app.get("/api/inventory")
def list_inventory():
    return {"items": store.all()}


@app.post("/api/inventory")
def add_inventory(items: list[InventoryItem]):
    # Each add goes to the front, so reverse to keep the reviewed order.
    added = [store.add(i.model_dump()) for i in reversed(items)]
    return {"items": list(reversed(added))}


@app.patch("/api/inventory/{item_id}")
def patch_inventory(item_id: str, changes: InventoryPatch):
    item = store.update(item_id, changes.model_dump(exclude_none=True))
    if item is None:
        raise HTTPException(status_code=404, detail="unknown item id")
    return item


@app.delete("/api/inventory/{item_id}")
def delete_inventory(item_id: str):
    if not store.delete(item_id):
        raise HTTPException(status_code=404, detail="unknown item id")
    return {"deleted": item_id}


if __name__ == "__main__":
    print("catalog:   %d records, %d categories, %d images"
          % (len(catalog.equipment), len(catalog.categories()), len(catalog.images)))
    print("inventory: %d item(s) in %s" % (len(store.items), settings.inventory_path))
    if not HEIC_SUPPORTED:
        print("WARNING: pillow-heif not installed - iPhone .heic uploads will fail")
    if not settings.api_key:
        print("WARNING: GEMINI_API_KEY is not set in .env")
    print("open http://localhost:%d  (camera needs localhost)" % settings.port)
    uvicorn.run(app, host=settings.host, port=settings.port)
