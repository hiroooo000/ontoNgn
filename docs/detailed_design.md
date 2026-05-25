# ontoNgn (Ontology Engine) 詳細設計書
Version: 2.0.0

---

## 1. データベースの抽象化と低依存設計

特定データベース（Neo4j, Apache AGE, Kùzu等）への依存を排除するため、ドメイン層に共通インターフェースを定義し、FastAPI の Dependency Injection システムにより動的にバインドします。

### 1.1 リポジトリインターフェース (`app/domain/services/graph_repository.py`)

```python
from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.models.graph import GraphNode, GraphEdge, ExtractionResult

class IGraphRepository(ABC):
    @abstractmethod
    async def save_node(self, node: GraphNode) -> None:
        """ノードを永続化（作成または更新）します。"""
        pass
        
    @abstractmethod
    async def save_edge(self, edge: GraphEdge) -> None:
        """エッジを永続化（作成または更新）します。"""
        pass
        
    @abstractmethod
    async def get_node(self, node_id: str) -> Optional[GraphNode]:
        """一意なID (URI) からノードを取得します。"""
        pass
        
    @abstractmethod
    async def query_neighbors(self, node_id: str) -> List[GraphEdge]:
        """対象ノードに隣接するエッジ群を取得します。"""
        pass
        
    @abstractmethod
    async def export_all(self) -> ExtractionResult:
        """全ノード・エッジの集合を取得します。"""
        pass

    @abstractmethod
    async def find_nodes_by_type(self, label_type: str) -> List[GraphNode]:
        """指定されたクラス・タイプ（例：ap:UnclassifiedConcept）の全ノードを取得します。"""
        pass

    @abstractmethod
    async def get_schema_definition(self) -> dict:
        """現在データベースに適用されているスキーマ定義メタデータを取得します。"""
        pass
```

### 1.2 依存性注入（DI）定義 (`app/core/dependencies.py`)

環境変数 `GRAPH_DB_TYPE` を用いて、実行時に有効にする具象リポジトリを決定します。

```python
from fastapi import Depends
from app.core.config import get_settings, Settings
from app.domain.services.graph_repository import IGraphRepository
from app.interfaces.gateways.neo4j_repository import Neo4jGraphRepository
from app.interfaces.gateways.age_repository import AgeGraphRepository
from app.interfaces.gateways.kuzu_repository import KuzuGraphRepository
from app.interfaces.gateways.rdf_repository import InMemoryRdfRepository

def get_graph_repository(settings: Settings = Depends(get_settings)) -> IGraphRepository:
    db_type = settings.graph_db_type.lower()
    
    if db_type == 'neo4j':
        return Neo4jGraphRepository(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password
        )
    elif db_type == 'apache_age':
        return AgeGraphRepository(dsn=settings.postgres_dsn)
    elif db_type == 'kuzu':
        return KuzuGraphRepository(db_path=settings.kuzu_db_path)
    else:
        # デフォルトはインメモリRDF（N3 / rdflib）
        return InMemoryRdfRepository(output_path=settings.rdf_output_path)
```

---

## 2. ドキュメントレンダラー詳細設計 (`app/interfaces/renderers/document_renderer.py`)

アップロードされたPDF、Word、Excelデータを、非同期で画像バッファ（PNG）へレンダリングするモジュールです。Word/Excel などの Office ファイルは、LibreOffice をヘッドレスモードで起動し、一時的に PDF へ変換した上で画像化します。

