from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float
from sqlalchemy.sql import func
from app.db.database import Base

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
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    endereco = Column(String, nullable=False)
    telefone = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    especializada = Column(Boolean, default=False)  # DEAM (delegacia da mulher)

class AlertaComunitario(Base):
    __tablename__ = "alertas_comunitarios"
    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, nullable=False)
    descricao = Column(Text, nullable=False)
    localizacao = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
