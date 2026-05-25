import json

from fastapi import Depends
from openai import AsyncOpenAI

from app.core.config import Settings, get_settings
from app.domain.models.graph import ExtractionResult, GraphEdge, GraphNode
from app.domain.services.text_llm_service import ITextLLMService
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
        schema_str = json.dumps(LLMExtraction.model_json_schema(), ensure_ascii=False)
        response = await self.client.chat.completions.create(
            model=self.text_model_name,
            temperature=self.temperature,
            messages=[
                {
                    "role": "system",
                    "content": f"あなたは行政ドキュメントを読み取り、指定されたJSON構造で手続き・必要書類・アクターの関係性を抽出する専門家です。Markdownのコードブロック(```json 等)は使用せず、生のJSON文字列のみを出力してください。\n以下のJSON Schemaに必ず従ってください（typeのEnum値やidのプレフィックス 'ap:' などを厳守してください）:\n{schema_str}",  # noqa: E501
                },
                {
                    "role": "user",
                    "content": f"以下の構造化テキストから行政手続きのオントロジー関係を抽出してください。\n\nテキスト:\n{text_content}",  # noqa: E501
                },
            ],
        )

        response_text = response.choices[0].message.content or "{}"

        # モデルがマークダウンを含めた場合へのフォールバック処理
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        elif response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        print(f"DEBUG - Raw LLM Response: {response_text}")
        json_parsed = json.loads(response_text)

        # スキーマによるデータ検証
        validated_data = LLMExtraction.model_validate(json_parsed)

        nodes = [
            GraphNode(id=n.id, label=n.label, properties={"type": n.type, "description": n.description, **n.properties})
            for n in validated_data.nodes
        ]

        edges = [
            GraphEdge(source_id=r.source, target_id=r.target, relation_type=r.type, properties=r.properties)
            for r in validated_data.relationships
        ]

        return ExtractionResult(nodes=nodes, edges=edges)
