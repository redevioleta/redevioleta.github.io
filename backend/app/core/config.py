import os
from typing import Optional
from pydantic_settings import BaseSettings

_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "fala_segura.db")

class Settings(BaseSettings):
    app_name: str = "Fala Segura API"
    api_v1_prefix: str = "/api/v1"
    database_url: str = f"sqlite:///{_DB}"
    # Origens permitidas no CORS, separadas por vírgula.
    cors_origins: str = "https://redevioleta.github.io,http://localhost:8000,http://127.0.0.1:8000"

    # ── Violeta IA (chat com IA generativa) ──
    # Compatível com qualquer provedor que siga o padrão de API da OpenAI
    # (OpenAI, Groq, OpenRouter, Azure OpenAI via gateway, etc).
    # Se `openai_api_key` não for definida, o backend cai automaticamente
    # para respostas locais baseadas em regras (sem depender de IA externa).
    openai_api_key: Optional[str] = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    openai_timeout_seconds: float = 20.0
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.5-flash"

    @property
    def sqlalchemy_database_url(self) -> str:
        """Normaliza DATABASE_URL para o driver psycopg 3 quando for PostgreSQL."""
        url = self.database_url.strip()
        for prefix in ("postgresql://", "postgres://"):
            if url.startswith(prefix):
                return "postgresql+psycopg://" + url[len(prefix):]
        return url

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip().rstrip("/") for o in self.cors_origins.split(",") if o.strip()]

    @property
    def ai_enabled(self) -> bool:
        return bool(self.openai_api_key or self.gemini_api_key)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

settings = Settings()
