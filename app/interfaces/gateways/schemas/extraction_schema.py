from typing import Any, Dict, List, Literal

from pydantic import BaseModel, Field


class ExtractedNode(BaseModel):
    id: str = Field(..., pattern=r"^ap:[A-Za-z0-9_]+$")
    type: Literal[
        "ap:Procedure",
        "ap:Actor",
        "ap:Document",
        "ap:Condition",
        "ap:Organization",
        "ap:InputItem",
        "ap:LegalBasis",
        "ap:UnclassifiedConcept",
    ]
    label: str
    description: str | None = None
    properties: Dict[str, Any] = Field(default_factory=dict)


class KeywordsExtraction(BaseModel):
    keywords: List[str]


class AnchorValidation(BaseModel):
    is_valid: bool
    reason: str


class ExtractedRelationship(BaseModel):
    source: str
    target: str
    type: Literal[
        "ap:hasTargetActor",
        "ap:requiresDocument",
        "ap:producesDocument",
        "ap:hasPrerequisite",
        "ap:administeredBy",
        "ap:basedOnLaw",
        "ap:nextProcedure",
    ]
    properties: Dict[str, Any] = Field(default_factory=dict)


class LLMExtraction(BaseModel):
    nodes: List[ExtractedNode]
    relationships: List[ExtractedRelationship]
