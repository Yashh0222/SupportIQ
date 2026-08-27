"""Company registry: every company gets its own isolated document compartment.

Each company owns a raw-docs folder under ``data/companies/<id>/raw_docs/`` and
its own Chroma collection (see ``app.rag.vectorstore``). The chat assistant
only ever retrieves from the selected company's collection.

Built-in companies live in ``KNOWN_COMPANIES``. Companies registered through
``POST /companies`` are persisted to MongoDB (collection ``companies``) so they
survive restarts. If MongoDB is not configured, a legacy ``registry.json``
fallback is used so the app keeps working locally.
"""

import json
from dataclasses import dataclass
from pathlib import Path

from app.config import COMPANIES_DIR
from app.db import get_db

DEFAULT_COMPANY_ID = "acmecrm"

REGISTRY_FILE = COMPANIES_DIR / "registry.json"


@dataclass(frozen=True)
class CompanyInfo:
    id: str
    display_name: str
    description: str
    owner_id: str = ""


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


def _collection():
    db = get_db()
    return db["companies"] if db is not None else None


def _doc_to_info(doc: dict) -> CompanyInfo:
    return CompanyInfo(
        id=doc["id"],
        display_name=doc.get("display_name", doc["id"]),
        description=doc.get("description", ""),
        owner_id=doc.get("owner_id", ""),
    )


def _load_registry() -> dict[str, CompanyInfo]:
    """Load registered companies from MongoDB (or legacy registry.json)."""
    coll = _collection()
    if coll is not None:
        return {
            doc["id"]: _doc_to_info(doc)
            for doc in coll.find({})
        }
    return _load_registry_json()


def _load_registry_json() -> dict[str, CompanyInfo]:
    """Legacy fallback: load companies from ``registry.json``."""
    if not REGISTRY_FILE.exists():
        return {}
    try:
        raw = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return {
        cid: CompanyInfo(
            id=entry["id"],
            display_name=entry["display_name"],
            description=entry.get("description", ""),
            owner_id=entry.get("owner_id", ""),
        )
        for cid, entry in raw.items()
    }


def _save_registry(companies: dict[str, CompanyInfo]) -> None:
    """Persist the registered-company map to the active store."""
    coll = _collection()
    if coll is not None:
        for info in companies.values():
            coll.update_one(
                {"id": info.id},
                {
                    "$set": {
                        "id": info.id,
                        "display_name": info.display_name,
                        "description": info.description,
                        "owner_id": info.owner_id,
                    }
                },
                upsert=True,
            )
        # Remove entries that no longer exist
        ids = {c.id for c in companies.values()}
        coll.delete_many({"id": {"$nin": list(ids)}})
        return
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        cid: {
            "id": info.id,
            "display_name": info.display_name,
            "description": info.description,
            "owner_id": info.owner_id,
        }
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
    """Built-in companies followed by registered companies."""
    return [*KNOWN_COMPANIES.values(), *_load_registry().values()]


def list_companies_for_owner(owner_id: str) -> list[CompanyInfo]:
    """Return only companies owned by *owner_id*."""
    return [c for c in _load_registry().values() if c.owner_id == owner_id]


def is_company_owner(company_id: str, user_id: str) -> bool:
    """Check if *user_id* owns the company (built-in companies have no owner)."""
    info = _load_registry().get(company_id)
    if info is None:
        return False
    return info.owner_id == user_id


def create_company(
    company_id: str,
    display_name: str,
    description: str,
    owner_id: str = "",
) -> CompanyInfo:
    """Register a new company and create its raw-docs folder."""
    if not company_id.islower() or not company_id.replace("-", "").isalnum():
        raise ValueError("Company id must be lowercase letters, digits and hyphens only.")
    if company_id in KNOWN_COMPANIES:
        raise ValueError(f"Company '{company_id}' already exists.")
    registry = _load_registry()
    if company_id in registry:
        raise ValueError(f"Company '{company_id}' already exists.")

    info = CompanyInfo(
        id=company_id,
        display_name=display_name,
        description=description,
        owner_id=owner_id,
    )
    registry[company_id] = info
    _save_registry(registry)
    company_raw_docs_dir(company_id).mkdir(parents=True, exist_ok=True)
    return info


def company_raw_docs_dir(company_id: str) -> Path:
    """Directory holding raw documents for a specific company."""
    return COMPANIES_DIR / get_company(company_id).id / "raw_docs"


def delete_company(company_id: str) -> bool:
    """Remove a company from the registry. Built-in companies cannot be deleted."""
    if company_id in KNOWN_COMPANIES:
        return False
    registry = _load_registry()
    if company_id not in registry:
        return False
    del registry[company_id]
    _save_registry(registry)
    return True
