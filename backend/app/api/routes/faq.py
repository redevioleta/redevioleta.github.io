from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import FaqItem
from app.schemas.schemas import FaqItemOut

router = APIRouter(prefix="/faq", tags=["FAQ"])

@router.get("/", response_model=List[FaqItemOut])
def listar_faq(db: Session = Depends(get_db)):
    return db.query(FaqItem).order_by(FaqItem.ordem).all()
