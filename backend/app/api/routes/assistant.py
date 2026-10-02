import asyncio
import json
from typing import Literal
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

from app.core.config import settings

router = APIRouter(prefix="/assistant", tags=["Assistente"])

SYSTEM_INSTRUCTION = (
    "Você é Violeta, guia acolhedora e informativa do site Rede Violeta, "
    "um projeto educativo brasileiro sobre violência contra a mulher. "
    "Responda em português brasileiro, com empatia e clareza. Ajude a pessoa "
    "a encontrar as seções Desabafo, Conheça os Casos, Meu Caso, Recursos & Apoio, "
    "FAQ e Alertas. Não faça diagnósticos nem substitua orientação profissional "
    "médica, psicológica ou jurídica. Não culpabilize a vítima, não invente "
    "serviços ou fatos e indique fontes oficiais quando não souber. Nunca peça "
    "nome, endereço, telefone ou outros dados identificáveis. Em risco imediato, "
    "oriente a pessoa a buscar um local seguro e ligar 190; o Ligue 180 oferece "
    "orientação sobre direitos e serviços de atendimento. Não diga que uma "
    "denúncia foi registrada ou que você acionou serviços."
)


class AssistantMessage(BaseModel):
    role: Literal["user", "model"]
    text: str = Field(min_length=1, max_length=2000)


class AssistantChatRequest(BaseModel):
    messages: list[AssistantMessage] = Field(min_length=1, max_length=12)

    @model_validator(mode="after")
    def validate_turn_order(self):
        roles = [message.role for message in self.messages]
        if roles[0] != "user" or roles[-1] != "user":
            raise ValueError("A conversa deve começar e terminar com uma mensagem do usuário.")
        if any(previous == current for previous, current in zip(roles, roles[1:])):
            raise ValueError("As mensagens devem alternar entre usuário e assistente.")
        return self


class AssistantChatResponse(BaseModel):
    reply: str


def _generate_reply(messages: list[AssistantMessage]) -> str:
    model = quote(settings.gemini_model, safe="-._")
    request = Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        data=json.dumps({
            "system_instruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
            "contents": [
                {"role": message.role, "parts": [{"text": message.text}]}
                for message in messages
            ],
            "generationConfig": {"maxOutputTokens": 500, "temperature": 0.5},
        }).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": settings.gemini_api_key or "",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=20) as response:
            result = json.loads(response.read())
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=502,
            detail="A Violeta não conseguiu obter uma resposta agora. Tente novamente.",
        ) from exc

    candidates = result.get("candidates", [])
    parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
    reply = "\n".join(part.get("text", "") for part in parts).strip()
    if not reply:
        raise HTTPException(
            status_code=502,
            detail="A Violeta não conseguiu obter uma resposta agora. Tente novamente.",
        )
    return reply


@router.post("/chat", response_model=AssistantChatResponse)
async def chat(dados: AssistantChatRequest):
    if not settings.gemini_api_key:
        raise HTTPException(
            status_code=503,
            detail="Gemini ainda não está configurado. Adicione GEMINI_API_KEY nas variáveis de ambiente do backend.",
        )
    reply = await asyncio.to_thread(_generate_reply, dados.messages)
    return AssistantChatResponse(reply=reply)
