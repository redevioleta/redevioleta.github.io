"""
Serviço da "Violeta IA" — assistente de apoio e informação do projeto
Rede Violeta.

Princípios de design (definidos pelo escopo do projeto):
  1. A Violeta IA NUNCA se apresenta como psicóloga, advogada, policial
     ou serviço de emergência.
  2. Em sinais de perigo imediato, a resposta de segurança é SEMPRE
     gerada localmente (sem depender da IA externa), garantindo que a
     orientação correta apareça mesmo se o provedor de IA falhar, demorar
     ou responder algo inadequado.
  3. Nenhuma mensagem é persistida em banco de dados — o histórico só
     existe em memória durante a própria requisição, a critério do
     frontend (ver `historico` no schema), nunca gravado no servidor.
  4. Se nenhuma chave de API estiver configurada (ou a chamada falhar),
     o serviço cai para um conjunto de respostas locais por
     palavra-chave, para que o site continue funcional sem depender de
     um provedor externo.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings
from app.schemas.schemas import ChatMensagem

SYSTEM_PROMPT = (
    "Você é a Violeta IA, assistente virtual do projeto acadêmico 'Rede "
    "Violeta', voltado ao acolhimento e à informação sobre violência "
    "contra a mulher (campanha Agosto Lilás).\n\n"
    "Regras obrigatórias:\n"
    "- Você OFERECE informação e acolhimento. Você NÃO é psicóloga, "
    "advogada, policial, nem um serviço de emergência, e deve deixar "
    "isso claro sempre que fizer sentido.\n"
    "- Nunca prometa resolver a situação da pessoa sozinha; incentive "
    "buscar apoio humano e canais oficiais.\n"
    "- Pode: explicar tipos de violência (física, psicológica, sexual, "
    "patrimonial, moral); informar sobre direitos (ex.: Lei Maria da "
    "Penha, medidas protetivas); ajudar a pessoa a organizar o que "
    "deseja contar a alguém de confiança; indicar canais oficiais "
    "(Ligue 180, Disque 100, Polícia 190, DEAM, Defensoria Pública).\n"
    "- Se perceber qualquer sinal de risco iminente, reforce IMEDIATAMENTE "
    "a importância de buscar um local seguro e ligar 190, antes de "
    "qualquer outra orientação.\n"
    "- Nunca minimize, julgue ou duvide do relato da pessoa.\n"
    "- Responda no idioma solicitado pela pessoa, em tom acolhedor, claro "
    "e objetivo (no máximo 4-5 frases por resposta)."
)

AVISO_SEGURANCA = (
    "⚠️ Se você está em perigo imediato, priorize sua segurança agora: "
    "se puder, vá para um local seguro e ligue 190 (Polícia Militar). "
    "O Ligue 180 (Central de Atendimento à Mulher) também orienta sobre "
    "a rede de proteção, gratuitamente e 24h. Eu sou uma assistente "
    "informativa — não substituo uma emergência real, mas posso ajudar "
    "você a entender os próximos passos quando estiver segura."
)

_TERMOS_PERIGO = (
    "perigo", "socorro", "me ajuda agora", "ele ta aqui", "ele está aqui",
    "ela ta aqui", "ela está aqui", "vou morrer", "ameaça de morte",
    "ameacando", "ameaçando", "arma", "agredindo", "me machucou",
    "me machucando", "nao consigo sair", "não consigo sair", "trancad",
    "danger", "help me now", "he is here", "she is here", "i am being hurt",
    "i can't leave", "immediate danger", "peligro", "auxilio", "ayuda ahora",
    "no puedo salir", "me está golpeando", "me esta golpeando",
)

_RESPOSTA_PADRAO = (
    "Posso ajudar com informações sobre os recursos da Rede Violeta, "
    "canais de apoio, tipos de violência ou formas de buscar ajuda. "
    "Sou a Violeta! 💜"
)

_REGRAS = (
    (("180", "denúncia", "denuncia", "orienta"),
     "O Ligue 180 é a Central de Atendimento à Mulher. O serviço é "
     "gratuito e funciona 24 horas. Ele oferece orientação sobre "
     "direitos e serviços da rede de atendimento."),
    (("delegacia", "deam"),
     "A DEAM é a Delegacia Especializada de Atendimento à Mulher. Ela "
     "integra a rede de atendimento especializado. Use a aba Recursos "
     "para encontrar mais informações."),
    (("violênci", "violenc"),
     "Violência contra a mulher pode assumir diferentes formas: física, "
     "psicológica, sexual, patrimonial e moral. Se você estiver vivendo "
     "isso, procure uma pessoa de confiança ou um serviço especializado."),
    (("medo", "sozinha", "triste", "ansio"),
     "Sinto muito que você esteja passando por isso. Você merece ser "
     "ouvida e respeitada. Se for seguro, converse com alguém de "
     "confiança. Em uma emergência, ligue 190."),
    (("lei", "maria da penha", "direito"),
     "O Brasil possui legislação específica de proteção às mulheres, "
     "incluindo a Lei Maria da Penha. Para orientação jurídica, procure "
     "a Defensoria Pública ou serviço jurídico especializado."),
    (("site", "rede violeta", "projeto"),
     "A Rede Violeta é um projeto acadêmico da Faculdade Cruzeiro do "
     "Sul. O objetivo é reunir informação, conscientização e caminhos "
     "de apoio relacionados à violência contra a mulher."),
)


def contem_sinal_de_perigo(texto: str) -> bool:
    t = texto.lower()
    return any(termo in t for termo in _TERMOS_PERIGO)


def aviso_seguranca_idioma(idioma: str) -> str:
    if idioma == "en":
        return (
            "⚠️ If you are in immediate danger, prioritize your safety now: "
            "if possible, move to a safe place and call 190 (Military Police). "
            "The 180 hotline also provides free, 24-hour guidance about support "
            "services. I provide information and support, but I am not an emergency service."
        )
    if idioma == "es":
        return (
            "⚠️ Si estás en peligro inmediato, prioriza tu seguridad: si puedes, "
            "ve a un lugar seguro y llama al 190 (Policía Militar). La línea 180 "
            "también ofrece orientación gratuita las 24 horas sobre servicios de "
            "apoyo. Soy una asistente informativa, no un servicio de emergencia."
        )
    return AVISO_SEGURANCA


def resposta_local(texto: str, idioma: str = "pt") -> str:
    """Respostas locais, baseadas em palavras-chave — usadas quando a IA
    generativa não está configurada ou falha."""
    t = texto.lower()
    if idioma == "en":
        if any(term in t for term in ("180", "report", "complaint", "guidance")):
            return "The 180 hotline is Brazil’s Women’s Support Center. It is free and operates 24 hours a day, providing guidance on rights and support services."
        if any(term in t for term in ("police station", "deam")):
            return "A DEAM is a specialized police station for women. Open the Resources tab to find more information about specialized support services."
        if any(term in t for term in ("violence", "abuse", "harassment")):
            return "Violence against women can be physical, psychological, sexual, financial, or moral. If this is happening to you, contact someone you trust or a specialized support service."
        if any(term in t for term in ("afraid", "fear", "alone", "sad", "anxious")):
            return "I am sorry you are going through this. You deserve to be heard and respected. If it is safe, talk to someone you trust. In an emergency, call 190."
        if any(term in t for term in ("law", "maria da penha", "right")):
            return "Brazil has specific legislation to protect women, including the Maria da Penha Law. For legal guidance, contact the Public Defender’s Office or a specialized legal service."
        return "I can help with information about Rede Violeta resources, emergency contacts, types of violence, or ways to seek support. I am Violeta! 💜"
    if idioma == "es":
        if any(term in t for term in ("180", "denuncia", "orienta")):
            return "La línea 180 es el Centro de Atención a las Mujeres de Brasil. Es gratuita y funciona las 24 horas. Ofrece orientación sobre derechos y servicios de apoyo."
        if any(term in t for term in ("comisaría", "policia", "deam")):
            return "La DEAM es una comisaría especializada en la atención a las mujeres. Consulta la pestaña Recursos para obtener más información sobre los servicios especializados."
        if any(term in t for term in ("violencia", "acoso", "abuso")):
            return "La violencia contra las mujeres puede ser física, psicológica, sexual, patrimonial o moral. Si estás viviendo esta situación, busca a alguien de confianza o un servicio especializado."
        if any(term in t for term in ("miedo", "sola", "triste", "ansio")):
            return "Siento mucho que estés pasando por esto. Mereces que te escuchen y te respeten. Si es seguro, habla con alguien de confianza. En una emergencia, llama al 190."
        if any(term in t for term in ("ley", "maria da penha", "derecho")):
            return "Brasil cuenta con legislación específica para proteger a las mujeres, incluida la Ley Maria da Penha. Para recibir orientación jurídica, contacta con la Defensoría Pública o un servicio especializado."
        return "Puedo ayudarte con información sobre los recursos de Rede Violeta, teléfonos de emergencia, tipos de violencia o formas de buscar apoyo. ¡Soy Violeta! 💜"
    for termos, resposta in _REGRAS:
        if any(termo in t for termo in termos):
            return resposta
    return _RESPOSTA_PADRAO


async def gerar_resposta_ia(mensagem: str, historico: list[ChatMensagem], idioma: str = "pt") -> str | None:
    """Chama um provedor de IA compatível com a API da OpenAI.
    Retorna None se a IA não estiver configurada ou a chamada falhar,
    para que o chamador use o fallback local."""
    if not settings.ai_enabled:
        return None

    instrucoes_idioma = {
        "pt": "Responda em português do Brasil.",
        "en": "Respond in English.",
        "es": "Responde en español.",
    }
    mensagens: list[dict[str, str]] = [{
        "role": "system",
        "content": SYSTEM_PROMPT + "\n\n" + instrucoes_idioma.get(idioma, instrucoes_idioma["pt"]),
    }]
    for item in historico[-8:]:
        mensagens.append({"role": item.role, "content": item.content})
    mensagens.append({"role": "user", "content": mensagem})

    payload: dict[str, Any] = {
        "model": settings.openai_model,
        "messages": mensagens,
        "temperature": 0.6,
        "max_tokens": 300,
    }
    headers: dict[str, str] = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=settings.openai_timeout_seconds) as client:
            resp = await client.post(
                f"{settings.openai_base_url}/chat/completions",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception:
        # Qualquer falha (sem internet, chave inválida, timeout, quota
        # excedida, etc.) cai silenciosamente para o fallback local —
        # a Violeta continua respondendo, só que com regras.
        return None


async def responder(mensagem: str, historico: list[ChatMensagem], idioma: str = "pt") -> tuple[str, str, bool]:
    """Retorna (resposta, fonte, alerta_seguranca).
    `fonte` é "seguranca", "ia" ou "regras"."""
    if contem_sinal_de_perigo(mensagem):
        return aviso_seguranca_idioma(idioma), "seguranca", True

    resposta_gerada = await gerar_resposta_ia(mensagem, historico, idioma)
    if resposta_gerada:
        return resposta_gerada, "ia", False

    return resposta_local(mensagem, idioma), "regras", False
