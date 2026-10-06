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

import json
import re
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
    "- Se perceber qualquer sinal de risco iminente, reforce IMEDIATAMENTE "
    "a importância de buscar um local seguro e ligar 190, antes de "
    "qualquer outra orientação.\n"
    "- Nunca minimize, julgue ou duvide do relato da pessoa.\n"
    "- Responda no idioma solicitado pela pessoa, em tom acolhedor, claro "
    "e objetivo (no máximo 4-5 frases por resposta).\n"
    "- Responda sempre em texto corrido simples, SEM formatação markdown "
    "(sem **negrito**, sem *itálico*, sem títulos com #, sem listas com "
    "asteriscos ou hífens). Se precisar listar itens, separe por vírgulas "
    "ou numere como '1)', '2)', '3)' dentro do próprio texto.\n\n"
    "Tópicos que você deve saber explicar quando perguntada:\n\n"
    "1) TIPOS DE VIOLÊNCIA (Lei Maria da Penha, art. 7º):\n"
    "   - Física: qualquer conduta que ofenda a integridade/saúde "
    "corporal (empurrões, tapas, socos, espancamento).\n"
    "   - Psicológica: humilhação, ameaça, manipulação, isolamento de "
    "amigos/família, controle excessivo, chantagem emocional.\n"
    "   - Sexual: forçar/constranger a presenciar, manter ou participar "
    "de relação sexual não desejada, impedir uso de método "
    "contraceptivo, forçar casamento ou prostituição.\n"
    "   - Patrimonial: destruir, reter ou subtrair bens, documentos, "
    "valores ou instrumentos de trabalho da mulher.\n"
    "   - Moral: calúnia, difamação ou injúria (ex.: espalhar mentiras "
    "ou xingamentos ofensivos sobre a mulher).\n\n"
    "2) PASSO A PASSO PARA DENUNCIAR:\n"
    "   a. Se houver perigo imediato, ligar 190 (Polícia Militar) "
    "primeiro.\n"
    "   b. Ligar 180 (Central de Atendimento à Mulher, gratuito e 24h) "
    "para orientação e encaminhamento, mesmo sem saber se quer "
    "denunciar formalmente ainda.\n"
    "   c. Ir a uma DEAM (Delegacia Especializada de Atendimento à "
    "Mulher) ou delegacia comum (se não houver DEAM na região) para "
    "registrar Boletim de Ocorrência; se possível, levar documentos, "
    "prints de mensagens, fotos de lesões ou testemunhas.\n"
    "   d. Buscar a Defensoria Pública (gratuita) ou um advogado para "
    "solicitar medida protetiva de urgência, que pode incluir "
    "afastamento do agressor e proibição de contato.\n"
    "   e. Procurar o IML (Instituto Médico Legal) para exame de corpo "
    "de delito quando houver violência física ou sexual — isso ajuda "
    "a reunir provas.\n"
    "   f. Guardar e organizar provas com segurança (prints, áudios, "
    "fotos, testemunhas), sem se colocar em risco para obtê-las.\n\n"
    "3) COMO AJUDAR ALGUÉM PRÓXIMO QUE ESTÁ SOFRENDO VIOLÊNCIA:\n"
    "   - Escutar sem julgar, sem pressionar a pessoa a tomar decisões "
    "imediatas e sem culpabilizá-la pela situação.\n"
    "   - Acreditar no relato e validar os sentimentos dela.\n"
    "   - Ajudar a planejar a segurança (ex.: ter uma mala/documentos "
    "prontos, saber para onde ir em caso de fuga, combinar uma palavra "
    "ou sinal de emergência).\n"
    "   - Oferecer-se para acompanhar a uma delegacia, ao 180 ou à "
    "Defensoria, se ela quiser.\n"
    "   - Nunca confrontar o agressor diretamente nem compartilhar a "
    "situação sem autorização da pessoa — isso pode colocá-la em mais "
    "risco.\n"
    "   - Em caso de risco iminente observado por quem pergunta, "
    "orientar a ligar 190 imediatamente.\n\n"
    "Use esse conhecimento para responder de forma prática e acolhedora, "
    "sempre lembrando que você complementa, mas não substitui, o "
    "atendimento humano especializado."
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
    (("passo a passo", "como denunciar", "como denuncio", "boletim de ocorrência",
      "boletim de ocorrencia", "registrar ocorrência", "registrar ocorrencia"),
     "Passo a passo para denunciar: 1) em perigo imediato, ligue 190; "
     "2) ligue 180 para orientação gratuita 24h; 3) vá a uma DEAM (ou "
     "delegacia comum) para registrar o Boletim de Ocorrência, levando "
     "provas se tiver (prints, fotos, testemunhas); 4) procure a "
     "Defensoria Pública para pedir medida protetiva; 5) se houve "
     "violência física/sexual, procure o IML para exame de corpo de "
     "delito."),
    (("ajudar amiga", "ajudar uma amiga", "ajudar minha", "amiga sofre",
      "como ajudar alguém", "como ajudar alguem"),
     "Para ajudar alguém próxima: escute sem julgar e acredite no "
     "relato dela; não a pressione a tomar decisões imediatas; ofereça "
     "ajuda para ligar no 180 ou ir à delegacia, se ela quiser; ajude a "
     "planejar a segurança (documentos, para onde ir); e nunca confronte "
     "o agressor sozinha(o), isso pode colocar as duas em risco."),
    (("prova", "provas", "medida protetiva", "medidas protetivas"),
     "Provas úteis incluem prints de mensagens, fotos de lesões, "
     "áudios e testemunhas — guarde-as com segurança. A medida "
     "protetiva de urgência pode afastar o agressor e proibir contato; "
     "para solicitá-la, procure a Defensoria Pública, um advogado ou a "
     "própria delegacia no momento do boletim de ocorrência."),
    (("180", "denúncia", "denuncia", "orienta"),
     "O Ligue 180 é a Central de Atendimento à Mulher. O serviço é "
     "gratuito e funciona 24 horas. Ele oferece orientação sobre "
     "direitos e serviços da rede de atendimento."),
    (("delegacia", "deam"),
     "A DEAM é a Delegacia Especializada de Atendimento à Mulher. Ela "
     "integra a rede de atendimento especializado. Use a aba Recursos "
     "para encontrar mais informações."),
    (("física", "fisica", "psicológica", "psicologica", "sexual",
      "patrimonial", "moral", "tipos de violênci", "tipos de violenc",
      "violênci", "violenc"),
     "Violência contra a mulher pode ser física (agressão ao corpo), "
     "psicológica (humilhação, ameaça, controle), sexual (relação "
     "forçada ou constrangimento), patrimonial (destruir/reter bens e "
     "documentos) ou moral (calúnia, difamação, injúria). Se você "
     "estiver vivendo isso, procure uma pessoa de confiança ou um "
     "serviço especializado."),
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


