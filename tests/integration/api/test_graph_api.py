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
        def __init__(self) -> None:
            self.saved_nodes: List[GraphNode] = []
            self.saved_edges: List[GraphEdge] = []
            self.deleted_nodes: List[str] = []
            self.deleted_edges: List[tuple[str, str]] = []

        async def save_node(self, node: GraphNode) -> None:
            self.saved_nodes.append(node)

        async def save_edge(self, edge: GraphEdge) -> None:
            self.saved_edges.append(edge)

        async def get_node(self, node_id: str) -> Optional[GraphNode]:
            if node_id == "node_1":
                return GraphNode(id="node_1", label="TestNode", properties={"name": "test"})
            return None

        async def delete_node(self, node_id: str) -> None:
            self.deleted_nodes.append(node_id)

        async def delete_edge(self, source_id: str, target_id: str) -> None:
            self.deleted_edges.append((source_id, target_id))

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
    assert len(data["nodes"]) == 2


def test_graph_search_api_no_results(override_graph_repo: IGraphRepository) -> None:
    response = client.get("/api/v1/graph/search?q=unknown&hops=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data["nodes"]) == 0


def test_graph_expand_api(override_graph_repo: IGraphRepository) -> None:
    response = client.get("/api/v1/graph/expand?node_id=node_1&hops=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["nodes"]) == 2


def test_graph_ingest_api(override_graph_repo: Any) -> None:
    payload = {
        "nodes": [{"id": "n1", "label": "L1", "properties": {}}],
        "edges": [{"source_id": "n1", "target_id": "n2", "relation_type": "REL", "properties": {}}],
    }
    response = client.post("/api/v1/graph/ingest", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(override_graph_repo.saved_nodes) == 1
    assert len(override_graph_repo.saved_edges) == 1


def test_graph_create_node_api(override_graph_repo: Any) -> None:
    payload = {"id": "n1", "label": "L1", "properties": {}}
    response = client.post("/api/v1/graph/nodes", json=payload)
    assert response.status_code == 200
    assert len(override_graph_repo.saved_nodes) == 1


def test_graph_get_node_api(override_graph_repo: Any) -> None:
    response = client.get("/api/v1/graph/nodes/node_1")
    assert response.status_code == 200
    assert response.json()["id"] == "node_1"

    response = client.get("/api/v1/graph/nodes/unknown")
    assert response.status_code == 404


def test_graph_delete_node_api(override_graph_repo: Any) -> None:
    response = client.delete("/api/v1/graph/nodes/node_1")
    assert response.status_code == 200
    assert "node_1" in override_graph_repo.deleted_nodes


def test_graph_create_edge_api(override_graph_repo: Any) -> None:
    payload = {"source_id": "n1", "target_id": "n2", "relation_type": "REL", "properties": {}}
    response = client.post("/api/v1/graph/edges", json=payload)
    assert response.status_code == 200
    assert len(override_graph_repo.saved_edges) == 1


def test_graph_delete_edge_api(override_graph_repo: Any) -> None:
    response = client.delete("/api/v1/graph/edges?source_id=n1&target_id=n2")
    assert response.status_code == 200
    assert ("n1", "n2") in override_graph_repo.deleted_edges
