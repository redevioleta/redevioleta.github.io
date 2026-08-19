from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...models.models import AlertaComunitario
from ...schemas.schemas import AlertaComunitarioCreate, AlertaComunitarioOut

router = APIRouter(prefix="/alertas", tags=["Alertas Comunitários"])

@router.post("/", response_model=AlertaComunitarioOut)
def criar_alerta(dados: AlertaComunitarioCreate, db: Session = Depends(get_db)) -> AlertaComunitarioOut:
    alerta = AlertaComunitario(**dados.model_dump())
    db.add(alerta)
    db.commit()
    db.refresh(alerta)
    return alerta  

@router.get("/", response_model=List[AlertaComunitarioOut])
def listar_alertas(db: Session = Depends(get_db)) -> List[AlertaComunitarioOut]:
    alertas = db.query(AlertaComunitario).order_by(AlertaComunitario.criado_em.desc()).all()
    return [AlertaComunitarioOut.model_validate(alerta) for alerta in alertas]
