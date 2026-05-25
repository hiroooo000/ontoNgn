from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    graph_db_type: str = "kuzu"
    kuzu_db_path: str = "./data/kuzu"
    llm_api_base_url: str = "http://localhost:1234/v1"
    llm_api_key: str = "lm-studio"
    text_model_name: str = "local-model"
    llm_temperature: float = 0.0

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


def get_settings() -> Settings:
    return Settings()
