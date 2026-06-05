from unittest.mock import AsyncMock

import pytest

from app.domain.models.graph import ExtractionResult, GraphEdge, GraphNode
from app.usecases.graph_crud import GraphCrudUseCase


@pytest.fixture
def mock_graph_repository() -> AsyncMock:
    repo = AsyncMock()
    return repo


@pytest.mark.asyncio
async def test_ingest_ontology(mock_graph_repository: AsyncMock) -> None:
    usecase = GraphCrudUseCase(mock_graph_repository)
    node1 = GraphNode(id="n1", label="Label1", properties={})
    edge1 = GraphEdge(source_id="n1", target_id="n2", relation_type="REL", properties={})

    result = ExtractionResult(nodes=[node1], edges=[edge1])

    await usecase.ingest_ontology(result)

    mock_graph_repository.save_node.assert_called_once_with(node1)
    mock_graph_repository.save_edge.assert_called_once_with(edge1)


@pytest.mark.asyncio
async def test_create_or_update_node(mock_graph_repository: AsyncMock) -> None:
    usecase = GraphCrudUseCase(mock_graph_repository)
    node = GraphNode(id="n1", label="Label1", properties={})

    await usecase.create_or_update_node(node)

    mock_graph_repository.save_node.assert_called_once_with(node)


@pytest.mark.asyncio
async def test_delete_node(mock_graph_repository: AsyncMock) -> None:
    usecase = GraphCrudUseCase(mock_graph_repository)

    await usecase.delete_node("n1")

    mock_graph_repository.delete_node.assert_called_once_with("n1")


@pytest.mark.asyncio
async def test_create_or_update_edge(mock_graph_repository: AsyncMock) -> None:
    usecase = GraphCrudUseCase(mock_graph_repository)
    edge = GraphEdge(source_id="n1", target_id="n2", relation_type="REL", properties={})

    await usecase.create_or_update_edge(edge)

    mock_graph_repository.save_edge.assert_called_once_with(edge)


@pytest.mark.asyncio
async def test_delete_edge(mock_graph_repository: AsyncMock) -> None:
    usecase = GraphCrudUseCase(mock_graph_repository)

    await usecase.delete_edge("n1", "n2")

    mock_graph_repository.delete_edge.assert_called_once_with("n1", "n2")
