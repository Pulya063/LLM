from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Debuggable AI Assistant"
    app_env: str = Field(default="development", alias="APP_ENV")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    model_name: str = Field(default="gpt-4o-mini", alias="MODEL_NAME")
    vector_store_dir: str = Field(default="./storage/chroma", alias="VECTOR_STORE_DIR")
    docs_dir: str = Field(default="./data/docs", alias="DOCS_DIR")
    cache_ttl_seconds: int = Field(default=120, alias="CACHE_TTL_SECONDS")
    api_key: str = Field(default="debug-assistant-key", alias="API_KEY")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        populate_by_name = True


settings = Settings()
Path(settings.vector_store_dir).mkdir(parents=True, exist_ok=True)
Path(settings.docs_dir).mkdir(parents=True, exist_ok=True)
