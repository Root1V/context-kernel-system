"""API configuration — reads settings from environment variables."""

from __future__ import annotations

import os


class Settings:
    CHAT_RATE_LIMIT: str = os.getenv("CHAT_RATE_LIMIT", "60/minute")


settings = Settings()
