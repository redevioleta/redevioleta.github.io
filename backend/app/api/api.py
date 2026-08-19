from fastapi import APIRouter

from app.api.routes import (
    desabafos,
    assedio,
    denuncias,
    quiz,
    recursos,
    faq,
    timeline,
    delegacias,
    alertas,
)

api_router = APIRouter()

api_router.include_router(desabafos.router)
api_router.include_router(assedio.router)
api_router.include_router(denuncias.router)
api_router.include_router(quiz.router)
api_router.include_router(recursos.router)
api_router.include_router(faq.router)
api_router.include_router(timeline.router)
api_router.include_router(delegacias.router)
api_router.include_router(alertas.router)
