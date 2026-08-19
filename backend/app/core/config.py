import os
from pydantic_settings import BaseSettings

_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "fala_segura.db")

class Settings(BaseSettings):
    app_name: str = "Fala Segura API"
    api_v1_prefix: str = "/api/v1"
    database_url: str = f"sqlite:///{_DB}"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

settings = Settings()
