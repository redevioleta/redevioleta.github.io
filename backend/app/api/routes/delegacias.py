from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import Delegacia
from app.schemas.schemas import DelegaciaOut

router = APIRouter(prefix="/delegacias", tags=["Mapa de Delegacias"])

@router.get("/", response_model=List[DelegaciaOut])
def listar_delegacias(apenas_especializadas: Optional[bool] = None, db: Session = Depends(get_db)):
    query = db.query(Delegacia)
    if apenas_especializadas:
        query = query.filter(Delegacia.especializada == True)  # noqa: E712
    return query.all()
