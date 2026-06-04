# 05. Ontology Evolution Agent 詳細設計

## 1. AI Agent 判定処理 (`app/domain/services/evolution_agent.py`)

未分類概念ノードに対し、判定および進化提案を生成するコアロジックです。

```python
import json
import uuid
from pydantic import BaseModel
from typing import List, Literal, Optional, Dict, Any
from app.domain.services.llm_service import ILLMService # 汎用 LLM 呼び出し interface
from app.domain.services.graph_repository import IGraphRepository

class EvolutionProposal(BaseModel):
    id: str
    action: Literal['PROMOTE_CLASS', 'MAP_TO_PROPERTY', 'DISCARD']
    targetConcept: str
    proposedName: str
    proposedDescription: str
    suggestedProperties: List[Dict[str, str]]
    targetExistingClassOrProperty: Optional[str] = None
    rationale: str

class OntologyEvolutionAgent:
    def __init__(self, llm_service: ILLMService, graph_repository: IGraphRepository):
        self.llm_service = llm_service
        self.graph_repository = graph_repository

    async def generate_proposals(self) -> List[EvolutionProposal]:
        # 1. データベースから未分類概念を全取得
        unclassified_nodes = await self.graph_repository.find_nodes_by_type('ap:UnclassifiedConcept')
        if not unclassified_nodes:
            return []

        # 2. 定義済みのスキーマ情報を取得
        current_schema = await self.graph_repository.get_schema_definition()

        proposals = []
        for node in unclassified_nodes:
            proposal = await self._evaluate_concept(node, current_schema)
            proposals.append(proposal)

        return proposals

    async def _evaluate_concept(self, node: Any, current_schema: Any) -> EvolutionProposal:
        prompt = f"""
あなたはドメインオントロジーの設計を監督する「OntologyEvolutionAgent」です。
ドキュメント解析中に、既存の定義クラスに当てはまらない概念が見つかりました。この概念について一次判定（Triage）を行い、人間への提案を生成してください。

【評価対象の未知概念】
- 概念名: {node.properties.get('label')}
- 抽出された文脈: {node.properties.get('contextDescription')}
- 想定属性候補: {json.dumps(node.properties.get('suggestedProperties'))}

【現在の定義済みクラス一覧】
{json.dumps(current_schema.get('classes', []))}

【判定基準】
1. 表記揺れまたは部分一致する既存クラス・プロパティがあれば「MAP_TO_PROPERTY」を選択し、マッピング先を指定してください。
2. 既存クラスでは表現できない独自のエンティティは「PROMOTE_CLASS」を選択し、新規クラス名（CamelCase）、説明、属性構造を設計してください。
3. 手続きと関係のないノイズや、単純な値の抽出エラーであれば「DISCARD」を選択してください。

以下のJSON形式のみで回答してください:
{{
  "action": "PROMOTE_CLASS" | "MAP_TO_PROPERTY" | "DISCARD",
  "proposedName": "推奨されるクラス名/プロパティ名",
  "proposedDescription": "概念の説明",
  "suggestedProperties": [{{"name": "プロパティ名", "type": "string" | "number" | "boolean"}}],
  "targetExistingClassOrProperty": "MAP_TO_PROPERTYの場合のマッピング先ID",
  "rationale": "この判定に至った論理的根拠・推論プロセス（日本語）"
}}
"""
        # LLMを呼び出しJSONをパース
        response_text = await self.llm_service.chat_complete(prompt)
        parsed = json.loads(response_text)
        
        return EvolutionProposal(
            id=f"prop_{uuid.uuid4().hex[:8]}",
            action=parsed.get('action', 'DISCARD'),
            targetConcept=node.properties.get('label', ''),
            proposedName=parsed.get('proposedName', ''),
            proposedDescription=parsed.get('proposedDescription', ''),
            suggestedProperties=parsed.get('suggestedProperties', []),
            targetExistingClassOrProperty=parsed.get('targetExistingClassOrProperty'),
            rationale=parsed.get('rationale', '')
        )
```
