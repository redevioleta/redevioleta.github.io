from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ...db.database import get_db
from ...models.models import Recurso
from ...schemas.schemas import RecursoOut

router = APIRouter(prefix="/recursos", tags=["Recursos"])
@router.get("/", response_model=List[RecursoOut])
def listar_recursos(categoria: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Recurso)
    if categoria:
        query = query.filter(Recurso.categoria == categoria)
    return query.all()
