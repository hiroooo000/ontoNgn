import asyncio
import json
from pathlib import Path

from app.core.config import get_settings
from app.domain.models.graph import ExtractionResult, GraphNode
from app.domain.services.text_llm_service import ITextLLMService
from app.infrastructure.database.kuzu_db import KuzuDB
from app.interfaces.repositories.kuzu_graph_repository import KuzuGraphRepository
from app.usecases.generate_ontology import GenerateOntologyUseCase


class MockLLMService(ITextLLMService):
    async def generate_ontology(self, text_content: str) -> ExtractionResult:
        raise NotImplementedError()

    async def extract_anchor_keywords(self, text_content: str) -> list[str]:
        return ["ダミーキーワード"]

    async def validate_anchor(self, text_content: str, candidate_node: GraphNode) -> bool:
        return True

    async def generate_links(self, new_graph: ExtractionResult, context_subgraph: ExtractionResult) -> ExtractionResult:
        return new_graph


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
    mock_llm = MockLLMService()

    usecase = GenerateOntologyUseCase(llm_service=mock_llm, graph_repository=repo)

    print("Loading initial dummy data into DB...")
    text_content = "dummy text content"
    await usecase.execute_context_linking(raw_graph, text_content)
    print("DB Setup Complete!\n")


if __name__ == "__main__":
    asyncio.run(main())