def _remover_markdown(texto: str) -> str:
    """Remove formatação markdown (negrito, itálico, títulos e marcadores
    de lista) que a IA às vezes gera mesmo quando instruída a não usar,
    já que o widget de chat exibe o texto puro, sem interpretar markdown."""
    texto = re.sub(r"\*\*\*(.+?)\*\*\*", r"\1", texto)
    texto = re.sub(r"\*\*(.+?)\*\*", r"\1", texto)
    texto = re.sub(r"__(.+?)__", r"\1", texto)
    texto = re.sub(r"(?<!\*)\*(?!\*)([^\n*]+?)\*(?!\*)", r"\1", texto)
    texto = re.sub(r"(?<!_)_(?!_)([^\n_]+?)_(?!_)", r"\1", texto)
    texto = re.sub(r"^\s*#{1,6}\s*", "", texto, flags=re.MULTILINE)
    texto = re.sub(r"^\s*[\*\-]\s+", "- ", texto, flags=re.MULTILINE)
    texto = re.sub(r"\*+", "", texto)
    return texto.strip()


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
        if any(term in t for term in ("step by step", "how to report", "how do i report", "file a complaint", "police report")):
            return "Steps to report: 1) if in immediate danger, call 190; 2) call 180 for free 24h guidance; 3) go to a women's police station (or any station) to file a police report, bringing evidence if you have it (screenshots, photos, witnesses); 4) contact the Public Defender's Office to request a protective order; 5) if there was physical/sexual violence, seek a forensic exam."
        if any(term in t for term in ("help a friend", "help my friend", "how can i help", "support someone")):
            return "To help someone close to you: listen without judging and believe her; don't pressure her into immediate decisions; offer to help call 180 or go to the police station if she wants; help plan for safety (documents, a safe place to go); and never confront the abuser directly, that can increase the risk."
        if any(term in t for term in ("evidence", "proof", "protective order", "restraining order")):
            return "Useful evidence includes message screenshots, photos of injuries, audio recordings and witnesses — keep them safe. A protective order can remove the abuser and ban contact; to request one, contact the Public Defender's Office, a lawyer, or the police station when filing the report."
        if any(term in t for term in ("180", "report", "complaint", "guidance")):
            return "The 180 hotline is Brazil’s Women’s Support Center. It is free and operates 24 hours a day, providing guidance on rights and support services."
        if any(term in t for term in ("police station", "deam")):
            return "A DEAM is a specialized police station for women. Open the Resources tab to find more information about specialized support services."
        if any(term in t for term in ("physical", "psychological", "sexual", "financial", "moral", "types of violence", "violence", "abuse", "harassment")):
            return "Violence against women can be physical (bodily harm), psychological (humiliation, threats, control), sexual (forced or non-consensual acts), financial/patrimonial (destroying or withholding assets/documents), or moral (slander, defamation). If this is happening to you, contact someone you trust or a specialized support service."
        if any(term in t for term in ("afraid", "fear", "alone", "sad", "anxious")):
            return "I am sorry you are going through this. You deserve to be heard and respected. If it is safe, talk to someone you trust. In an emergency, call 190."
        if any(term in t for term in ("law", "maria da penha", "right")):
            return "Brazil has specific legislation to protect women, including the Maria da Penha Law. For legal guidance, contact the Public Defender’s Office or a specialized legal service."
        return "I can help with information about Rede Violeta resources, emergency contacts, types of violence, how to report, or ways to seek support. I am Violeta! 💜"
    if idioma == "es":
        if any(term in t for term in ("paso a paso", "cómo denuncio", "como denuncio", "cómo denunciar", "como denunciar")):
            return "Pasos para denunciar: 1) si hay peligro inmediato, llama al 190; 2) llama al 180 para orientación gratuita 24h; 3) ve a una comisaría especializada (o comisaría común) para registrar la denuncia, llevando pruebas si tienes (capturas de pantalla, fotos, testigos); 4) contacta a la Defensoría Pública para solicitar una medida de protección; 5) si hubo violencia física o sexual, busca un examen médico legal."
        if any(term in t for term in ("ayudar a una amiga", "cómo puedo ayudar", "como puedo ayudar", "apoyar a alguien")):
            return "Para ayudar a alguien cercana: escúchala sin juzgar y cree en su relato; no la presiones a tomar decisiones inmediatas; ofrécele ayuda para llamar al 180 o ir a la comisaría si ella quiere; ayúdala a planear su seguridad (documentos, un lugar seguro); y nunca confrontes al agresor directamente, eso puede aumentar el riesgo."
        if any(term in t for term in ("prueba", "pruebas", "medida de protección", "medida protectiva")):
            return "Pruebas útiles incluyen capturas de mensajes, fotos de lesiones, audios y testigos — guárdalas con seguridad. La medida de protección puede alejar al agresor y prohibir el contacto; para solicitarla, contacta a la Defensoría Pública, un abogado o la misma comisaría al registrar la denuncia."
        if any(term in t for term in ("180", "denuncia", "orienta")):
            return "La línea 180 es el Centro de Atención a las Mujeres de Brasil. Es gratuita y funciona las 24 horas. Ofrece orientación sobre derechos y servicios de apoyo."
        if any(term in t for term in ("comisaría", "policia", "deam")):
            return "La DEAM es una comisaría especializada en la atención a las mujeres. Consulta la pestaña Recursos para obtener más información sobre los servicios especializados."
        if any(term in t for term in ("física", "psicológica", "sexual", "patrimonial", "moral", "tipos de violencia", "violencia", "acoso", "abuso")):
            return "La violencia contra las mujeres puede ser física (daño corporal), psicológica (humillación, amenazas, control), sexual (actos forzados o sin consentimiento), patrimonial (destruir o retener bienes/documentos) o moral (calumnia, difamación). Si estás viviendo esta situación, busca a alguien de confianza o un servicio especializado."
        if any(term in t for term in ("miedo", "sola", "triste", "ansio")):
            return "Siento mucho que estés pasando por esto. Mereces que te escuchen y te respeten. Si es seguro, habla con alguien de confianza. En una emergencia, llama al 190."
        if any(term in t for term in ("ley", "maria da penha", "derecho")):
            return "Brasil cuenta con legislación específica para proteger a las mujeres, incluida la Ley Maria da Penha. Para recibir orientación jurídica, contacta con la Defensoría Pública o un servicio especializado."
        return "Puedo ayudarte con información sobre los recursos de Rede Violeta, teléfonos de emergencia, tipos de violencia, cómo denunciar o formas de buscar apoyo. ¡Soy Violeta! 💜"
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
            conteudo = data["choices"][0]["message"]["content"].strip()
            return _remover_markdown(conteudo)
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


