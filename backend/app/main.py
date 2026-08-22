"""SupportIQ FastAPI application entry point."""

from fastapi import FastAPI

from app.middleware import DynamicCorsMiddleware
from app.routes.chat import router as chat_router
from app.routes.companies import router as companies_router
from app.routes.origins import router as origins_router
from app.routes.upload import router as upload_router

app = FastAPI(title="SupportIQ", version="0.4.0")

app.add_middleware(DynamicCorsMiddleware)

app.include_router(chat_router)
app.include_router(upload_router)
app.include_router(companies_router)
app.include_router(origins_router)


@app.get("/")
def root() -> dict:
    return {"message": "SupportIQ backend is running", "status": "ok"}
