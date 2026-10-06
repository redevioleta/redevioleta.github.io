import os
from typing import Optional
from pydantic_settings import BaseSettings

_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "fala_segura.db")

class Settings(BaseSettings):
    app_name: str = "Fala Segura API"
    api_v1_prefix: str = "/api/v1"
    database_url: str = f"sqlite:///{_DB}"

    # ── Violeta IA (chat com IA generativa) ──
    # Compatível com qualquer provedor que siga o padrão de API da OpenAI
    # (OpenAI, Groq, OpenRouter, Azure OpenAI via gateway, etc).
    # Se `openai_api_key` não for definida, o backend cai automaticamente
    # para respostas locais baseadas em regras (sem depender de IA externa).
    openai_api_key: Optional[str] = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    openai_timeout_seconds: float = 20.0

    @property
    def ai_enabled(self) -> bool:
        return bool(self.openai_api_key)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

settings = Settings()
