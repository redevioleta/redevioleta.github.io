from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.db.database import Base, engine
from app.api.api import api_router

Base.metadata.create_all(bind=engine)
app = FastAPI(title=settings.app_name)

FRONTEND_DIR = Path(__file__).resolve().parents[2]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix=settings.api_v1_prefix)

@app.get("/health", include_in_schema=False)
def healthcheck():
    return {"status": "ok", "projeto": "Fala Segura API"}

app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
