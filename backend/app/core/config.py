"""Variables del proceso tienen prioridad sobre el .env de la raíz."""

from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore",
        hide_input_in_errors=True,
    )

    mongo_host: str = Field(default="127.0.0.1", pattern=r"^[a-zA-Z0-9_.-]+$")
    mongo_port: int = Field(default=27017, ge=1, le=65535)
    mongo_root_username: SecretStr = Field(min_length=1)
    mongo_root_password: SecretStr = Field(min_length=1)
    mongo_auth_source: str = "admin"
    neo4j_host: str = Field(default="127.0.0.1", pattern=r"^[a-zA-Z0-9_.-]+$")
    neo4j_port: int = Field(default=7687, ge=1, le=65535)
    neo4j_username: SecretStr = SecretStr("neo4j")
    neo4j_password: SecretStr = Field(min_length=1)
    neo4j_database: str = "neo4j"
    db_timeout_seconds: float = Field(default=3, ge=1, le=10)
