from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import IdentificacaoAssedio
from app.schemas.schemas import IdentificacaoAssedioCreate, IdentificacaoAssedioOut

router = APIRouter(prefix="/identificar-assedio", tags=["Identificar Assédio"])

def _classificar(descricao: str) -> str:
    termos_alerta = ["toque", "insistiu", "ameaça", "constrangimento", "forçou"]
    if any(termo in descricao.lower() for termo in termos_alerta):
        return "A situação descrita apresenta sinais de assédio. Considere buscar orientação."
    return "Não identificamos sinais claros, mas se você se sentiu desconfortável, isso já importa."

@router.post("/", response_model=IdentificacaoAssedioOut)
def identificar_assedio(dados: IdentificacaoAssedioCreate, db: Session = Depends(get_db)):
    resultado = _classificar(dados.descricao_situacao)
    registro = IdentificacaoAssedio(
        descricao_situacao=dados.descricao_situacao,
        resultado=resultado,
    )
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return registro
