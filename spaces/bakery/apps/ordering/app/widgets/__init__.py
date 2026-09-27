"""Widget asset loader.

Each widget lives as a standalone `.html` file in this directory for readable
editing. Two fragments are shared across all of them and injected at load time
via placeholders, so the design tokens and the `window.openai` bootstrap are
written once:

    {{THEME_CSS}}   ->  _theme.css     (design tokens + base styles)
    {{BRIDGE_JS}}   ->  _bridge.js     (host bridge, helpers, SVG icons)

The composed HTML is cached in memory after first read. Set the environment
variable ``BAKERY_WIDGET_NO_CACHE=1`` to reload from disk on every request,
which is handy while iterating on widget markup.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

_DIR = Path(__file__).parent


def _read(name: str) -> str:
    return (_DIR / name).read_text(encoding="utf-8")


def _compose(widget_file: str) -> str:
    html = _read(widget_file)
    html = html.replace("{{THEME_CSS}}", _read("_theme.css"))
    html = html.replace("{{BRIDGE_JS}}", _read("_bridge.js"))
    return html


@lru_cache(maxsize=None)
def _compose_cached(widget_file: str) -> str:
    return _compose(widget_file)


def render_widget(widget_file: str) -> str:
    """Return the fully composed HTML for a widget file (e.g. 'catalog.html')."""
    if os.getenv("BAKERY_WIDGET_NO_CACHE") == "1":
        return _compose(widget_file)
    return _compose_cached(widget_file)
