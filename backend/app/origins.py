"""Dynamic allowed-origin registry for cross-site access control.

Replaces the static ``ALLOWED_ORIGINS`` env list: admins manage which site
origins may call the API from the admin panel. Origins are persisted to
``data/companies/allowed_origins.json`` so they survive restarts. On first
run the registry is seeded from the ``ALLOWED_ORIGINS`` env var so existing
deployments keep working after the upgrade.
"""

import json
import os
import re

from app.config import COMPANIES_DIR

ORIGINS_FILE = COMPANIES_DIR / "allowed_origins.json"

_ORIGIN_PATTERN = re.compile(r"^https?://[a-z0-9-]+(\.[a-z0-9-]+)*(:\d+)?$")

_DEFAULT_ORIGINS_ENV = (
    "https://support-iq-yk.vercel.app,"
    "https://wanderlust-project-18.onrender.com,"
    "http://localhost:5173,http://localhost:3000"
)


def normalize_origin(origin: str) -> str:
    return origin.strip().rstrip("/").lower()


def _validate(origin: str) -> str:
    if not _ORIGIN_PATTERN.match(origin):
        raise ValueError(f"Invalid origin '{origin}'. Use scheme://host[:port], e.g. https://mysite.com")
    return origin


def _save(origins: list[str]) -> None:
    ORIGINS_FILE.parent.mkdir(parents=True, exist_ok=True)
    ORIGINS_FILE.write_text(json.dumps(sorted(origins), indent=2), encoding="utf-8")


def _load() -> list[str]:
    if ORIGINS_FILE.exists():
        try:
            return json.loads(ORIGINS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    seed = [
        _validate(normalize_origin(o))
        for o in os.getenv("ALLOWED_ORIGINS", _DEFAULT_ORIGINS_ENV).split(",")
        if o.strip()
    ]
    _save(seed)
    return seed


def list_origins() -> list[str]:
    return sorted(set(_load()))


def add_origin(origin: str) -> list[str]:
    cleaned = _validate(normalize_origin(origin))
    origins = set(_load())
    origins.add(cleaned)
    result = sorted(origins)
    _save(result)
    return result


def remove_origin(origin: str) -> list[str]:
    cleaned = normalize_origin(origin)
    origins = [o for o in _load() if o != cleaned]
    _save(origins)
    return origins


def is_allowed(origin: str | None) -> bool:
    if not origin:
        return False
    cleaned = normalize_origin(origin)
    if not _ORIGIN_PATTERN.match(cleaned):
        return False
    return cleaned in set(_load())
