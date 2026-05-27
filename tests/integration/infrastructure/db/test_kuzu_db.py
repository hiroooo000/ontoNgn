import shutil
import tempfile
from typing import Generator

import pytest

from app.core.config import Settings
from app.infrastructure.database.kuzu_db import KuzuDB


@pytest.fixture
def temp_kuzu_settings() -> Generator[Settings, None, None]:
    temp_dir = tempfile.mkdtemp()
    import os

    db_file = os.path.join(temp_dir, "test.db")
    settings = Settings(kuzu_db_path=db_file)
    yield settings
    shutil.rmtree(temp_dir, ignore_errors=True)
    KuzuDB._instance = None  # Reset singleton for other tests


def test_kuzu_db_initialization(temp_kuzu_settings: Settings) -> None:
    db = KuzuDB(settings=temp_kuzu_settings)
    conn = db.get_connection()
    assert conn is not None

    # Check if tables exist by querying schema
    # Kuzu has a built-in function to show tables: CALL show_tables() RETURN *
    res = conn.execute("CALL show_tables() RETURN *;")
    tables = []
    # Kuzu QueryResult API: has_next() and get_next()
    while res.has_next():  # type: ignore
        row = res.get_next()  # type: ignore
        # row is a list in python API according to mypy
        tables.append(row[1])  # type: ignore

    assert "Entity" in tables
    assert "Relation" in tables

    # Test idempotency (should not raise error if tables exist)
    db._init_schema()
