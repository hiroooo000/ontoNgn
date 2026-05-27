from typing import Any, List, Optional
from unittest.mock import AsyncMock

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

    async def extract_anchor_keywords(self, text_content: str) -> list[str]:
        return []

    async def validate_anchor(self, text_content: str, candidate_node: GraphNode) -> bool:
        return True

    async def generate_links(self, new_graph: ExtractionResult, context_subgraph: ExtractionResult) -> ExtractionResult:
        return new_graph


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
async def test_generate_ontology_usecase_success() -> None:
    # 準備
    new_node = GraphNode(id="ap:Procedure1", label="Label1", properties={"type": "ap:Procedure"})
    new_edge = GraphEdge(source_id="ap:Procedure1", target_id="ap:Actor1", relation_type="rel", properties={})
    raw_result = ExtractionResult(nodes=[new_node], edges=[new_edge])

    # 統合後の結果
    linked_edge = GraphEdge(source_id="ap:Context1", target_id="ap:Procedure1", relation_type="rel2", properties={})
    linked_result = ExtractionResult(nodes=[new_node], edges=[new_edge, linked_edge])

    llm_service = MockLLMService(raw_result)
    # validate_anchorがTrueを返すようにモックを調整（デフォルトTrue）
    llm_service.generate_links = AsyncMock(return_value=linked_result)  # type: ignore
    llm_service.extract_anchor_keywords = AsyncMock(return_value=["キーワード1"])  # type: ignore

    repo = MockGraphRepository()
    context_node = GraphNode(id="ap:Context1", label="ContextLabel", properties={"type": "ap:Procedure"})
    repo.search_nodes_by_keywords = AsyncMock(return_value=[context_node])  # type: ignore
    repo.get_subgraph = AsyncMock(return_value=ExtractionResult(nodes=[context_node], edges=[]))  # type: ignore

    usecase = GenerateOntologyUseCase(llm_service, repo)

    # 実行
    res = await usecase.execute("text content")

    # 検証
    assert res == linked_result
    assert res.needs_evolution is False
    assert len(repo.saved_nodes) == 1
    assert repo.saved_nodes[0] == new_node
    # DB保存時のステータスはデフォルトではpendingにならないはずだが、
    # UnclassifiedConceptがないので特に変更なし
    assert len(repo.saved_edges) == 2

    repo.search_nodes_by_keywords.assert_called_once_with(["キーワード1"], top_k=3)
    repo.get_subgraph.assert_called_once_with(["ap:Context1"], max_hops=1)
    llm_service.generate_links.assert_called_once()


@pytest.mark.asyncio
async def test_generate_ontology_usecase_with_unclassified_concept() -> None:
    # 未分類概念が含まれる場合
    unclass_node = GraphNode(id="ap:Unclassified1", label="Unknown", properties={"type": "ap:UnclassifiedConcept"})
    raw_result = ExtractionResult(nodes=[unclass_node], edges=[])

    llm_service = MockLLMService(raw_result)
    llm_service.extract_anchor_keywords = AsyncMock(return_value=[])  # type: ignore

    repo = MockGraphRepository()
    repo.search_nodes_by_keywords = AsyncMock(return_value=[])  # type: ignore

    usecase = GenerateOntologyUseCase(llm_service, repo)

    # 実行
    res = await usecase.execute("text content with unknown concept")

    # 検証
    assert res.needs_evolution is True
    assert len(repo.saved_nodes) == 1
    # 未分類概念はDB保存時にstatus="pending"が付与される
    assert repo.saved_nodes[0].properties.get("status") == "pending"
