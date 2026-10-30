"""Variables del proceso tienen prioridad sobre el .env de la raíz."""

from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class HTTPSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore",
        hide_input_in_errors=True,
    )

    api_query_timeout_seconds: float = Field(default=10, ge=1, le=30)
    cors_origins: list[str] = Field(default_factory=lambda: [
        "http://localhost:5173", "http://127.0.0.1:5173",
    ])

    @field_validator('cors_origins')
    @classmethod
    def valid_origins(cls, values):
        from urllib.parse import urlsplit
        for value in values:
            parsed = urlsplit(value)
            if (parsed.scheme not in ('http', 'https') or not parsed.hostname
                    or parsed.username or parsed.password or parsed.path
                    or parsed.query or parsed.fragment or '*' in value):
                raise ValueError('Origen CORS invalido; usar esquema, host y puerto sin ruta')
            try:
                parsed.port
            except ValueError:
                raise ValueError('Puerto CORS invalido') from None
        return list(dict.fromkeys(values))


class Settings(HTTPSettings):
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
