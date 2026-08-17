"""Restaurant Equipment Identification.

    GET    {ROOT}/                     UI
    GET    {ROOT}/api/health           service and catalog status
    GET    {ROOT}/api/catalog          categories and models
    GET    {ROOT}/api/equipment/{id}   one reference record
    POST   {ROOT}/api/detect           photo -> detected assets
    POST   {ROOT}/api/identify         crop  -> specific model
    GET    {ROOT}/api/inventory        every saved item
    POST   {ROOT}/api/inventory        save one or more items
    PATCH  {ROOT}/api/inventory/{id}   edit a saved item
    DELETE {ROOT}/api/inventory/{id}   remove a saved item

ROOT_PATH (e.g. /scanning) prefixes every route so the app serves the full
path the ingress forwards. Empty in local dev, so paths are bare.
"""
import io
import os

import uvicorn
from fastapi import APIRouter, FastAPI, HTTPException
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

# ROOT_PATH like "/scanning"; "" locally. Strip any trailing slash.
PREFIX = settings.root_path.rstrip("/")

app = FastAPI(title="Restaurant Equipment Identification", version="1.1.0")

# Static + captures served under the same prefix so absolute asset URLs
# in the page resolve behind the ingress.
app.mount(PREFIX + "/static",
          StaticFiles(directory=os.path.join(ROOT, "static")), name="static")
app.mount(PREFIX + "/captures",
          StaticFiles(directory=store.captures), name="captures")
templates = Jinja2Templates(directory=os.path.join(ROOT, "templates"))

router = APIRouter(prefix=PREFIX)


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


@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    # Pass the prefix so the template can build correct asset/API URLs.
    return templates.TemplateResponse(request, "index.html", {"root_path": PREFIX})


@router.get("/api/health")
def health():
    return {"status": "ok",
            "equipment_count": len(catalog.equipment),
            "categories": len(catalog.categories()),
            "reference_images": len(catalog.images),
            "inventory_count": len(store.items),
            "model": settings.gemini_model}


@router.get("/api/catalog")
def get_catalog():
    return {"categories": {c: catalog.models_for(c) for c in catalog.categories()}}


@router.get("/api/equipment/{equipment_id}")
def get_equipment(equipment_id: str):
    record = catalog.by_id.get(equipment_id)
    if not record:
        raise HTTPException(status_code=404, detail="unknown equipment_id")
    return record


@router.post("/api/detect", response_model=DetectResponse)
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


@router.post("/api/identify", response_model=IdentifyResponse)
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


@router.get("/api/inventory")
def list_inventory():
    return {"items": store.all()}


@router.post("/api/inventory")
def add_inventory(items: list[InventoryItem]):
    # Each add goes to the front, so reverse to keep the reviewed order.
    added = [store.add(i.model_dump()) for i in reversed(items)]
    return {"items": list(reversed(added))}


@router.patch("/api/inventory/{item_id}")
def patch_inventory(item_id: str, changes: InventoryPatch):
    item = store.update(item_id, changes.model_dump(exclude_none=True))
    if item is None:
        raise HTTPException(status_code=404, detail="unknown item id")
    return item


@router.delete("/api/inventory/{item_id}")
def delete_inventory(item_id: str):
    if not store.delete(item_id):
        raise HTTPException(status_code=404, detail="unknown item id")
    return {"deleted": item_id}


app.include_router(router)


if __name__ == "__main__":
    print("catalog:   %d records, %d categories, %d images"
          % (len(catalog.equipment), len(catalog.categories()), len(catalog.images)))
    print("inventory: %d item(s) in %s" % (len(store.items), settings.inventory_path))
    print("root_path: %r" % PREFIX)
    if not HEIC_SUPPORTED:
        print("WARNING: pillow-heif not installed - iPhone .heic uploads will fail")
    if not settings.api_key:
        print("WARNING: GEMINI_API_KEY is not set in .env")
    print("open http://localhost:%d%s/" % (settings.port, PREFIX))
    uvicorn.run(app, host=settings.host, port=settings.port)