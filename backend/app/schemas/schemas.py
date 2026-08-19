from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class DesabafoCreate(BaseModel):
    texto: str
    anonimo: bool = True


class DesabafoOut(DesabafoCreate):
    id: int
    criado_em: datetime

    class Config:
        from_attributes = True

class IdentificacaoAssedioCreate(BaseModel):
    descricao_situacao: str


class IdentificacaoAssedioOut(IdentificacaoAssedioCreate):
    id: int
    resultado: Optional[str] = None
    criado_em: datetime

    class Config:
        from_attributes = True

class DenunciaCreate(BaseModel):
    descricao: str
    local: Optional[str] = None
    anonimo: bool = True
    contato: Optional[str] = None

class DenunciaOut(DenunciaCreate):
    id: int
    status: str
    criado_em: datetime

    class Config:
        from_attributes = True

class QuizPerguntaOut(BaseModel):
    id: int
    pergunta: str
    opcoes: str
    peso: int

    class Config:
        from_attributes = True

class QuizRespostaIn(BaseModel):
    respostas: List[int] 

class QuizResultadoOut(BaseModel):
    pontuacao: int
    mensagem: str

class RecursoOut(BaseModel):
    id: int
    titulo: str
    descricao: Optional[str] = None
    link: Optional[str] = None
    categoria: Optional[str] = None

    class Config:
        from_attributes = True

class FaqItemOut(BaseModel):
    id: int
    pergunta: str
    resposta: str
    ordem: int

    class Config:
        from_attributes = True

class EventoLinhaDoTempoOut(BaseModel):
    id: int
    titulo: str
    descricao: Optional[str] = None
    data_evento: datetime

    class Config:
        from_attributes = True

class DelegaciaOut(BaseModel):
    id: int
    nome: str
    endereco: str
    telefone: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    especializada: bool

    class Config:
        from_attributes = True

class AlertaComunitarioCreate(BaseModel):
    titulo: str
    descricao: str
    localizacao: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class AlertaComunitarioOut(AlertaComunitarioCreate):
    id: int
    criado_em: datetime

    class Config:
        from_attributes = True
