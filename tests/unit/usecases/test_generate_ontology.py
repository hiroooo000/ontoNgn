from typing import Any, List, Optional

import pytest

from app.domain.models.graph import ExtractionResult, GraphEdge, GraphNode
from app.domain.services.graph_repository import IGraphRepository
from app.domain.services.text_llm_service import ITextLLMService
from app.usecases.generate_ontology import GenerateOntologyUseCase


class MockLLMService(ITextLLMService):
    def __init__(self, result: ExtractionResult):
        self.result = result

    async def generate_ontology(self, text_content: str) -> ExtractionResult:
        return self.result


class MockGraphRepository(IGraphRepository):
    def __init__(self) -> None:
        self.saved_nodes: list[GraphNode] = []
        self.saved_edges: list[GraphEdge] = []

    async def save_node(self, node: GraphNode) -> None:
        self.saved_nodes.append(node)

    async def save_edge(self, edge: GraphEdge) -> None:
        self.saved_edges.append(edge)

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
        return []

    async def get_subgraph(self, anchor_ids: List[str], max_hops: int) -> ExtractionResult:
        return ExtractionResult(nodes=[], edges=[])


@pytest.mark.asyncio
async def test_generate_ontology_usecase() -> None:
    node = GraphNode(id="ap:1", label="Label", properties={})
    edge = GraphEdge(source_id="ap:1", target_id="ap:2", relation_type="rel", properties={})
    result = ExtractionResult(nodes=[node], edges=[edge])

    llm_service = MockLLMService(result)
    repo = MockGraphRepository()

    usecase = GenerateOntologyUseCase(llm_service, repo)
    res = await usecase.execute("text content")

    assert res == result
    assert len(repo.saved_nodes) == 1
    assert repo.saved_nodes[0] == node
    assert len(repo.saved_edges) == 1
    assert repo.saved_edges[0] == edge
