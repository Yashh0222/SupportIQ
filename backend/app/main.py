"""SupportIQ FastAPI application entry point."""

from fastapi import Depends, FastAPI

from app.auth import require_admin, require_auth
from app.middleware import DynamicCorsMiddleware
from app.routes.chat import router as chat_router
from app.routes.companies import router as companies_router
from app.routes.origin_requests import router as origin_requests_router
from app.routes.origins import router as origins_router
from app.routes.upload import router as upload_router

app = FastAPI(title="SupportIQ", version="0.4.0")

app.add_middleware(DynamicCorsMiddleware)

# Public routes
app.include_router(chat_router)

# Authenticated user routes (no admin required)
app.include_router(companies_router)
app.include_router(origin_requests_router)

# Upload: auth checked per-route (owner or admin)
app.include_router(upload_router)

# Admin-only routes
app.include_router(origins_router, dependencies=[Depends(require_admin)])


@app.get("/")
def root() -> dict:
    return {"message": "SupportIQ backend is running", "status": "ok"}
