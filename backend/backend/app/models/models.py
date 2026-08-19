import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column

Base = declarative_base()

class AlertaComunitario(Base):
    __tablename__ = "alertas_comunitarios"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    titulo: Mapped[str] = mapped_column(String, nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    localizacao: Mapped[str | None] = mapped_column(String, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    criado_em: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

class Desabafo(Base):
    __tablename__ = "desabafos"

    id = Column(Integer, primary_key=True, index=True)
    texto = Column(Text, nullable=False)
    anonimo = Column(Boolean, default=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())

class IdentificacaoAssedio(Base):
    __tablename__ = "identificacoes_assedio"
    id = Column(Integer, primary_key=True, index=True)
    descricao_situacao = Column(Text, nullable=False)
    resultado = Column(String, nullable=True)  # ex: "configura assédio" / "atenção" / etc
    criado_em = Column(DateTime(timezone=True), server_default=func.now())

class Denuncia(Base):
    __tablename__ = "denuncias"
    id = Column(Integer, primary_key=True, index=True)
    descricao = Column(Text, nullable=False)
    local = Column(String, nullable=True)
    anonimo = Column(Boolean, default=True)
    contato = Column(String, nullable=True)
    status = Column(String, default="recebida")  # recebida, em_analise, encaminhada
    criado_em = Column(DateTime(timezone=True), server_default=func.now())

class Quiz(Base):
    __tablename__ = "quiz_perguntas"
    id = Column(Integer, primary_key=True, index=True)
    pergunta = Column(Text, nullable=False)
    opcoes = Column(Text, nullable=False)  # JSON serializado com as opções
    peso = Column(Integer, default=1)

class Recurso(Base):
    __tablename__ = "recursos"
    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, nullable=False)
    descricao = Column(Text, nullable=True)
    link = Column(String, nullable=True)
    categoria = Column(String, nullable=True)  # ex: jurídico, psicológico, saúde

class FaqItem(Base):
    __tablename__ = "faq_itens"
    id = Column(Integer, primary_key=True, index=True)
    pergunta = Column(String, nullable=False)
    resposta = Column(Text, nullable=False)
    ordem = Column(Integer, default=0)

class EventoLinhaDoTempo(Base):
    __tablename__ = "linha_do_tempo"
    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, nullable=False)
    descricao = Column(Text, nullable=True)
    data_evento = Column(DateTime, nullable=False)

class Delegacia(Base):
    __tablename__ = "delegacias"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String, nullable=False)
    endereco: Mapped[str] = mapped_column(String, nullable=False)
    telefone: Mapped[str | None] = mapped_column(String, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    especializada: Mapped[bool] = mapped_column(Boolean, default=False)  # DEAM (delegacia da mulher)
