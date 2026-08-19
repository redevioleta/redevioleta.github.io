from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...db.database import get_db
from ...models.models import Denuncia
from ...schemas.schemas import DenunciaCreate, DenunciaOut

router = APIRouter(prefix="/denuncias", tags=["Denúncia"])

@router.post("/", response_model=DenunciaOut)
def criar_denuncia(dados: DenunciaCreate, db: Session = Depends(get_db)):
    denuncia = Denuncia(**dados.model_dump())
    db.add(denuncia)
    db.commit()
    db.refresh(denuncia)
    return denuncia

@router.get("/", response_model=List[DenunciaOut])
def listar_denuncias(db: Session = Depends(get_db)):
    return db.query(Denuncia).order_by(Denuncia.criado_em.desc()).all()

@router.get("/{denuncia_id}", response_model=DenunciaOut)
def obter_denuncia(denuncia_id: int, db: Session = Depends(get_db)):
    denuncia = db.query(Denuncia).filter(Denuncia.id == denuncia_id).first()
    if not denuncia:
        raise HTTPException(status_code=404, detail="Denúncia não encontrada")
    return denuncia
