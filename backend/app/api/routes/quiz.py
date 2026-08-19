from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import Quiz
from app.schemas.schemas import QuizPerguntaOut, QuizRespostaIn, QuizResultadoOut

router = APIRouter(prefix="/quiz", tags=["Quiz de Autoavaliação"])

@router.get("/perguntas", response_model=List[QuizPerguntaOut])
def listar_perguntas(db: Session = Depends(get_db)):
    return db.query(Quiz).all()

@router.post("/resultado", response_model=QuizResultadoOut)
def calcular_resultado(dados: QuizRespostaIn):
    pontuacao = sum(dados.respostas)
    if pontuacao <= 3:
        mensagem = "Baixo indício de situações de risco identificadas."
    elif pontuacao <= 7:
        mensagem = "Alguns sinais de atenção. Vale conhecer os recursos disponíveis."
    else:
        mensagem = "Vários sinais de alerta. Recomendamos buscar apoio e orientação."
    return QuizResultadoOut(pontuacao=pontuacao, mensagem=mensagem)
