from typing import Any, Generator, List, Optional

import pytest
from fastapi.testclient import TestClient

from app.core.dependencies import get_graph_repository
from app.domain.models.graph import ExtractionResult, GraphEdge, GraphNode
from app.domain.services.graph_repository import IGraphRepository
from app.main import app

client = TestClient(app)


@pytest.fixture
def override_graph_repo() -> Generator[IGraphRepository, None, None]:
    class MockGraphRepository(IGraphRepository):
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

        async def delete_document_graph(self, document_id: str) -> None:
            pass

        async def search_nodes_by_keywords(self, keywords: List[str], top_k: int) -> List[GraphNode]:
            if "test" in keywords:
                return [GraphNode(id="node_1", label="TestNode", properties={"name": "test"})]
            return []

        async def get_subgraph(self, anchor_ids: List[str], max_hops: int) -> ExtractionResult:
            if "node_1" in anchor_ids:
                return ExtractionResult(
                    nodes=[
                        GraphNode(id="node_1", label="TestNode", properties={"name": "test"}),
                        GraphNode(id="node_2", label="TargetNode", properties={"name": "target"}),
                    ],
                    edges=[
                        GraphEdge(source_id="node_1", target_id="node_2", relation_type="related_to", properties={})
                    ],
                )
            return ExtractionResult(nodes=[], edges=[])

    repo = MockGraphRepository()
    app.dependency_overrides[get_graph_repository] = lambda: repo
    yield repo
    app.dependency_overrides.pop(get_graph_repository, None)


def test_graph_search_api_with_results(override_graph_repo: IGraphRepository) -> None:
    response = client.get("/api/v1/graph/search?q=test&hops=1")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    assert "hits" in data
    assert len(data["nodes"]) == 2
    assert len(data["edges"]) == 1
    assert len(data["hits"]) == 1
    assert data["nodes"][0]["id"] == "node_1"
    assert data["edges"][0]["relation_type"] == "related_to"
    assert data["hits"][0]["id"] == "node_1"


def test_graph_search_api_no_results(override_graph_repo: IGraphRepository) -> None:
    response = client.get("/api/v1/graph/search?q=unknown&hops=1")
    assert response.status_code == 200
    data = response.json()
    assert "hits" in data
    assert len(data["nodes"]) == 0
    assert len(data["edges"]) == 0
    assert len(data["hits"]) == 0


def test_graph_expand_api(override_graph_repo: IGraphRepository) -> None:
    response = client.get("/api/v1/graph/expand?node_id=node_1&hops=2")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    assert "hits" not in data
    assert len(data["nodes"]) == 2
    assert len(data["edges"]) == 1
    assert data["nodes"][0]["id"] == "node_1"
