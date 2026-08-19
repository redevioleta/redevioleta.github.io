from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import EventoLinhaDoTempo
from app.schemas.schemas import EventoLinhaDoTempoOut

router = APIRouter(prefix="/linha-do-tempo", tags=["Linha do Tempo"])

@router.get("/", response_model=List[EventoLinhaDoTempoOut])
def listar_eventos(db: Session = Depends(get_db)):
    return db.query(EventoLinhaDoTempo).order_by(EventoLinhaDoTempo.data_evento).all()
