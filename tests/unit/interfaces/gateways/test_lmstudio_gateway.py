from unittest.mock import AsyncMock, patch

import pytest

from app.core.config import Settings
from app.domain.models.graph import GraphNode
from app.interfaces.gateways.lmstudio_gateway import LMStudioGateway


@pytest.mark.asyncio
async def test_generate_ontology_success() -> None:
    settings = Settings(
        llm_api_base_url="http://test/v1", llm_api_key="test-key", text_model_name="test-model", llm_temperature=0.0
    )

    mock_response = AsyncMock()
    mock_response.choices = [
        AsyncMock(
            message=AsyncMock(
                content='{"nodes": [{"id": "ap:Proc1", "type": "ap:Procedure", "label": "L1", "properties": {}}], "relationships": []}'  # noqa: E501
            )
        )
    ]

    with patch("app.interfaces.gateways.lmstudio_gateway.AsyncOpenAI") as mock_openai_class:
        mock_client = mock_openai_class.return_value
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        gateway = LMStudioGateway(settings=settings)
        result = await gateway.generate_ontology("test text")

        assert len(result.nodes) == 1
        assert result.nodes[0].id == "ap:Proc1"
        assert len(result.edges) == 0


@pytest.mark.asyncio
async def test_extract_anchor_keywords_success() -> None:
    settings = Settings(
        llm_api_base_url="http://test/v1", llm_api_key="test-key", text_model_name="test-model", llm_temperature=0.0
    )

    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock(message=AsyncMock(content='{"keywords": ["児童手当", "対象者"]}'))]

    with patch("app.interfaces.gateways.lmstudio_gateway.AsyncOpenAI") as mock_openai_class:
        mock_client = mock_openai_class.return_value
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        gateway = LMStudioGateway(settings=settings)
        result = await gateway.extract_anchor_keywords("test text")

        assert len(result) == 2
        assert "児童手当" in result


@pytest.mark.asyncio
async def test_validate_anchor_success() -> None:
    settings = Settings(
        llm_api_base_url="http://test/v1", llm_api_key="test-key", text_model_name="test-model", llm_temperature=0.0
    )

    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock(message=AsyncMock(content='{"is_valid": true, "reason": "関連性が高いため"}'))]

    with patch("app.interfaces.gateways.lmstudio_gateway.AsyncOpenAI") as mock_openai_class:
        mock_client = mock_openai_class.return_value
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        gateway = LMStudioGateway(settings=settings)
        node = GraphNode(id="ap:Procedure1", label="児童手当", properties={"description": "児童手当の手続き"})
        result = await gateway.validate_anchor("児童手当について", node)

        assert result is True


@pytest.mark.asyncio
async def test_generate_links_success() -> None:
    settings = Settings(
        llm_api_base_url="http://test/v1", llm_api_key="test-key", text_model_name="test-model", llm_temperature=0.0
    )

    mock_response = AsyncMock()
    mock_response.choices = [
        AsyncMock(
            message=AsyncMock(
                content='{"nodes": [{"id": "ap:NewNode", "type": "ap:Procedure", "label": "N1", "properties": {}}], "relationships": [{"source": "ap:Proc1", "target": "ap:NewNode", "type": "ap:hasPrerequisite", "properties": {}}]}'  # noqa: E501
            )
        )
    ]

    with patch("app.interfaces.gateways.lmstudio_gateway.AsyncOpenAI") as mock_openai_class:
        mock_client = mock_openai_class.return_value
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        gateway = LMStudioGateway(settings=settings)
        from app.domain.models.graph import ExtractionResult

        new_graph = ExtractionResult(
            nodes=[GraphNode(id="ap:NewNode", label="N1", properties={"type": "ap:Procedure"})], edges=[]
        )
        context_graph = ExtractionResult(
            nodes=[GraphNode(id="ap:Proc1", label="P1", properties={"type": "ap:Procedure"})], edges=[]
        )

        result = await gateway.generate_links(new_graph, context_graph)

        assert len(result.nodes) == 1
        assert len(result.edges) == 1
        assert result.edges[0].source_id == "ap:Proc1"
