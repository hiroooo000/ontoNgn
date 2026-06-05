from fastapi.testclient import TestClient

from app.core.dependencies import get_text_llm_service
from app.domain.models.graph import ExtractionResult, GraphNode
from app.domain.services.text_llm_service import ITextLLMService
from app.main import app


class DummyLLMService(ITextLLMService):
    async def generate_ontology(self, text_content: str) -> ExtractionResult:
        return ExtractionResult(
            nodes=[GraphNode(id="ap:Procedure1", label="Procedure", properties={"type": "ap:Procedure"})],
            edges=[],
        )

    async def extract_anchor_keywords(self, text_content: str) -> list[str]:
        return []

    async def validate_anchor(self, text_content: str, candidate_node: GraphNode) -> bool:
        return True

    async def generate_links(self, new_graph: ExtractionResult, context_subgraph: ExtractionResult) -> ExtractionResult:
        return new_graph


app.dependency_overrides[get_text_llm_service] = lambda: DummyLLMService()

client = TestClient(app)


def test_generate_ontology_endpoint() -> None:
    response = client.post("/api/v1/ontology/generate", content="dummy text", headers={"Content-Type": "text/plain"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["nodes"]) == 1
    assert data["nodes"][0]["id"] == "ap:Procedure1"
