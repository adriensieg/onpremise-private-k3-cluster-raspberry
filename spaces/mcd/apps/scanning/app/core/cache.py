"""Response cache, so the same image is never sent to Gemini twice.
"""
import copy
import hashlib
import json
import os
import threading

from core.config import ROOT, settings

CACHE_DIR = os.getenv("CACHE_DIR", "data/cache")
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "1") not in ("0", "false", "False", "")


def _fingerprint(*parts):
    h = hashlib.sha256()
    for p in parts:
        h.update(str(p).encode("utf-8"))
    return h.hexdigest()[:12]


def key_for(image_bytes, version):
    return "%s-%s" % (hashlib.sha256(image_bytes).hexdigest()[:24], version)


def version(prompt):
    return _fingerprint(settings.gemini_model, prompt)


class Cache:
    def __init__(self, name):
        directory = os.path.join(ROOT, CACHE_DIR)
        os.makedirs(directory, exist_ok=True)
        self.path = os.path.join(directory, "%s.txt" % name)
        self.name = name
        self._lock = threading.Lock()
        self.entries = self._load()

    def _load(self):
        entries = {}
        if not os.path.exists(self.path):
            return entries
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                try:
                    row = json.loads(line)
                    entries[row["key"]] = row["value"]
                except (ValueError, KeyError):
                    continue
        if entries:
            print("cache: %d %s entr(ies) loaded" % (len(entries), self.name))
        return entries

    def get(self, key):
        # A copy: detect() attaches a crop to what it gets back, and those must
        # never end up stored.
        if not CACHE_ENABLED:
            return None
        hit = self.entries.get(key)
        return copy.deepcopy(hit) if hit is not None else None

    def put(self, key, value):
        if not CACHE_ENABLED:
            return value
        with self._lock:
            self.entries[key] = copy.deepcopy(value)
            # Append-only, so a hit costs no disk work.
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"key": key, "value": value},
                                   ensure_ascii=False) + "\n")
        return value

    def clear(self):
        with self._lock:
            self.entries = {}
            if os.path.exists(self.path):
                os.remove(self.path)


detect_cache = Cache("detect")
identify_cache = Cache("identify")
