from typing import Any, Dict, List

from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    id: str
    label: str
    properties: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    source_id: str
    target_id: str
    relation_type: str
    properties: Dict[str, Any] = Field(default_factory=dict)


class ExtractionResult(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
