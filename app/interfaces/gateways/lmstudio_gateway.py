import json

from fastapi import Depends
from openai import AsyncOpenAI

from app.core.config import Settings, get_settings
from app.domain.models.graph import ExtractionResult, GraphEdge, GraphNode
from app.domain.services.text_llm_service import ITextLLMService
from app.interfaces.gateways.schemas.extraction_schema import AnchorValidation, KeywordsExtraction, LLMExtraction


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

    async def extract_anchor_keywords(self, text_content: str) -> list[str]:
        schema_str = json.dumps(KeywordsExtraction.model_json_schema(), ensure_ascii=False)
        response = await self.client.chat.completions.create(
            model=self.text_model_name,
            temperature=0.0,
            messages=[
                {
                    "role": "system",
                    "content": f"あなたは行政ドキュメントのテキストから、既存知識グラフとの照合に用いる中心概念（アンカーとなる手続き名や対象者など）を3〜5個抽出する専門家です。Markdownのコードブロック(```json 等)は使用せず、生のJSON文字列のみを出力してください。\n以下のJSON Schemaに従ってください:\n{schema_str}",  # noqa: E501
                },
                {
                    "role": "user",
                    "content": f"以下のテキストから中心概念を抽出してください。\n\nテキスト:\n{text_content}",
                },
            ],
        )
        response_text = response.choices[0].message.content or "{}"

        # フォールバック処理
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        elif response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        print(f"DEBUG - KeywordsExtraction Response: {response_text}")
        json_parsed = json.loads(response_text)
        validated_data = KeywordsExtraction.model_validate(json_parsed)
        return validated_data.keywords

    async def validate_anchor(self, text_content: str, candidate_node: GraphNode) -> bool:
        schema_str = json.dumps(AnchorValidation.model_json_schema(), ensure_ascii=False)
        response = await self.client.chat.completions.create(
            model=self.text_model_name,
            temperature=0.0,
            messages=[
                {
                    "role": "system",
                    "content": f"あなたは新規のドキュメントテキストと、既存の知識グラフ上のノード（候補）を比較し、両者が実質的に同一または密接に関連する概念を指しているかを判定する専門家です。Markdownのコードブロックは使用せず、生のJSON文字列のみを出力してください。\n以下のJSON Schemaに従ってください:\n{schema_str}",  # noqa: E501
                },
                {
                    "role": "user",
                    "content": f"以下のテキストと既存ノード候補を比較し、関連性を判定してください。\n\n【テキスト】\n{text_content}\n\n【既存ノード候補】\nID: {candidate_node.id}\nLabel: {candidate_node.label}\nDescription: {candidate_node.properties.get('description', '')}\nProperties: {json.dumps(candidate_node.properties, ensure_ascii=False)}",  # noqa: E501
                },
            ],
        )
        response_text = response.choices[0].message.content or "{}"

        # フォールバック処理
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        elif response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        print(f"DEBUG - AnchorValidation Response: {response_text}")
        json_parsed = json.loads(response_text)
        validated_data = AnchorValidation.model_validate(json_parsed)
        return validated_data.is_valid

    async def generate_links(self, new_graph: ExtractionResult, context_subgraph: ExtractionResult) -> ExtractionResult:
        schema_str = json.dumps(LLMExtraction.model_json_schema(), ensure_ascii=False)
        new_graph_json = new_graph.model_dump_json()
        context_subgraph_json = context_subgraph.model_dump_json()

        response = await self.client.chat.completions.create(
            model=self.text_model_name,
            temperature=self.temperature,
            messages=[
                {
                    "role": "system",
                    "content": f"あなたは2つの知識グラフ（新規オントロジーと既存サブグラフ）を分析し、それらを統合するための新しいエッジ（関係性）や、新規ノードを抽出する専門家です。既存サブグラフの文脈を考慮し、新規グラフと既存グラフを繋ぐ新しい関係性を見つけてください。Markdownのコードブロックは使用せず、生のJSON文字列のみを出力してください。\n以下のJSON Schemaに従ってください:\n{schema_str}",  # noqa: E501
                },
                {
                    "role": "user",
                    "content": f"以下の2つのグラフ情報を統合推論し、新規抽出されたオントロジーと、追加すべきエッジ（既存ノードとの繋がりを含む）を出力してください。\n\n【新規抽出されたオントロジー】\n{new_graph_json}\n\n【既存の周辺サブグラフ（コンテキスト）】\n{context_subgraph_json}",  # noqa: E501
                },
            ],
        )
        response_text = response.choices[0].message.content or "{}"

        # フォールバック処理
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        elif response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        print(f"DEBUG - GenerateLinks Response: {response_text}")
        json_parsed = json.loads(response_text)
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
