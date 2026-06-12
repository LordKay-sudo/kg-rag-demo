from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    neo4j_uri: str = "bolt://localhost:7688"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "changeme"

    llm_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chunk_size: int = 500
    chunk_overlap: int = 80
    top_k_chunks: int = 5
    compact_top_k: int = 2
    compact_snippet_chars: int = 120
    min_retrieval_score: float = 0.25
    widen_top_k: int = 10
    widen_min_retrieval_score: float = 0.15
    cors_origins: str = "http://localhost:5173"
    bioinsight_api_url: str = ""

    documents_dir: Path = ROOT / "data" / "documents"
    prompts_dir: Path = ROOT / "prompts"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
