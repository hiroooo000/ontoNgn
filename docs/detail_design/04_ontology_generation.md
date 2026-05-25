# 04. Ontology Generation API 詳細設計

## 1. 抽象サービス定義 (`app/domain/services/text_llm_service.py`)

```python
from abc import ABC, abstractmethod
from app.domain.models.graph import ExtractionResult

class ITextLLMService(ABC):
    @abstractmethod
    async def generate_ontology(self, text_content: str) -> ExtractionResult:
        """構造化テキストからオントロジーデータを抽出"""
        pass
```

## 2. バリデーションスキーマ定義 (`app/interfaces/gateways/schemas/extraction_schema.py`)

LLM の Structured Outputs (JSON モード) から取得した値を Pydantic で厳密に検証するための定義です。

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal

class ExtractedNode(BaseModel):
    id: str = Field(..., pattern=r"^ap:[A-Za-z0-9_]+$")
    type: Literal[
        'ap:Procedure',
        'ap:Actor',
        'ap:Document',
        'ap:Condition',
        'ap:Organization',
        'ap:InputItem',
        'ap:LegalBasis',
        'ap:UnclassifiedConcept' # 未知概念は一時的にこのタイプで退避
    ]
    label: str
    description: str | None = None
    properties: Dict[str, Any] = Field(default_factory=dict)

class ExtractedRelationship(BaseModel):
    source: str
    target: str
    type: Literal[
        'ap:hasTargetActor',
        'ap:requiresDocument',
        'ap:producesDocument',
        'ap:hasPrerequisite',
        'ap:administeredBy',
        'ap:basedOnLaw',
        'ap:nextProcedure'
    ]
    properties: Dict[str, Any] = Field(default_factory=dict)

class LLMExtraction(BaseModel):
    nodes: List[ExtractedNode]
    relationships: List[ExtractedRelationship]
```

## 3. LMStudio 連携ゲートウェイ (Ontology抽出実装)

`app/interfaces/gateways/lmstudio_gateway.py` のOntology生成関連の実装を抜粋します。

```python
import json
from openai import AsyncOpenAI
from fastapi import Depends
from app.core.config import get_settings, Settings
from app.domain.services.text_llm_service import ITextLLMService
from app.domain.models.graph import ExtractionResult, GraphNode, GraphEdge
from app.interfaces.gateways.schemas.extraction_schema import LLMExtraction

class LMStudioGateway(ITextLLMService):
    def __init__(self, settings: Settings = Depends(get_settings)):
        self.client = AsyncOpenAI(
            base_url=settings.llm_api_base_url,
            api_key=settings.llm_api_key or "lm-studio",
        )
        self.text_model_name = settings.text_model_name
        self.temperature = settings.llm_temperature

    async def generate_ontology(self, text_content: str) -> ExtractionResult:
        response = await self.client.chat.completions.create(
            model=self.text_model_name,
            temperature=self.temperature,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "あなたは行政ドキュメントを読み取り、指定されたJSON構造で手続き・必要書類・アクターの関係性を抽出する専門家です。指定のスキーマ以外のプロパティは含めないでください。"
                },
                {
                    "role": "user",
                    "content": f"以下の構造化テキストから行政手続きのオントロジー関係を抽出してください。\n\nテキスト:\n{text_content}"
                }
            ]
        )

        response_text = response.choices[0].message.content or "{}"
        json_parsed = json.loads(response_text)

        # スキーマによるデータ検証
        validated_data = LLMExtraction.model_validate(json_parsed)

        nodes = [
            GraphNode(
                id=n.id,
                label=n.label,
                properties={"type": n.type, "description": n.description, **n.properties}
            ) for n in validated_data.nodes
        ]

        edges = [
            GraphEdge(
                source_id=r.source,
                target_id=r.target,
                relation_type=r.type,
                properties=r.properties
            ) for r in validated_data.relationships
        ]

        return ExtractionResult(nodes=nodes, edges=edges)
```
