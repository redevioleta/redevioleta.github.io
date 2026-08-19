from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

api_router = None

try:
    from .db.database import Base, engine
    from .api.api import api_router

    Base.metadata.create_all(bind=engine)
except (ImportError, ModuleNotFoundError):
    pass

app = FastAPI(title="Rede Violeta API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if api_router is not None:
    app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def raiz():
    return {"status": "ok", "projeto": "Fala Segura API"}
