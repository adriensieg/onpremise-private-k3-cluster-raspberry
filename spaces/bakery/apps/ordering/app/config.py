"""Configuration, read once from the environment.

No secrets or auth here by design — this first prototype is intentionally
frictionless (no OAuth, no identity provider).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _split(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    host: str = field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8000")))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    # The public URL the server is reachable at (used only for docs/health).
    public_url: str = field(
        default_factory=lambda: os.getenv("PUBLIC_URL", "http://bakery.devailab.work")
    )

    # Origins allowed to call the MCP endpoint from a browser. ChatGPT widgets
    # run under chatgpt.com / openai.com. Override with CORS_ORIGINS (comma-sep).
    cors_origins: list[str] = field(
        default_factory=lambda: _split(
            os.getenv(
                "CORS_ORIGINS",
                "https://chatgpt.com,https://chat.openai.com,https://openai.com",
            )
        )
    )

    # If "1", MCP POSTs return a single JSON body instead of an SSE stream.
    # Leave off for ChatGPT.
    json_response: bool = field(
        default_factory=lambda: os.getenv("MCP_JSON_RESPONSE", "0") == "1"
    )


settings = Settings()
