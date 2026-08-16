"""Company registry endpoint: lists available company compartments and creates new ones."""

from fastapi import APIRouter, HTTPException

from app.companies import (
    CompanyInfo,
    company_raw_docs_dir,
    create_company,
    list_companies,
)
from app.models.schemas import CreateCompanyRequest

router = APIRouter(tags=["companies"])


@router.get("/companies")
def companies() -> list[dict]:
    result = []
    for company in list_companies():
        docs_dir = company_raw_docs_dir(company.id)
        doc_count = (
            len([p for p in docs_dir.rglob("*") if p.is_file()]) if docs_dir.exists() else 0
        )
        result.append(
            {
                "id": company.id,
                "display_name": company.display_name,
                "description": company.description,
                "doc_count": doc_count,
            }
        )
    return result


@router.post("/companies", status_code=201)
def create_company_route(req: CreateCompanyRequest) -> dict:
    try:
        info: CompanyInfo = create_company(req.id, req.display_name, req.description)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return {
        "id": info.id,
        "display_name": info.display_name,
        "description": info.description,
        "doc_count": 0,
    }
