from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import AlertaComunitario
from app.schemas.schemas import AlertaComunitarioCreate, AlertaComunitarioOut
from app.core.violeta_ia import analisar_alerta_ia

router = APIRouter(prefix="/alertas", tags=["Alertas Comunitários"])

@router.post("/", response_model=AlertaComunitarioOut)
async def criar_alerta(dados: AlertaComunitarioCreate, db: Session = Depends(get_db)):
    alerta = AlertaComunitario(**dados.model_dump())

    # A Violeta IA modera o alerta assim que ele é criado: classifica a
    # urgência de forma automática e gera um resumo curto. Se a IA não
    # estiver disponível ou a análise falhar, o alerta é salvo normalmente
    # com a urgência escolhida pela pessoa que avisou, sem bloquear o envio.
    analise = await analisar_alerta_ia(dados.titulo, dados.descricao)
    if analise:
        alerta.urgencia = analise["urgencia"]  # type: ignore[assignment]
        alerta.resumo_ia = analise["resumo"]  # type: ignore[assignment]
        alerta.moderado_ia = True  # type: ignore[assignment]

    db.add(alerta)
    db.commit()
    db.refresh(alerta)
    return alerta

@router.get("/", response_model=List[AlertaComunitarioOut])
def listar_alertas(db: Session = Depends(get_db)):
    return db.query(AlertaComunitario).order_by(AlertaComunitario.criado_em.desc()).all()

@router.patch("/{alerta_id}/confirmar", response_model=AlertaComunitarioOut)
def confirmar_alerta(alerta_id: int, db: Session = Depends(get_db)):
    alerta = db.query(AlertaComunitario).filter(AlertaComunitario.id == alerta_id).first()
    if not alerta:
        raise HTTPException(status_code=404, detail="Alerta não encontrado")
    alerta.confirmacoes = (alerta.confirmacoes or 0) + 1  # type: ignore[assignment]
    db.commit()
    db.refresh(alerta)
    return alerta

@router.delete("/{alerta_id}", status_code=204)
def remover_alerta(alerta_id: int, db: Session = Depends(get_db)):
    alerta = db.query(AlertaComunitario).filter(AlertaComunitario.id == alerta_id).first()
    if not alerta:
        raise HTTPException(status_code=404, detail="Alerta não encontrado")
    db.delete(alerta)
    db.commit()
    return None
