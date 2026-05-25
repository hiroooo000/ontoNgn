from unittest.mock import AsyncMock, patch

import pytest

from app.core.config import Settings
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
