"""Inventory: a list in memory, mirrored to a text file. No database.

"""
import base64
import json
import os
import threading
import time
import uuid

from core.config import ROOT, settings

FIELDS = ("id", "type", "model", "zone", "status", "photo", "equipment_id",
          "manufacturer", "source", "why", "scanned", "created_at")


class Store:
    def __init__(self):
        self.path = os.path.join(ROOT, settings.inventory_path)
        self.captures = os.path.join(ROOT, settings.captures_dir)
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        os.makedirs(self.captures, exist_ok=True)
        self._lock = threading.Lock()
        self.items = self._load()

    def _load(self):
        if not os.path.exists(self.path):
            return []
        items = []
        with open(self.path, encoding="utf-8") as f:
            for n, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                try:
                    items.append(json.loads(line))
                except ValueError:
                    print("inventory.txt: skipped unreadable line %d" % n)
        return items

    def _save(self):
        # Write then rename, so a crash mid-write cannot truncate the file.
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write("# one JSON record per line - safe to edit or delete lines\n")
            for it in self.items:
                f.write(json.dumps(it, ensure_ascii=False) + "\n")
        os.replace(tmp, self.path)

    def _save_photo(self, item_id, data_url):
        if not data_url or not data_url.startswith("data:"):
            return None
        try:
            raw = base64.b64decode(data_url.split(",", 1)[-1])
        except Exception:
            return None
        name = "%s.jpg" % item_id
        with open(os.path.join(self.captures, name), "wb") as f:
            f.write(raw)
        return name

    def all(self):
        return list(self.items)

    def add(self, data):
        with self._lock:
            item = {k: data.get(k) for k in FIELDS}
            item["id"] = uuid.uuid4().hex[:12]
            item["created_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            item["status"] = data.get("status") or "Needs review"
            item["scanned"] = bool(data.get("scanned"))
            item["photo"] = self._save_photo(item["id"], data.get("photo"))
            self.items.insert(0, item)
            self._save()
            return item

    def update(self, item_id, changes):
        with self._lock:
            item = next((i for i in self.items if i["id"] == item_id), None)
            if item is None:
                return None
            for key, value in changes.items():
                if key in FIELDS and key not in ("id", "photo", "created_at"):
                    item[key] = value
            self._save()
            return item

    def delete(self, item_id):
        with self._lock:
            before = len(self.items)
            self.items = [i for i in self.items if i["id"] != item_id]
            if len(self.items) == before:
                return False
            photo = os.path.join(self.captures, "%s.jpg" % item_id)
            if os.path.exists(photo):
                os.remove(photo)
            self._save()
            return True


store = Store()
