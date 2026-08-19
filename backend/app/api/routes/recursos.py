from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import Recurso
from app.schemas.schemas import RecursoOut

router = APIRouter(prefix="/recursos", tags=["Recursos"])

@router.get("/", response_model=List[RecursoOut])
def listar_recursos(categoria: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Recurso)
    if categoria:
        query = query.filter(Recurso.categoria == categoria)
    return query.all()
