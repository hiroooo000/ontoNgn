from app.domain.models.graph import ExtractionResult, GraphEdge, GraphNode


def test_graph_node_creation() -> None:
    node = GraphNode(id="ap:Test", label="Test Node", properties={"type": "ap:Test"})
    assert node.id == "ap:Test"
    assert node.label == "Test Node"
    assert node.properties["type"] == "ap:Test"


def test_graph_edge_creation() -> None:
    edge = GraphEdge(
        source_id="ap:Node1", target_id="ap:Node2", relation_type="ap:hasRelation", properties={"weight": 1}
    )
    assert edge.source_id == "ap:Node1"
    assert edge.target_id == "ap:Node2"
    assert edge.relation_type == "ap:hasRelation"
    assert edge.properties["weight"] == 1


def test_extraction_result_creation() -> None:
    node = GraphNode(id="ap:Test", label="Test Node", properties={})
    edge = GraphEdge(source_id="ap:Node1", target_id="ap:Node2", relation_type="ap:hasRelation", properties={})
    result = ExtractionResult(nodes=[node], edges=[edge])
    assert len(result.nodes) == 1
    assert len(result.edges) == 1
    assert result.nodes[0] == node
    assert result.edges[0] == edge