```python
import asyncio
from pdf2image import convert_from_bytes
import tempfile
import os
from typing import List

class DocumentRenderer:
    """PDF / DOCX / XLSX バッファを画像バッファ（PNG）にレンダリングする"""
    
    async def render_to_images(self, file_buffer: bytes, file_extension: str) -> List[bytes]:
        pdf_buffer = file_buffer

        # Word/Excel の場合は LibreOffice を介して PDF に事前変換
        if file_extension.lower() in ['.docx', '.xlsx']:
            pdf_buffer = await self._convert_to_pdf_via_libreoffice(file_buffer, file_extension)

        # PDF を各ページ PNG のバイナリデータに展開
        return await self._render_pdf_to_pngs(pdf_buffer)

    async def _convert_to_pdf_via_libreoffice(self, buffer: bytes, ext: str) -> bytes:
        temp_dir = os.path.join(os.getcwd(), 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        with tempfile.NamedTemporaryFile(dir=temp_dir, suffix=ext, delete=False) as temp_input:
            temp_input.write(buffer)
            temp_input_path = temp_input.name

        try:
            # LibreOffice ヘッドレスモードで PDF 変換を実行
            process = await asyncio.create_subprocess_shell(
                f'soffice --headless --convert-to pdf --outdir "{temp_dir}" "{temp_input_path}"',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            base_name = os.path.splitext(os.path.basename(temp_input_path))[0]
            temp_pdf_path = os.path.join(temp_dir, f"{base_name}.pdf")
            
            with open(temp_pdf_path, 'rb') as f:
                pdf_buffer = f.read()

            return pdf_buffer
        finally:
            # 一時ファイルの削除
            if os.path.exists(temp_input_path):
                os.remove(temp_input_path)
            if 'temp_pdf_path' in locals() and os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)

    async def _render_pdf_to_pngs(self, pdf_buffer: bytes) -> List[bytes]:
        # pdf2image を用いて PNG リストへレンダリング (並列処理のために executor を使うことを推奨)
        images = convert_from_bytes(pdf_buffer, dpi=200)
        
        buffers = []
        for img in images:
            import io
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            buffers.append(img_byte_arr.getvalue())
            
        return buffers
```

---

## 3. Visionテキスト抽出・LLMオントロジー生成

### 3.1 抽象サービス定義

#### Vision サービス (`app/domain/services/vision_service.py`)
```python
from abc import ABC, abstractmethod
from typing import List

class IVisionService(ABC):
    @abstractmethod
    async def extract_text(self, image_buffers: List[bytes]) -> str:
        """画像群からレイアウト情報を維持した構造化テキストを抽出"""
        pass
```

#### Text LLM サービス (`app/domain/services/text_llm_service.py`)
```python
from abc import ABC, abstractmethod
from app.domain.models.graph import ExtractionResult

class ITextLLMService(ABC):
    @abstractmethod
    async def generate_ontology(self, text_content: str) -> ExtractionResult:
        """構造化テキストからオントロジーデータを抽出"""
        pass
```

### 3.2 バリデーションスキーマ定義 (`app/interfaces/gateways/schemas/extraction_schema.py`)

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

### 3.3 LMStudio 連携ゲートウェイ (`app/interfaces/gateways/lmstudio_gateway.py`)

```python
import base64
import json
from openai import AsyncOpenAI
from typing import List
from fastapi import Depends
from app.core.config import get_settings, Settings
from app.domain.services.vision_service import IVisionService
from app.domain.services.text_llm_service import ITextLLMService
from app.domain.models.graph import ExtractionResult, GraphNode, GraphEdge
from app.interfaces.gateways.schemas.extraction_schema import LLMExtraction

class LMStudioGateway(IVisionService, ITextLLMService):
    def __init__(self, settings: Settings = Depends(get_settings)):
        self.client = AsyncOpenAI(
            base_url=settings.llm_api_base_url,
            api_key=settings.llm_api_key or "lm-studio",
        )
        self.vision_model_name = settings.vision_model_name
        self.text_model_name = settings.text_model_name
        self.temperature = settings.llm_temperature

    async def extract_text(self, image_buffers: List[bytes]) -> str:
        content_parts = [
            {
                "type": "text",
                "text": "提供された画像に含まれる文書の構造（見出し、表、段落など）を維持し、詳細なMarkdown形式のテキストとして抽出してください。"
            }
        ]
        
        for buf in image_buffers:
            base64_image = base64.b64encode(buf).decode('utf-8')
            content_parts.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{base64_image}"
                }
            })

        response = await self.client.chat.completions.create(
            model=self.vision_model_name,
            temperature=0.0,
            messages=[{"role": "user", "content": content_parts}]
        )
        return response.choices[0].message.content or ""

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

---

## 4. スキーマ進化AIエージェント設計

### 4.1 AI Agent 判定処理 (`app/domain/services/evolution_agent.py`)

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

### 4.2 スキーマコンパイラ (`app/domain/services/schema_compiler.py`)

人間が承認した際に、Pydantic validator コードおよび OWL 定義ファイルを動的書き換えするモジュールです。

```python
import os
import re

