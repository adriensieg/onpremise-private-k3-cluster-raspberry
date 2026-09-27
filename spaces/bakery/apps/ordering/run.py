"""Local entrypoint: `python run.py` (or the `bakery-mcp` console script).

For production you'd typically run uvicorn/gunicorn directly against
``app.main:app``; this wrapper just makes local development a single command.
"""

from __future__ import annotations

import uvicorn

from app.config import settings


def main() -> None:
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        reload=False,
    )


if __name__ == "__main__":
    main()
