import os

import kuzu

from app.core.config import Settings, get_settings


class KuzuDB:
    _instance = None

    def __new__(cls, settings: Settings | None = None) -> "KuzuDB":
        if cls._instance is None:
            cls._instance = super(KuzuDB, cls).__new__(cls)
            try:
                cls._instance._init_db(settings or get_settings())
            except Exception:
                cls._instance = None
                raise
        return cls._instance

    def _init_db(self, settings: Settings) -> None:
        db_path = settings.kuzu_db_path
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self.db = kuzu.Database(db_path)
        self.conn = kuzu.Connection(self.db)
        self._init_schema()

    def _init_schema(self) -> None:
        # Node table
        try:
            self.conn.execute(
                "CREATE NODE TABLE Entity ("
                "id STRING, label STRING, sourceDocumentIds STRING[], properties_json STRING, "
                "PRIMARY KEY (id))"
            )
        except RuntimeError as e:
            if "already exists" not in str(e).lower():
                raise

        # Rel table
        try:
            self.conn.execute(
                "CREATE REL TABLE Relation ("
                "FROM Entity TO Entity, relation_type STRING, sourceDocumentId STRING, properties_json STRING)"
            )
        except RuntimeError as e:
            if "already exists" not in str(e).lower():
                raise

    def get_connection(self) -> kuzu.Connection:
        return self.conn
