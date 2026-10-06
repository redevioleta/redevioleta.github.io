from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from app.core.config import settings
from app.db.database import Base, engine
from app.api.api import api_router

Base.metadata.create_all(bind=engine)

# Migração leve e idempotente: create_all não altera tabelas existentes.
# Adicionamos colunas introduzidas por versões novas do modelo, preservando
# os registros já armazenados.
with engine.connect() as _conn:
    for _coluna_sql in (
        "ALTER TABLE alertas_comunitarios ADD COLUMN urgencia VARCHAR DEFAULT 'media'",
        "ALTER TABLE alertas_comunitarios ADD COLUMN confirmacoes INTEGER DEFAULT 0",
        "ALTER TABLE alertas_comunitarios ADD COLUMN resumo_ia TEXT",
        "ALTER TABLE alertas_comunitarios ADD COLUMN moderado_ia BOOLEAN DEFAULT 0",
    ):
        try:
            _conn.execute(text(_coluna_sql))
            _conn.commit()
        except Exception:
            _conn.rollback()

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
