from typing import Any, List, Optional

from fastapi.testclient import TestClient

from app.core.dependencies import get_graph_repository, get_text_llm_service
from app.domain.models.graph import ExtractionResult, GraphEdge, GraphNode
from app.domain.services.graph_repository import IGraphRepository
from app.domain.services.text_llm_service import ITextLLMService
from app.main import app


class DummyLLMService(ITextLLMService):
    async def generate_ontology(self, text_content: str) -> ExtractionResult:
        node = GraphNode(id="ap:Test", label="Test", properties={})
        return ExtractionResult(nodes=[node], edges=[])


class DummyGraphRepository(IGraphRepository):
    async def save_node(self, node: GraphNode) -> None:
        pass

    async def save_edge(self, edge: GraphEdge) -> None:
        pass

    async def get_node(self, node_id: str) -> Optional[GraphNode]:
        return None

    async def query_neighbors(self, node_id: str) -> List[GraphEdge]:
        return []

    async def export_all(self) -> ExtractionResult:
        return ExtractionResult(nodes=[], edges=[])

    async def find_nodes_by_type(self, label_type: str) -> List[GraphNode]:
        return []

    async def get_schema_definition(self) -> dict[str, Any]:
        return {}


app.dependency_overrides[get_text_llm_service] = lambda: DummyLLMService()
app.dependency_overrides[get_graph_repository] = lambda: DummyGraphRepository()

client = TestClient(app)


def test_generate_ontology_endpoint() -> None:
    response = client.post("/api/v1/ontology/generate", content="dummy text", headers={"Content-Type": "text/plain"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["nodes"]) == 1
    assert data["nodes"][0]["id"] == "ap:Test"
