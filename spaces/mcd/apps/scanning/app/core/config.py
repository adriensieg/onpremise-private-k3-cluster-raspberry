"""Settings from the environment (.env in development)."""
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Settings:
    def __init__(self):
        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("PORT", "8000"))

        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

        self.catalog_path = os.getenv("CATALOG_PATH", "data/equipment_catalog.json")
        self.inventory_path = os.getenv("INVENTORY_PATH", "/data/inventory.txt")
        self.captures_dir = os.getenv("CAPTURES_DIR", "/data/captures")

        # Keep SOURCE_SIDE in step with UPLOAD_MAX_SIDE in static/script.js.
        self.source_side = int(os.getenv("SOURCE_SIDE", "3072"))
        self.detect_side = int(os.getenv("DETECT_SIDE", "1024"))
        self.crop_side = int(os.getenv("CROP_SIDE", "1536"))


settings = Settings()