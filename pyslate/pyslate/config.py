"""Runtime settings, read from environment variables."""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass, field
from pathlib import Path


def _env(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name)
    return value if value not in (None, "") else default


@dataclass
class Settings:
    data_dir: Path = field(default_factory=lambda: Path(_env("PYSLATE_DATA_DIR", "./data")))
    database_url: str | None = field(default_factory=lambda: _env("DATABASE_URL"))
    public_url: str = field(default_factory=lambda: _env("PYSLATE_PUBLIC_URL", "http://localhost:8000"))
    # Password for the shop admin console. Admin is disabled when unset.
    admin_token: str | None = field(default_factory=lambda: _env("PYSLATE_ADMIN_TOKEN"))
    # Shared secret the shop agent on the shop PC sends to pick up machine runs. API off when unset.
    agent_token: str | None = field(default_factory=lambda: _env("PYSLATE_AGENT_TOKEN"))
    # Signs admin session cookies. Set a fixed value in production so logins survive restarts.
    secret_key: str = field(default_factory=lambda: _env("PYSLATE_SECRET_KEY") or secrets.token_hex(32))
    stripe_secret_key: str | None = field(default_factory=lambda: _env("STRIPE_SECRET_KEY"))
    stripe_webhook_secret: str | None = field(default_factory=lambda: _env("STRIPE_WEBHOOK_SECRET"))
    max_upload_mb: int = field(default_factory=lambda: int(_env("PYSLATE_MAX_UPLOAD_MB", "50")))

    @property
    def upload_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def db_url(self) -> str:
        return self.database_url or f"sqlite:///{(self.data_dir / 'pyslate.db').resolve()}"

    @property
    def stripe_enabled(self) -> bool:
        return bool(self.stripe_secret_key)

    @property
    def secure_cookies(self) -> bool:
        return self.public_url.startswith("https://")


settings = Settings()
