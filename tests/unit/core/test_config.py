import os

from app.core.config import Settings


def test_config_default_kuzu_db_path() -> None:
    settings = Settings()
    assert settings.kuzu_db_path == "./data/kuzu"


def test_config_env_override() -> None:
    os.environ["KUZU_DB_PATH"] = "/tmp/test_kuzu"
    try:
        settings = Settings()
        assert settings.kuzu_db_path == "/tmp/test_kuzu"
    finally:
        del os.environ["KUZU_DB_PATH"]
