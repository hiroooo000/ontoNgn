import os
import shutil
import tempfile
from typing import Generator

import pytest

from app.core.config import Settings
from app.domain.models.graph import GraphNode
from app.infrastructure.database.kuzu_db import KuzuDB
from app.interfaces.repositories.kuzu_graph_repository import KuzuGraphRepository


@pytest.fixture
def temp_repo() -> Generator[KuzuGraphRepository, None, None]:
    temp_dir = tempfile.mkdtemp()
    db_file = os.path.join(temp_dir, "test_repo.db")
    settings = Settings(kuzu_db_path=db_file)
    KuzuDB._instance = None
    db = KuzuDB(settings=settings)
    repo = KuzuGraphRepository(db)
    yield repo
    shutil.rmtree(temp_dir, ignore_errors=True)
    KuzuDB._instance = None


@pytest.mark.asyncio
async def test_save_and_get_node(temp_repo: KuzuGraphRepository) -> None:
    node = GraphNode(id="ap:TestNode1", label="TestLabel", properties={"key1": "value1", "key2": 123})

    # Save node
    await temp_repo.save_node(node)

    # Get node
    retrieved = await temp_repo.get_node("ap:TestNode1")
    assert retrieved is not None
    assert retrieved.id == node.id
    assert retrieved.label == node.label
    assert retrieved.properties == node.properties

    # Update node
    node.properties["key1"] = "new_value"
    await temp_repo.save_node(node)
    retrieved_updated = await temp_repo.get_node("ap:TestNode1")
    assert retrieved_updated is not None
    assert retrieved_updated.properties["key1"] == "new_value"


@pytest.mark.asyncio
async def test_get_non_existent_node(temp_repo: KuzuGraphRepository) -> None:
    retrieved = await temp_repo.get_node("non:existent")
    assert retrieved is None


@pytest.mark.asyncio
async def test_save_edge_and_query_neighbors(temp_repo: KuzuGraphRepository) -> None:
    from app.domain.models.graph import GraphEdge

    # Create two nodes first
    node1 = GraphNode(id="ap:Node1", label="Label1", properties={})
    node2 = GraphNode(id="ap:Node2", label="Label2", properties={})
    await temp_repo.save_node(node1)
    await temp_repo.save_node(node2)

    # Create an edge
    edge = GraphEdge(source_id="ap:Node1", target_id="ap:Node2", relation_type="DEPENDS_ON", properties={"weight": 1.0})
    await temp_repo.save_edge(edge)

    # Query neighbors of Node1
    neighbors = await temp_repo.query_neighbors("ap:Node1")
    assert len(neighbors) == 1
    assert neighbors[0].source_id == "ap:Node1"
    assert neighbors[0].target_id == "ap:Node2"
    assert neighbors[0].relation_type == "DEPENDS_ON"
    assert neighbors[0].properties["weight"] == 1.0


@pytest.mark.asyncio
async def test_export_all_and_find_by_type(temp_repo: KuzuGraphRepository) -> None:
    from app.domain.models.graph import GraphEdge

    node1 = GraphNode(id="ap:TypeA_1", label="TypeA", properties={})
    node2 = GraphNode(id="ap:TypeB_1", label="TypeB", properties={})
    await temp_repo.save_node(node1)
    await temp_repo.save_node(node2)

    edge = GraphEdge(source_id="ap:TypeA_1", target_id="ap:TypeB_1", relation_type="LINK", properties={})
    await temp_repo.save_edge(edge)

    # test find_nodes_by_type
    type_a_nodes = await temp_repo.find_nodes_by_type("TypeA")
    assert len(type_a_nodes) == 1
    assert type_a_nodes[0].id == "ap:TypeA_1"

    # test export_all
    exported = await temp_repo.export_all()
    assert len(exported.nodes) == 2
    assert len(exported.edges) == 1


@pytest.mark.asyncio
async def test_search_nodes_by_keywords(temp_repo: KuzuGraphRepository) -> None:
    node1 = GraphNode(id="ap:KWNode1", label="Label1", properties={"text": "artificial intelligence"})
    node2 = GraphNode(id="ap:KWNode2", label="Label2", properties={"text": "machine learning"})
    await temp_repo.save_node(node1)
    await temp_repo.save_node(node2)

    # Note: search_nodes_by_keywords is currently a naive LIKE or basic matching.
    # In kuzu, we might just query JSON properties using CONTAINS.
    res = await temp_repo.search_nodes_by_keywords(["intelligence"], top_k=10)
    assert len(res) == 1
    assert res[0].id == "ap:KWNode1"


@pytest.mark.asyncio
async def test_get_subgraph(temp_repo: KuzuGraphRepository) -> None:
    from app.domain.models.graph import GraphEdge

    node1 = GraphNode(id="ap:Sub1", label="Node", properties={})
    node2 = GraphNode(id="ap:Sub2", label="Node", properties={})
    node3 = GraphNode(id="ap:Sub3", label="Node", properties={})
    await temp_repo.save_node(node1)
    await temp_repo.save_node(node2)
    await temp_repo.save_node(node3)

    await temp_repo.save_edge(GraphEdge(source_id="ap:Sub1", target_id="ap:Sub2", relation_type="REL", properties={}))
    await temp_repo.save_edge(GraphEdge(source_id="ap:Sub2", target_id="ap:Sub3", relation_type="REL", properties={}))

    # Get subgraph from Sub1 with max_hops=1 should include Sub1, Sub2, and 1 edge
    res1 = await temp_repo.get_subgraph(["ap:Sub1"], max_hops=1)
    assert len(res1.nodes) == 2
    assert len(res1.edges) == 1
    assert set(n.id for n in res1.nodes) == {"ap:Sub1", "ap:Sub2"}

    # Get subgraph from Sub1 with max_hops=2 should include Sub1, Sub2, Sub3 and 2 edges
    res2 = await temp_repo.get_subgraph(["ap:Sub1"], max_hops=2)
    assert len(res2.nodes) == 3
    assert len(res2.edges) == 2


@pytest.mark.asyncio
async def test_delete_document_graph(temp_repo: KuzuGraphRepository) -> None:
    # We must set sourceDocumentIds in properties to delete them
    node1 = GraphNode(id="ap:DocNode1", label="Node", properties={"sourceDocumentIds": ["doc1"]})
    node2 = GraphNode(id="ap:DocNode2", label="Node", properties={"sourceDocumentIds": ["doc1", "doc2"]})
    await temp_repo.save_node(node1)
    await temp_repo.save_node(node2)

    await temp_repo.delete_document_graph("doc1")

    # DocNode1 should be deleted (it only had doc1)
    assert await temp_repo.get_node("ap:DocNode1") is None

    # DocNode2 should still exist but without doc1
    retrieved = await temp_repo.get_node("ap:DocNode2")
    assert retrieved is not None
    assert "doc1" not in retrieved.properties.get("sourceDocumentIds", [])
