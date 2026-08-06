"""Application configuration loaded from the environment."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings with safe local-development defaults."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="RAPID_LEARN_")
    database_url: str = "sqlite:///./rapid_learn.db"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:5173"
    default_forgetting_rate: float = 0.03
    default_initial_mastery: float = 0.2

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
