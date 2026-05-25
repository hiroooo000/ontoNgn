import pytest
from pydantic import ValidationError

from app.interfaces.gateways.schemas.extraction_schema import ExtractedNode, ExtractedRelationship, LLMExtraction


def test_extracted_node_valid() -> None:
    node = ExtractedNode(id="ap:ValidNode", type="ap:Procedure", label="Valid Label")
    assert node.id == "ap:ValidNode"
    assert node.type == "ap:Procedure"


def test_extracted_node_invalid_id() -> None:
    with pytest.raises(ValidationError):
        ExtractedNode(id="invalid_id", type="ap:Procedure", label="Valid Label")


def test_extracted_node_invalid_type() -> None:
    with pytest.raises(ValidationError):
        ExtractedNode(id="ap:ValidNode", type="ap:InvalidType", label="Valid Label")  # type: ignore


def test_extracted_relationship_valid() -> None:
    rel = ExtractedRelationship(source="ap:Node1", target="ap:Node2", type="ap:requiresDocument")
    assert rel.source == "ap:Node1"
    assert rel.type == "ap:requiresDocument"


def test_llm_extraction_valid() -> None:
    data = {
        "nodes": [{"id": "ap:Node1", "type": "ap:Procedure", "label": "Procedure 1"}],
        "relationships": [{"source": "ap:Node1", "target": "ap:Node2", "type": "ap:requiresDocument"}],
    }
    extraction = LLMExtraction.model_validate(data)
    assert len(extraction.nodes) == 1
    assert len(extraction.relationships) == 1
