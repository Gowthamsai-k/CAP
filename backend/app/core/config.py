from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "Global Compliance Intelligence"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///../data/compliance.db"
    qdrant_mode: str = "local"
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    qdrant_path: str = "data/qdrant"
    redis_url: str | None = None
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    retrieval_similarity_threshold: float = 0.25
    llm_provider: str = "ollama"  # "ollama" or "openai"
    llm_base_url: str = "http://localhost:11434/v1"
    llm_model: str = "qwen2.5:3b"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    upload_dir: str = "data/uploads"
    company_upload_dir: str = "data/company/g-inc/uploads"
    demo_company_id: str = "g-inc-demo"
    max_upload_mb: int = 25
    cors_origins: str = "http://localhost:5173"
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore")

    @property
    def resolved_database_url(self) -> str:
        if self.database_url == "sqlite:///../data/compliance.db":
            db_path = (Path(__file__).resolve().parents[3] / "data" / "compliance.db").resolve()
            return f"sqlite:///{db_path.as_posix()}"
        return self.database_url

    @property
    def is_production(self) -> bool:
        return self.app_env.strip().lower() in {"prod", "production"}

    @property
    def active_llm_model(self) -> str:
        if self.llm_provider.lower() == "ollama":
            return self.llm_model
        return self.openai_model

    @property
    def active_llm_base_url(self) -> str | None:
        if self.llm_provider.lower() == "ollama":
            return self.llm_base_url
        return None

    @property
    def is_llm_available(self) -> bool:
        if self.llm_provider.lower() == "ollama":
            return True
        return bool(self.openai_api_key)

    @property
    def upload_path(self) -> Path:
        path = Path(self.upload_dir)
        return path if path.is_absolute() else (Path(__file__).resolve().parents[3] / path).resolve()

    @property
    def qdrant_local_path(self) -> Path:
        path = Path(self.qdrant_path)
        return path if path.is_absolute() else (Path(__file__).resolve().parents[3] / path).resolve()

    @property
    def company_upload_path(self) -> Path:
        path = Path(self.company_upload_dir)
        return path if path.is_absolute() else (Path(__file__).resolve().parents[3] / path).resolve()

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