class SchemaCompiler:
    def __init__(self):
        self.schema_file_path = os.path.join(
            os.path.dirname(__file__), 
            '../../interfaces/gateways/schemas/extraction_schema.py'
        )

    async def compile_pydantic_schema(self, new_class: dict) -> None:
        """LLM抽出検証用の Pydantic Schema ファイルを動的に書き換えます。"""
        with open(self.schema_file_path, 'r', encoding='utf-8') as f:
            schema_code = f.read()

        # Literal[] のマッチと追加
        enum_search_regex = r"type:\s*Literal\[\s*([^\]]+?)\s*\]"
        match = re.search(enum_search_regex, schema_code)
        
        if match:
            current_enums = [s.strip().strip("'").strip('"') for s in match.group(1).split(',')]
            class_name = f"ap:{new_class['name']}"
            if class_name not in current_enums:
                current_enums.append(class_name)
                new_enum_content = ",\n        ".join(f"'{e}'" for e in current_enums)
                
                schema_code = re.sub(
                    enum_search_regex,
                    f"type: Literal[\n        {new_enum_content}\n    ]",
                    schema_code
                )

        with open(self.schema_file_path, 'w', encoding='utf-8') as f:
            f.write(schema_code)

    async def compile_owl_ontology(self, new_class: dict) -> None:
        """W3C標準オントロジー定義ファイル (.ttl) に新規クラス記述を追記します。"""
        owl_path = os.path.join(os.getcwd(), 'docs/schema/ontology.ttl')
        ttl_fragment = f"""
###  http://example.org/ap/{new_class['name']}
ap:{new_class['name']} rdf:type owl:Class ;
       rdfs:subClassOf ap:DomainEntity ;
       rdfs:label "{new_class['name']}"@ja ;
       rdfs:comment "{new_class['description']}"@ja .
"""
        with open(owl_path, 'a', encoding='utf-8') as f:
            f.write(ttl_fragment)
```

---

## 5. ドキュメント収集（Ingestion）エンジンの処理詳細

多様な経路からのインプットを処理し、解析の自動トリガーを行うバックグラウンドタスク処理です。

### 5.1 手動アップロード (`UploadHandler`)
- **処理内容**: Console UI よりファイルバッファを受け取ります。ファイルデータの SHA-256 ハッシュを計算し、`document_sources` テーブルに対してハッシュ検索を実行。
- **重複判定**: ハッシュが一致する既存レコードがあり、且つステータスが `completed` の場合は処理をスキップ。未登録の場合は、`data/sources/` にファイルを保存してステータス `pending` で登録し、Orchestrator を非同期起動します。

### 5.2 ローカルパススキャナ (`LocalPathScanner`)
- **処理内容**: 設定されたフォルダ（例：`/data/watch/`）を定期スキャン（APScheduler や `watchdog` を利用）。
- **更新検知**: ファイルの追加、または既存ファイルの最終更新日時の変化を検出。新旧のメタデータを比較し、変更があれば `document_sources` レコードを作成・更新の上、非同期でパイプラインを起動します。

### 5.3 URL自動収集タスク (`UrlDownloader`)
- **処理内容**: 設定された外部リソースのURL（例：行政ポータルのPDFリンク）へ、定期的に HTTP `GET` または `HEAD` リクエストを発行。
- **更新検知**: `ETag` や `Last-Modified` レスポンスヘッダの値がローカル保存情報と異なる場合、ファイルを再ダウンロード。ハッシュ変更を確認できた場合、`document_sources` レコードを更新し、パイプラインを再実行します。
