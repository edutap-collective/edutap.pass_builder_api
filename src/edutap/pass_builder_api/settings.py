"""Client configuration via pydantic-settings."""

from pydantic import HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class PassBuilderSettings(BaseSettings):
    """Pass Builder API client settings."""

    model_config = SettingsConfigDict(
        env_prefix="PASS_BUILDER_",
        env_file=".env",
        extra="ignore",
    )

    base_url: HttpUrl = HttpUrl("http://localhost:8000")
    token: SecretStr | None = None
    timeout: float = 30.0
