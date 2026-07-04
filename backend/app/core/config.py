from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    postgres_db: str = "voice_agent"
    postgres_user: str = "voice_agent"
    postgres_password: str = "voice_agent"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"
    default_provider: str = "ollama"
    ollama_base_url: str = ""
    ollama_candidate_urls: str = "http://host.docker.internal:11434,http://ollama:11434"
    lmstudio_base_url: str = "http://localhost:1234"
    ollama_request_timeout_seconds: int = 60
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    backend_public_url: str = "http://localhost:8000"
    backend_cors_origins: str = "http://localhost:5678,http://localhost:3000"
    max_upload_bytes: int = 2_000_000
    allowed_ingest_roots: str = "/workspace/knowledge,knowledge"
    stt_model_path: str = "mlx-community/whisper-base-mlx"
    tts_model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2"
    tts_device: str = "auto"
    tts_language: str = "tr"
    tts_speaker: str = ""
    tts_speaker_wav: str = ""
    log_level: str = "INFO"

    @property
    def database_url(self) -> str:
        return (
            "postgresql+psycopg://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]

    @property
    def ingest_roots(self) -> list[str]:
        return [path.strip() for path in self.allowed_ingest_roots.split(",") if path.strip()]

    @property
    def ollama_urls(self) -> list[str]:
        urls = [self.ollama_base_url, *self.ollama_candidate_urls.split(",")]
        normalized: list[str] = []
        for url in urls:
            clean = url.strip().rstrip("/")
            if clean and clean not in normalized:
                normalized.append(clean)
        return normalized


settings = Settings()
