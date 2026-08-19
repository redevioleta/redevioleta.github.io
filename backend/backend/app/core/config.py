from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Fala Segura API"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./fala_segura.db"
    model_config = {"env_file": ".env"}
settings = Settings()
