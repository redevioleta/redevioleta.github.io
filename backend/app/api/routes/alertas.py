from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import AlertaComunitario
from app.schemas.schemas import AlertaComunitarioCreate, AlertaComunitarioOut

router = APIRouter(prefix="/alertas", tags=["Alertas Comunitários"])

@router.post("/", response_model=AlertaComunitarioOut)
def criar_alerta(dados: AlertaComunitarioCreate, db: Session = Depends(get_db)):
    alerta = AlertaComunitario(**dados.model_dump())
    db.add(alerta)
    db.commit()
    db.refresh(alerta)
    return alerta
    
@router.get("/", response_model=List[AlertaComunitarioOut])
def listar_alertas(db: Session = Depends(get_db)):
    return db.query(AlertaComunitario).order_by(AlertaComunitario.criado_em.desc()).all()
