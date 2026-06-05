import pytest

from app.domain.models.graph import ExtractionResult, GraphEdge, GraphNode
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


@pytest.mark.asyncio
async def test_generate_ontology_usecase_success() -> None:
    # 準備
    new_node = GraphNode(id="ap:Procedure1", label="Label1", properties={"type": "ap:Procedure"})
    new_edge = GraphEdge(source_id="ap:Procedure1", target_id="ap:Actor1", relation_type="rel", properties={})
    raw_result = ExtractionResult(nodes=[new_node], edges=[new_edge])

    llm_service = MockLLMService(raw_result)
    usecase = GenerateOntologyUseCase(llm_service)

    # 実行
    res = await usecase.execute("text content")

    # 検証
    assert res == raw_result
    assert res.needs_evolution is False
    assert len(res.nodes) == 1
    assert len(res.edges) == 1


@pytest.mark.asyncio
async def test_generate_ontology_usecase_with_unclassified_concept() -> None:
    # 未分類概念が含まれる場合
    unclass_node = GraphNode(id="ap:Unclassified1", label="Unknown", properties={"type": "ap:UnclassifiedConcept"})
    raw_result = ExtractionResult(nodes=[unclass_node], edges=[])

    llm_service = MockLLMService(raw_result)
    usecase = GenerateOntologyUseCase(llm_service)

    # 実行
    res = await usecase.execute("text content with unknown concept")

    # 検証
    assert res.needs_evolution is True
    # 未分類概念はstatus="pending"が付与される
    assert res.nodes[0].properties.get("status") == "pending"
