"""Company registry: every company gets its own isolated document compartment.

Each company owns a raw-docs folder under ``data/companies/<id>/raw_docs/`` and
its own Chroma collection (see ``app.rag.vectorstore``). The chat assistant
only ever retrieves from the selected company's collection.

Built-in companies live in ``KNOWN_COMPANIES``. Companies registered by an
admin through ``POST /companies`` are persisted to ``registry.json`` so they
survive restarts.
"""

import json
from dataclasses import dataclass
from pathlib import Path

from app.config import COMPANIES_DIR

DEFAULT_COMPANY_ID = "acmecrm"

REGISTRY_FILE = COMPANIES_DIR / "registry.json"


@dataclass(frozen=True)
class CompanyInfo:
    id: str
    display_name: str
    description: str


KNOWN_COMPANIES: dict[str, CompanyInfo] = {
    "acmecrm": CompanyInfo(
        id="acmecrm",
        display_name="AcmeCRM",
        description="a cloud-based CRM platform for small and mid-sized teams",
    ),
    "globex": CompanyInfo(
        id="globex",
        display_name="Globex",
        description="an e-commerce and marketplace platform for online retailers",
    ),
}


def _load_registry() -> dict[str, CompanyInfo]:
    """Load admin-registered companies from ``registry.json``."""
    if not REGISTRY_FILE.exists():
        return {}
    try:
        raw = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return {
        cid: CompanyInfo(id=entry["id"], display_name=entry["display_name"], description=entry.get("description", ""))
        for cid, entry in raw.items()
    }


def _save_registry(companies: dict[str, CompanyInfo]) -> None:
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        cid: {"id": info.id, "display_name": info.display_name, "description": info.description}
        for cid, info in companies.items()
    }
    REGISTRY_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def get_company(company_id: str) -> CompanyInfo:
    """Return registry info for *company_id*, falling back to a generic entry."""
    known = KNOWN_COMPANIES.get(company_id)
    if known is not None:
        return known
    registered = _load_registry().get(company_id)
    if registered is not None:
        return registered
    return CompanyInfo(
        id=company_id,
        display_name=company_id.replace("-", " ").title(),
        description="a customer support company",
    )


def list_companies() -> list[CompanyInfo]:
    """Built-in companies followed by admin-registered companies."""
    return [*KNOWN_COMPANIES.values(), *_load_registry().values()]


def create_company(company_id: str, display_name: str, description: str) -> CompanyInfo:
    """Register a new company and create its raw-docs folder."""
    if not company_id.islower() or not company_id.replace("-", "").isalnum():
        raise ValueError("Company id must be lowercase letters, digits and hyphens only.")
    if company_id in KNOWN_COMPANIES:
        raise ValueError(f"Company '{company_id}' already exists.")
    registry = _load_registry()
    if company_id in registry:
        raise ValueError(f"Company '{company_id}' already exists.")

    info = CompanyInfo(id=company_id, display_name=display_name, description=description)
    registry[company_id] = info
    _save_registry(registry)
    company_raw_docs_dir(company_id).mkdir(parents=True, exist_ok=True)
    return info


def company_raw_docs_dir(company_id: str) -> Path:
    """Directory holding raw documents for a specific company."""
    return COMPANIES_DIR / get_company(company_id).id / "raw_docs"
