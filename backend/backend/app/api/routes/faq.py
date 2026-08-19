from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ...db.database import get_db
from ...models.models import FaqItem
from ...schemas.schemas import FaqItemOut

router = APIRouter(prefix="/faq", tags=["FAQ"])
@router.get("/", response_model=List[FaqItemOut])
def listar_faq(db: Session = Depends(get_db)):
    return db.query(FaqItem).order_by(FaqItem.ordem).all()