_PROMPT_MODERACAO_ALERTA = (
    "Você é a Violeta IA, responsável por moderar alertas comunitários do "
    "projeto Rede Violeta (avisos enviados pela comunidade sobre situações "
    "de risco em locais públicos, ex.: ruas mal iluminadas, assédio "
    "recorrente, presença de agressor conhecido na região).\n\n"
    "Para o alerta abaixo, responda SOMENTE com um JSON válido, sem "
    "nenhum texto antes ou depois, no formato exato:\n"
    '{"urgencia": "alta" | "media" | "baixa", "resumo": "uma frase curta"}\n\n'
    "Critérios de urgência:\n"
    "- alta: risco físico iminente ou recorrente (agressão, arma, "
    "perseguição, agressor presente na região).\n"
    "- media: situação preocupante mas sem indício de risco imediato "
    "(local mal iluminado, assédio verbal isolado, suspeita).\n"
    "- baixa: aviso informativo, sem indício concreto de perigo.\n"
    "O resumo deve ter no máximo 20 palavras, em português, sem markdown, "
    "sem repetir literalmente o título."
)


async def analisar_alerta_ia(titulo: str, descricao: str) -> dict[str, str] | None:
    """Usa a Violeta IA para classificar a urgência e gerar um resumo
    curto de um alerta comunitário recém-criado.

    Retorna None se a IA não estiver configurada ou a chamada falhar —
    nesse caso o alerta é salvo normalmente, apenas sem moderação da IA."""
    if not settings.ai_enabled:
        return None

    payload: dict[str, Any] = {
        "model": settings.openai_model,
        "messages": [
            {"role": "system", "content": _PROMPT_MODERACAO_ALERTA},
            {"role": "user", "content": f"Título: {titulo}\nDescrição: {descricao}"},
        ],
        "temperature": 0.2,
        # Alguns modelos (ex.: gpt-oss da Groq) gastam parte do orçamento de
        # tokens em "raciocínio" interno antes de gerar a resposta final —
        # por isso o limite precisa ser generoso, senão o conteúdo final
        # chega vazio e a moderação falha silenciosamente.
        "max_tokens": 600,
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
            conteudo = (data["choices"][0]["message"].get("content") or "").strip()
            conteudo = re.sub(r"^```(?:json)?\s*|\s*```$", "", conteudo.strip())
            resultado = json.loads(conteudo)
            urgencia = str(resultado.get("urgencia", "")).strip().lower()
            resumo = _remover_markdown(str(resultado.get("resumo", "")).strip())
            if urgencia not in ("alta", "media", "baixa"):
                return None
            return {"urgencia": urgencia, "resumo": resumo}
    except Exception:
        # Qualquer falha (IA indisponível, resposta fora do formato
        # esperado, etc.) faz o alerta ser salvo sem moderação da IA,
        # mantendo o valor de urgência escolhido pela pessoa que avisou.
        return None

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

import re
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
    "- Se perceber qualquer sinal de risco iminente, reforce IMEDIATAMENTE "
    "a importância de buscar um local seguro e ligar 190, antes de "
    "qualquer outra orientação.\n"
    "- Nunca minimize, julgue ou duvide do relato da pessoa.\n"
    "- Responda no idioma solicitado pela pessoa, em tom acolhedor, claro "
    "e objetivo (no máximo 4-5 frases por resposta).\n"
    "- Responda sempre em texto corrido simples, SEM formatação markdown "
    "(sem **negrito**, sem *itálico*, sem títulos com #, sem listas com "
    "asteriscos ou hífens). Se precisar listar itens, separe por vírgulas "
    "ou numere como '1)', '2)', '3)' dentro do próprio texto.\n\n"
    "Tópicos que você deve saber explicar quando perguntada:\n\n"
    "1) TIPOS DE VIOLÊNCIA (Lei Maria da Penha, art. 7º):\n"
    "   - Física: qualquer conduta que ofenda a integridade/saúde "
    "corporal (empurrões, tapas, socos, espancamento).\n"
    "   - Psicológica: humilhação, ameaça, manipulação, isolamento de "
    "amigos/família, controle excessivo, chantagem emocional.\n"
    "   - Sexual: forçar/constranger a presenciar, manter ou participar "
    "de relação sexual não desejada, impedir uso de método "
    "contraceptivo, forçar casamento ou prostituição.\n"
    "   - Patrimonial: destruir, reter ou subtrair bens, documentos, "
    "valores ou instrumentos de trabalho da mulher.\n"
    "   - Moral: calúnia, difamação ou injúria (ex.: espalhar mentiras "
    "ou xingamentos ofensivos sobre a mulher).\n\n"
    "2) PASSO A PASSO PARA DENUNCIAR:\n"
    "   a. Se houver perigo imediato, ligar 190 (Polícia Militar) "
    "primeiro.\n"
    "   b. Ligar 180 (Central de Atendimento à Mulher, gratuito e 24h) "
    "para orientação e encaminhamento, mesmo sem saber se quer "
    "denunciar formalmente ainda.\n"
    "   c. Ir a uma DEAM (Delegacia Especializada de Atendimento à "
    "Mulher) ou delegacia comum (se não houver DEAM na região) para "
    "registrar Boletim de Ocorrência; se possível, levar documentos, "
    "prints de mensagens, fotos de lesões ou testemunhas.\n"
    "   d. Buscar a Defensoria Pública (gratuita) ou um advogado para "
    "solicitar medida protetiva de urgência, que pode incluir "
    "afastamento do agressor e proibição de contato.\n"
    "   e. Procurar o IML (Instituto Médico Legal) para exame de corpo "
    "de delito quando houver violência física ou sexual — isso ajuda "
    "a reunir provas.\n"
    "   f. Guardar e organizar provas com segurança (prints, áudios, "
    "fotos, testemunhas), sem se colocar em risco para obtê-las.\n\n"
    "3) COMO AJUDAR ALGUÉM PRÓXIMO QUE ESTÁ SOFRENDO VIOLÊNCIA:\n"
    "   - Escutar sem julgar, sem pressionar a pessoa a tomar decisões "
    "imediatas e sem culpabilizá-la pela situação.\n"
    "   - Acreditar no relato e validar os sentimentos dela.\n"
    "   - Ajudar a planejar a segurança (ex.: ter uma mala/documentos "
    "prontos, saber para onde ir em caso de fuga, combinar uma palavra "
    "ou sinal de emergência).\n"
    "   - Oferecer-se para acompanhar a uma delegacia, ao 180 ou à "
    "Defensoria, se ela quiser.\n"
    "   - Nunca confrontar o agressor diretamente nem compartilhar a "
    "situação sem autorização da pessoa — isso pode colocá-la em mais "
    "risco.\n"
    "   - Em caso de risco iminente observado por quem pergunta, "
    "orientar a ligar 190 imediatamente.\n\n"
    "Use esse conhecimento para responder de forma prática e acolhedora, "
    "sempre lembrando que você complementa, mas não substitui, o "
    "atendimento humano especializado."
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
    (("passo a passo", "como denunciar", "como denuncio", "boletim de ocorrência",
      "boletim de ocorrencia", "registrar ocorrência", "registrar ocorrencia"),
     "Passo a passo para denunciar: 1) em perigo imediato, ligue 190; "
     "2) ligue 180 para orientação gratuita 24h; 3) vá a uma DEAM (ou "
     "delegacia comum) para registrar o Boletim de Ocorrência, levando "
     "provas se tiver (prints, fotos, testemunhas); 4) procure a "
     "Defensoria Pública para pedir medida protetiva; 5) se houve "
     "violência física/sexual, procure o IML para exame de corpo de "
     "delito."),
    (("ajudar amiga", "ajudar uma amiga", "ajudar minha", "amiga sofre",
      "como ajudar alguém", "como ajudar alguem"),
     "Para ajudar alguém próxima: escute sem julgar e acredite no "
     "relato dela; não a pressione a tomar decisões imediatas; ofereça "
     "ajuda para ligar no 180 ou ir à delegacia, se ela quiser; ajude a "
     "planejar a segurança (documentos, para onde ir); e nunca confronte "
     "o agressor sozinha(o), isso pode colocar as duas em risco."),
    (("prova", "provas", "medida protetiva", "medidas protetivas"),
     "Provas úteis incluem prints de mensagens, fotos de lesões, "
     "áudios e testemunhas — guarde-as com segurança. A medida "
     "protetiva de urgência pode afastar o agressor e proibir contato; "
     "para solicitá-la, procure a Defensoria Pública, um advogado ou a "
     "própria delegacia no momento do boletim de ocorrência."),
    (("180", "denúncia", "denuncia", "orienta"),
     "O Ligue 180 é a Central de Atendimento à Mulher. O serviço é "
     "gratuito e funciona 24 horas. Ele oferece orientação sobre "
     "direitos e serviços da rede de atendimento."),
    (("delegacia", "deam"),
     "A DEAM é a Delegacia Especializada de Atendimento à Mulher. Ela "
     "integra a rede de atendimento especializado. Use a aba Recursos "
     "para encontrar mais informações."),
    (("física", "fisica", "psicológica", "psicologica", "sexual",
      "patrimonial", "moral", "tipos de violênci", "tipos de violenc",
      "violênci", "violenc"),
     "Violência contra a mulher pode ser física (agressão ao corpo), "
     "psicológica (humilhação, ameaça, controle), sexual (relação "
     "forçada ou constrangimento), patrimonial (destruir/reter bens e "
     "documentos) ou moral (calúnia, difamação, injúria). Se você "
     "estiver vivendo isso, procure uma pessoa de confiança ou um "
     "serviço especializado."),
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


def _remover_markdown(texto: str) -> str:
    """Remove formatação markdown (negrito, itálico, títulos e marcadores
    de lista) que a IA às vezes gera mesmo quando instruída a não usar,
    já que o widget de chat exibe o texto puro, sem interpretar markdown."""
    texto = re.sub(r"\*\*\*(.+?)\*\*\*", r"\1", texto)
    texto = re.sub(r"\*\*(.+?)\*\*", r"\1", texto)
    texto = re.sub(r"__(.+?)__", r"\1", texto)
    texto = re.sub(r"(?<!\*)\*(?!\*)([^\n*]+?)\*(?!\*)", r"\1", texto)
    texto = re.sub(r"(?<!_)_(?!_)([^\n_]+?)_(?!_)", r"\1", texto)
    texto = re.sub(r"^\s*#{1,6}\s*", "", texto, flags=re.MULTILINE)
    texto = re.sub(r"^\s*[\*\-]\s+", "- ", texto, flags=re.MULTILINE)
    texto = re.sub(r"\*+", "", texto)
    return texto.strip()


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
        if any(term in t for term in ("step by step", "how to report", "how do i report", "file a complaint", "police report")):
            return "Steps to report: 1) if in immediate danger, call 190; 2) call 180 for free 24h guidance; 3) go to a women's police station (or any station) to file a police report, bringing evidence if you have it (screenshots, photos, witnesses); 4) contact the Public Defender's Office to request a protective order; 5) if there was physical/sexual violence, seek a forensic exam."
        if any(term in t for term in ("help a friend", "help my friend", "how can i help", "support someone")):
            return "To help someone close to you: listen without judging and believe her; don't pressure her into immediate decisions; offer to help call 180 or go to the police station if she wants; help plan for safety (documents, a safe place to go); and never confront the abuser directly, that can increase the risk."
        if any(term in t for term in ("evidence", "proof", "protective order", "restraining order")):
            return "Useful evidence includes message screenshots, photos of injuries, audio recordings and witnesses — keep them safe. A protective order can remove the abuser and ban contact; to request one, contact the Public Defender's Office, a lawyer, or the police station when filing the report."
        if any(term in t for term in ("180", "report", "complaint", "guidance")):
            return "The 180 hotline is Brazil’s Women’s Support Center. It is free and operates 24 hours a day, providing guidance on rights and support services."
        if any(term in t for term in ("police station", "deam")):
            return "A DEAM is a specialized police station for women. Open the Resources tab to find more information about specialized support services."
        if any(term in t for term in ("physical", "psychological", "sexual", "financial", "moral", "types of violence", "violence", "abuse", "harassment")):
            return "Violence against women can be physical (bodily harm), psychological (humiliation, threats, control), sexual (forced or non-consensual acts), financial/patrimonial (destroying or withholding assets/documents), or moral (slander, defamation). If this is happening to you, contact someone you trust or a specialized support service."
        if any(term in t for term in ("afraid", "fear", "alone", "sad", "anxious")):
            return "I am sorry you are going through this. You deserve to be heard and respected. If it is safe, talk to someone you trust. In an emergency, call 190."
        if any(term in t for term in ("law", "maria da penha", "right")):
            return "Brazil has specific legislation to protect women, including the Maria da Penha Law. For legal guidance, contact the Public Defender’s Office or a specialized legal service."
        return "I can help with information about Rede Violeta resources, emergency contacts, types of violence, how to report, or ways to seek support. I am Violeta! 💜"
    if idioma == "es":
        if any(term in t for term in ("paso a paso", "cómo denuncio", "como denuncio", "cómo denunciar", "como denunciar")):
            return "Pasos para denunciar: 1) si hay peligro inmediato, llama al 190; 2) llama al 180 para orientación gratuita 24h; 3) ve a una comisaría especializada (o comisaría común) para registrar la denuncia, llevando pruebas si tienes (capturas de pantalla, fotos, testigos); 4) contacta a la Defensoría Pública para solicitar una medida de protección; 5) si hubo violencia física o sexual, busca un examen médico legal."
        if any(term in t for term in ("ayudar a una amiga", "cómo puedo ayudar", "como puedo ayudar", "apoyar a alguien")):
            return "Para ayudar a alguien cercana: escúchala sin juzgar y cree en su relato; no la presiones a tomar decisiones inmediatas; ofrécele ayuda para llamar al 180 o ir a la comisaría si ella quiere; ayúdala a planear su seguridad (documentos, un lugar seguro); y nunca confrontes al agresor directamente, eso puede aumentar el riesgo."
        if any(term in t for term in ("prueba", "pruebas", "medida de protección", "medida protectiva")):
            return "Pruebas útiles incluyen capturas de mensajes, fotos de lesiones, audios y testigos — guárdalas con seguridad. La medida de protección puede alejar al agresor y prohibir el contacto; para solicitarla, contacta a la Defensoría Pública, un abogado o la misma comisaría al registrar la denuncia."
        if any(term in t for term in ("180", "denuncia", "orienta")):
            return "La línea 180 es el Centro de Atención a las Mujeres de Brasil. Es gratuita y funciona las 24 horas. Ofrece orientación sobre derechos y servicios de apoyo."
        if any(term in t for term in ("comisaría", "policia", "deam")):
            return "La DEAM es una comisaría especializada en la atención a las mujeres. Consulta la pestaña Recursos para obtener más información sobre los servicios especializados."
        if any(term in t for term in ("física", "psicológica", "sexual", "patrimonial", "moral", "tipos de violencia", "violencia", "acoso", "abuso")):
            return "La violencia contra las mujeres puede ser física (daño corporal), psicológica (humillación, amenazas, control), sexual (actos forzados o sin consentimiento), patrimonial (destruir o retener bienes/documentos) o moral (calumnia, difamación). Si estás viviendo esta situación, busca a alguien de confianza o un servicio especializado."
        if any(term in t for term in ("miedo", "sola", "triste", "ansio")):
            return "Siento mucho que estés pasando por esto. Mereces que te escuchen y te respeten. Si es seguro, habla con alguien de confianza. En una emergencia, llama al 190."
        if any(term in t for term in ("ley", "maria da penha", "derecho")):
            return "Brasil cuenta con legislación específica para proteger a las mujeres, incluida la Ley Maria da Penha. Para recibir orientación jurídica, contacta con la Defensoría Pública o un servicio especializado."
        return "Puedo ayudarte con información sobre los recursos de Rede Violeta, teléfonos de emergencia, tipos de violencia, cómo denunciar o formas de buscar apoyo. ¡Soy Violeta! 💜"
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
            conteudo = data["choices"][0]["message"]["content"].strip()
            return _remover_markdown(conteudo)
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
_PROMPT_MODERACAO_ALERTA = (
    "Você é a Violeta IA, responsável por moderar alertas comunitários do "
    "projeto Rede Violeta (avisos enviados pela comunidade sobre situações "
    "de risco em locais públicos, ex.: ruas mal iluminadas, assédio "
    "recorrente, presença de agressor conhecido na região).\n\n"
    "Para o alerta abaixo, responda SOMENTE com um JSON válido, sem "
    "nenhum texto antes ou depois, no formato exato:\n"
    '{"urgencia": "alta" | "media" | "baixa", "resumo": "uma frase curta"}\n\n'
    "Critérios de urgência:\n"
    "- alta: risco físico iminente ou recorrente (agressão, arma, "
    "perseguição, agressor presente na região).\n"
    "- media: situação preocupante mas sem indício de risco imediato "
    "(local mal iluminado, assédio verbal isolado, suspeita).\n"
    "- baixa: aviso informativo, sem indício concreto de perigo.\n"
    "O resumo deve ter no máximo 20 palavras, em português, sem markdown, "
    "sem repetir literalmente o título."
)


async def analisar_alerta_ia(titulo: str, descricao: str) -> dict[str, str] | None:
    """Usa a Violeta IA para classificar a urgência e gerar um resumo
    curto de um alerta comunitário recém-criado.

    Retorna None se a IA não estiver configurada ou a chamada falhar —
    nesse caso o alerta é salvo normalmente, apenas sem moderação da IA."""
    if not settings.ai_enabled:
        return None

    payload: dict[str, Any] = {
        "model": settings.openai_model,
        "messages": [
            {"role": "system", "content": _PROMPT_MODERACAO_ALERTA},
            {"role": "user", "content": f"Título: {titulo}\nDescrição: {descricao}"},
        ],
        "temperature": 0.2,
        # Alguns modelos (ex.: gpt-oss da Groq) gastam parte do orçamento de
        # tokens em "raciocínio" interno antes de gerar a resposta final —
        # por isso o limite precisa ser generoso, senão o conteúdo final
        # chega vazio e a moderação falha silenciosamente.
        "max_tokens": 600,
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
            conteudo = (data["choices"][0]["message"].get("content") or "").strip()
            conteudo = re.sub(r"^```(?:json)?\s*|\s*```$", "", conteudo.strip())
            resultado = json.loads(conteudo)
            urgencia = str(resultado.get("urgencia", "")).strip().lower()
            resumo = _remover_markdown(str(resultado.get("resumo", "")).strip())
            if urgencia not in ("alta", "media", "baixa"):
                return None
            return {"urgencia": urgencia, "resumo": resumo}
    except Exception:
        # Qualquer falha (IA indisponível, resposta fora do formato
        # esperado, etc.) faz o alerta ser salvo sem moderação da IA,
        # mantendo o valor de urgência escolhido pela pessoa que avisou.
        return None

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

import re
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
    "- Se perceber qualquer sinal de risco iminente, reforce IMEDIATAMENTE "
    "a importância de buscar um local seguro e ligar 190, antes de "
    "qualquer outra orientação.\n"
    "- Nunca minimize, julgue ou duvide do relato da pessoa.\n"
    "- Responda no idioma solicitado pela pessoa, em tom acolhedor, claro "
    "e objetivo (no máximo 4-5 frases por resposta).\n"
    "- Responda sempre em texto corrido simples, SEM formatação markdown "
    "(sem **negrito**, sem *itálico*, sem títulos com #, sem listas com "
    "asteriscos ou hífens). Se precisar listar itens, separe por vírgulas "
    "ou numere como '1)', '2)', '3)' dentro do próprio texto.\n\n"
    "Tópicos que você deve saber explicar quando perguntada:\n\n"
    "1) TIPOS DE VIOLÊNCIA (Lei Maria da Penha, art. 7º):\n"
    "   - Física: qualquer conduta que ofenda a integridade/saúde "
    "corporal (empurrões, tapas, socos, espancamento).\n"
    "   - Psicológica: humilhação, ameaça, manipulação, isolamento de "
    "amigos/família, controle excessivo, chantagem emocional.\n"
    "   - Sexual: forçar/constranger a presenciar, manter ou participar "
    "de relação sexual não desejada, impedir uso de método "
    "contraceptivo, forçar casamento ou prostituição.\n"
    "   - Patrimonial: destruir, reter ou subtrair bens, documentos, "
    "valores ou instrumentos de trabalho da mulher.\n"
    "   - Moral: calúnia, difamação ou injúria (ex.: espalhar mentiras "
    "ou xingamentos ofensivos sobre a mulher).\n\n"
    "2) PASSO A PASSO PARA DENUNCIAR:\n"
    "   a. Se houver perigo imediato, ligar 190 (Polícia Militar) "
    "primeiro.\n"
    "   b. Ligar 180 (Central de Atendimento à Mulher, gratuito e 24h) "
    "para orientação e encaminhamento, mesmo sem saber se quer "
    "denunciar formalmente ainda.\n"
    "   c. Ir a uma DEAM (Delegacia Especializada de Atendimento à "
    "Mulher) ou delegacia comum (se não houver DEAM na região) para "
    "registrar Boletim de Ocorrência; se possível, levar documentos, "
    "prints de mensagens, fotos de lesões ou testemunhas.\n"
    "   d. Buscar a Defensoria Pública (gratuita) ou um advogado para "
    "solicitar medida protetiva de urgência, que pode incluir "
    "afastamento do agressor e proibição de contato.\n"
    "   e. Procurar o IML (Instituto Médico Legal) para exame de corpo "
    "de delito quando houver violência física ou sexual — isso ajuda "
    "a reunir provas.\n"
    "   f. Guardar e organizar provas com segurança (prints, áudios, "
    "fotos, testemunhas), sem se colocar em risco para obtê-las.\n\n"
    "3) COMO AJUDAR ALGUÉM PRÓXIMO QUE ESTÁ SOFRENDO VIOLÊNCIA:\n"
    "   - Escutar sem julgar, sem pressionar a pessoa a tomar decisões "
    "imediatas e sem culpabilizá-la pela situação.\n"
    "   - Acreditar no relato e validar os sentimentos dela.\n"
    "   - Ajudar a planejar a segurança (ex.: ter uma mala/documentos "
    "prontos, saber para onde ir em caso de fuga, combinar uma palavra "
    "ou sinal de emergência).\n"
    "   - Oferecer-se para acompanhar a uma delegacia, ao 180 ou à "
    "Defensoria, se ela quiser.\n"
    "   - Nunca confrontar o agressor diretamente nem compartilhar a "
    "situação sem autorização da pessoa — isso pode colocá-la em mais "
    "risco.\n"
    "   - Em caso de risco iminente observado por quem pergunta, "
    "orientar a ligar 190 imediatamente.\n\n"
    "Use esse conhecimento para responder de forma prática e acolhedora, "
    "sempre lembrando que você complementa, mas não substitui, o "
    "atendimento humano especializado."
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
    (("passo a passo", "como denunciar", "como denuncio", "boletim de ocorrência",
      "boletim de ocorrencia", "registrar ocorrência", "registrar ocorrencia"),
     "Passo a passo para denunciar: 1) em perigo imediato, ligue 190; "
     "2) ligue 180 para orientação gratuita 24h; 3) vá a uma DEAM (ou "
     "delegacia comum) para registrar o Boletim de Ocorrência, levando "
     "provas se tiver (prints, fotos, testemunhas); 4) procure a "
     "Defensoria Pública para pedir medida protetiva; 5) se houve "
     "violência física/sexual, procure o IML para exame de corpo de "
     "delito."),
    (("ajudar amiga", "ajudar uma amiga", "ajudar minha", "amiga sofre",
      "como ajudar alguém", "como ajudar alguem"),
     "Para ajudar alguém próxima: escute sem julgar e acredite no "
     "relato dela; não a pressione a tomar decisões imediatas; ofereça "
     "ajuda para ligar no 180 ou ir à delegacia, se ela quiser; ajude a "
     "planejar a segurança (documentos, para onde ir); e nunca confronte "
     "o agressor sozinha(o), isso pode colocar as duas em risco."),
    (("prova", "provas", "medida protetiva", "medidas protetivas"),
     "Provas úteis incluem prints de mensagens, fotos de lesões, "
     "áudios e testemunhas — guarde-as com segurança. A medida "
     "protetiva de urgência pode afastar o agressor e proibir contato; "
     "para solicitá-la, procure a Defensoria Pública, um advogado ou a "
     "própria delegacia no momento do boletim de ocorrência."),
    (("180", "denúncia", "denuncia", "orienta"),
     "O Ligue 180 é a Central de Atendimento à Mulher. O serviço é "
     "gratuito e funciona 24 horas. Ele oferece orientação sobre "
     "direitos e serviços da rede de atendimento."),
    (("delegacia", "deam"),
     "A DEAM é a Delegacia Especializada de Atendimento à Mulher. Ela "
     "integra a rede de atendimento especializado. Use a aba Recursos "
     "para encontrar mais informações."),
    (("física", "fisica", "psicológica", "psicologica", "sexual",
      "patrimonial", "moral", "tipos de violênci", "tipos de violenc",
      "violênci", "violenc"),
     "Violência contra a mulher pode ser física (agressão ao corpo), "
     "psicológica (humilhação, ameaça, controle), sexual (relação "
     "forçada ou constrangimento), patrimonial (destruir/reter bens e "
     "documentos) ou moral (calúnia, difamação, injúria). Se você "
     "estiver vivendo isso, procure uma pessoa de confiança ou um "
     "serviço especializado."),
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


def _remover_markdown(texto: str) -> str:
    """Remove formatação markdown (negrito, itálico, títulos e marcadores
    de lista) que a IA às vezes gera mesmo quando instruída a não usar,
    já que o widget de chat exibe o texto puro, sem interpretar markdown."""
    texto = re.sub(r"\*\*\*(.+?)\*\*\*", r"\1", texto)
    texto = re.sub(r"\*\*(.+?)\*\*", r"\1", texto)
    texto = re.sub(r"__(.+?)__", r"\1", texto)
    texto = re.sub(r"(?<!\*)\*(?!\*)([^\n*]+?)\*(?!\*)", r"\1", texto)
    texto = re.sub(r"(?<!_)_(?!_)([^\n_]+?)_(?!_)", r"\1", texto)
    texto = re.sub(r"^\s*#{1,6}\s*", "", texto, flags=re.MULTILINE)
    texto = re.sub(r"^\s*[\*\-]\s+", "- ", texto, flags=re.MULTILINE)
    texto = re.sub(r"\*+", "", texto)
    return texto.strip()


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
        if any(term in t for term in ("step by step", "how to report", "how do i report", "file a complaint", "police report")):
            return "Steps to report: 1) if in immediate danger, call 190; 2) call 180 for free 24h guidance; 3) go to a women's police station (or any station) to file a police report, bringing evidence if you have it (screenshots, photos, witnesses); 4) contact the Public Defender's Office to request a protective order; 5) if there was physical/sexual violence, seek a forensic exam."
        if any(term in t for term in ("help a friend", "help my friend", "how can i help", "support someone")):
            return "To help someone close to you: listen without judging and believe her; don't pressure her into immediate decisions; offer to help call 180 or go to the police station if she wants; help plan for safety (documents, a safe place to go); and never confront the abuser directly, that can increase the risk."
        if any(term in t for term in ("evidence", "proof", "protective order", "restraining order")):
            return "Useful evidence includes message screenshots, photos of injuries, audio recordings and witnesses — keep them safe. A protective order can remove the abuser and ban contact; to request one, contact the Public Defender's Office, a lawyer, or the police station when filing the report."
        if any(term in t for term in ("180", "report", "complaint", "guidance")):
            return "The 180 hotline is Brazil’s Women’s Support Center. It is free and operates 24 hours a day, providing guidance on rights and support services."
        if any(term in t for term in ("police station", "deam")):
            return "A DEAM is a specialized police station for women. Open the Resources tab to find more information about specialized support services."
        if any(term in t for term in ("physical", "psychological", "sexual", "financial", "moral", "types of violence", "violence", "abuse", "harassment")):
            return "Violence against women can be physical (bodily harm), psychological (humiliation, threats, control), sexual (forced or non-consensual acts), financial/patrimonial (destroying or withholding assets/documents), or moral (slander, defamation). If this is happening to you, contact someone you trust or a specialized support service."
        if any(term in t for term in ("afraid", "fear", "alone", "sad", "anxious")):
            return "I am sorry you are going through this. You deserve to be heard and respected. If it is safe, talk to someone you trust. In an emergency, call 190."
        if any(term in t for term in ("law", "maria da penha", "right")):
            return "Brazil has specific legislation to protect women, including the Maria da Penha Law. For legal guidance, contact the Public Defender’s Office or a specialized legal service."
        return "I can help with information about Rede Violeta resources, emergency contacts, types of violence, how to report, or ways to seek support. I am Violeta! 💜"
    if idioma == "es":
        if any(term in t for term in ("paso a paso", "cómo denuncio", "como denuncio", "cómo denunciar", "como denunciar")):
            return "Pasos para denunciar: 1) si hay peligro inmediato, llama al 190; 2) llama al 180 para orientación gratuita 24h; 3) ve a una comisaría especializada (o comisaría común) para registrar la denuncia, llevando pruebas si tienes (capturas de pantalla, fotos, testigos); 4) contacta a la Defensoría Pública para solicitar una medida de protección; 5) si hubo violencia física o sexual, busca un examen médico legal."
        if any(term in t for term in ("ayudar a una amiga", "cómo puedo ayudar", "como puedo ayudar", "apoyar a alguien")):
            return "Para ayudar a alguien cercana: escúchala sin juzgar y cree en su relato; no la presiones a tomar decisiones inmediatas; ofrécele ayuda para llamar al 180 o ir a la comisaría si ella quiere; ayúdala a planear su seguridad (documentos, un lugar seguro); y nunca confrontes al agresor directamente, eso puede aumentar el riesgo."
        if any(term in t for term in ("prueba", "pruebas", "medida de protección", "medida protectiva")):
            return "Pruebas útiles incluyen capturas de mensajes, fotos de lesiones, audios y testigos — guárdalas con seguridad. La medida de protección puede alejar al agresor y prohibir el contacto; para solicitarla, contacta a la Defensoría Pública, un abogado o la misma comisaría al registrar la denuncia."
        if any(term in t for term in ("180", "denuncia", "orienta")):
            return "La línea 180 es el Centro de Atención a las Mujeres de Brasil. Es gratuita y funciona las 24 horas. Ofrece orientación sobre derechos y servicios de apoyo."
        if any(term in t for term in ("comisaría", "policia", "deam")):
            return "La DEAM es una comisaría especializada en la atención a las mujeres. Consulta la pestaña Recursos para obtener más información sobre los servicios especializados."
        if any(term in t for term in ("física", "psicológica", "sexual", "patrimonial", "moral", "tipos de violencia", "violencia", "acoso", "abuso")):
            return "La violencia contra las mujeres puede ser física (daño corporal), psicológica (humillación, amenazas, control), sexual (actos forzados o sin consentimiento), patrimonial (destruir o retener bienes/documentos) o moral (calumnia, difamación). Si estás viviendo esta situación, busca a alguien de confianza o un servicio especializado."
        if any(term in t for term in ("miedo", "sola", "triste", "ansio")):
            return "Siento mucho que estés pasando por esto. Mereces que te escuchen y te respeten. Si es seguro, habla con alguien de confianza. En una emergencia, llama al 190."
        if any(term in t for term in ("ley", "maria da penha", "derecho")):
            return "Brasil cuenta con legislación específica para proteger a las mujeres, incluida la Ley Maria da Penha. Para recibir orientación jurídica, contacta con la Defensoría Pública o un servicio especializado."
        return "Puedo ayudarte con información sobre los recursos de Rede Violeta, teléfonos de emergencia, tipos de violencia, cómo denunciar o formas de buscar apoyo. ¡Soy Violeta! 💜"
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
            conteudo = data["choices"][0]["message"]["content"].strip()
            return _remover_markdown(conteudo)
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
