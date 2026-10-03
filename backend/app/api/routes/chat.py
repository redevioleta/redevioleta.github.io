from fastapi import APIRouter

from app.core.violeta_ia import responder
from app.schemas.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["Violeta IA"])


@router.post("/", response_model=ChatResponse)
async def conversar_com_violeta(dados: ChatRequest):
    """Conversa com a 'Violeta IA'.

    Não persiste nenhuma mensagem em banco de dados — o histórico
    trafega apenas dentro da própria requisição, a critério do
    frontend, para preservar a privacidade da pessoa usuária.
    """
    texto = dados.mensagem.strip()
    if not texto:
        mensagens_vazias = {
            "pt": "Pode escrever ou falar à vontade — estou aqui para ouvir. 💜",
            "en": "You can type or speak freely — I’m here to listen. 💜",
            "es": "Puedes escribir o hablar con libertad — estoy aquí para escucharte. 💜",
        }
        return ChatResponse(
            resposta=mensagens_vazias[dados.idioma],
            fonte="regras",
            alerta_seguranca=False,
        )

    resposta, fonte, alerta = await responder(texto, dados.historico, dados.idioma)
    return ChatResponse(resposta=resposta, fonte=fonte, alerta_seguranca=alerta)
