from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import Desabafo
from app.schemas.schemas import DesabafoCreate, DesabafoOut

router = APIRouter(prefix="/desabafos", tags=["Desabafo"])

@router.post("/", response_model=DesabafoOut)
def criar_desabafo(dados: DesabafoCreate, db: Session = Depends(get_db)):
    desabafo = Desabafo(**dados.model_dump())
    db.add(desabafo)
    db.commit()
    db.refresh(desabafo)
    return desabafo

@router.get("/", response_model=List[DesabafoOut])
def listar_desabafos(db: Session = Depends(get_db)):
    return db.query(Desabafo).order_by(Desabafo.criado_em.desc()).all()
