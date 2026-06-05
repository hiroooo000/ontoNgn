import asyncio
import json
from pathlib import Path

from app.core.config import get_settings
from app.domain.models.graph import ExtractionResult
from app.infrastructure.database.kuzu_db import KuzuDB
from app.interfaces.repositories.kuzu_graph_repository import KuzuGraphRepository
from app.usecases.graph_crud import GraphCrudUseCase


async def main() -> None:
    print("=== Development DB Setup Script ===")

    settings = get_settings()
    db_path = settings.kuzu_db_path
    print(f"Using DB Path from Settings: {db_path}")

    json_path = Path("tests/integration/usecases/test_data/context_linking_inputs/case1_base_procedure.json")
    if not json_path.exists():
        print(f"Error: Test data not found ({json_path})")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    raw_graph = ExtractionResult.model_validate(data)

    # Initialize DB with the configured path
    KuzuDB._instance = None
    db = KuzuDB(settings=settings)
    repo = KuzuGraphRepository(db)

    usecase = GraphCrudUseCase(graph_repository=repo)

    print("Loading initial dummy data into DB...")
    await usecase.ingest_ontology(raw_graph)
    print("DB Setup Complete!\n")


if __name__ == "__main__":
    asyncio.run(main())
