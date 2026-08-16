"""SupportIQ FastAPI application entry point."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.chat import router as chat_router
from app.routes.companies import router as companies_router
from app.routes.upload import router as upload_router

app = FastAPI(title="SupportIQ", version="0.3.0")

_allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "https://support-iq-yk.vercel.app,http://localhost:5173,http://localhost:3000",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(upload_router)
app.include_router(companies_router)


@app.get("/")
def root() -> dict:
    return {"message": "SupportIQ backend is running", "status": "ok"}
