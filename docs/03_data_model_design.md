# ontoNgn (Ontology Engine) データモデル定義書
Version: 2.0.0

---

## 1. RDBに関するデータモデル定義

解析対象となるドキュメントのソース情報、処理ステータス、およびコンテンツハッシュなどを管理するため、システムは以下のリレーショナル（RDB）テーブルまたはスキーマを使用します。

### 1.1 ドキュメント管理モデル (`app/domain/models/document_source.py`)

ドキュメントのメタデータを定義する Pydantic モデルです。実体はメタデータ用 RDB (PostgreSQL 等) の `document_sources` テーブルに格納されます。

```python
from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime

SourceType = Literal['upload', 'local_path', 'url']
ProcessingStatus = Literal['pending', 'processing', 'completed', 'failed']

class DocumentSource(BaseModel):
    id: str                 # ユニークID (ユーザー指定またはファイルコンテンツのハッシュ値)
    file_name: str          # ファイル名
    source_type: SourceType # 取り込みソースの種類
    source_path: Optional[str] = None # ローカルファイルパスまたはダウンロード元のURL
    status: ProcessingStatus # パイプライン処理ステータス
    error_message: Optional[str] = None # 処理失敗時のエラーメッセージ
    hash: str               # 変更検知用のコンテンツハッシュ (SHA-256)
    created_at: datetime
    updated_at: datetime
```

### 1.2 `document_sources` テーブル物理設計 (想定)

| カラム名 | 型 | 制約 | 説明 |
| :--- | :--- | :--- | :--- |
| `id` | VARCHAR(255) | PRIMARY KEY | ドキュメントの一意な識別子。 |
| `file_name` | VARCHAR(255) | NOT NULL | アップロードされたファイル名。 |
| `source_type` | VARCHAR(50) | NOT NULL | `upload`, `local_path`, `url` のいずれか。 |
| `source_path` | TEXT | NULL | ファイルの保存先パスまたはURL。 |
| `status` | VARCHAR(50) | NOT NULL | 処理状況。初期値 `pending`。 |
| `error_message` | TEXT | NULL | 処理エラー発生時の詳細ログ。 |
| `hash` | VARCHAR(64) | NOT NULL | 重複・変更検知用ハッシュ。 |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 作成日時。 |
| `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 更新日時。 |

### 1.3 ドキュメントデータベース (JSONB) の活用
Vision Modelが抽出した中間の構造化テキスト（Markdown）や、OCRブロックの座標情報など、非構造化データは PostgreSQL の **JSONB** 型カラムに格納し、GINインデックスを付与して高速に検索・パース可能にします。

---

## 2. オントロジーに関するデータモデル定義

任意のドキュメントから汎用的な概念体系を構築するためのオントロジー構造設計です。初期のドメインモデルとして「行政手続き」を定義しています。

### 2.1 クラス定義 (Entities)

行政手続きを構成する主要な概念（ノード）の定義です。

| クラス名 (URIプレフィックス: `ap:`) | 説明 | 主要プロパティ |
| :--- | :--- | :--- |
| `ap:Procedure` | 行政手続きそのもの（申請、届出など）。 | `rdfs:label`, `ap:description`, `ap:leadTime` (処理期間) |
| `ap:Actor` | 手続きを行う対象者（申請者、代理人、扶養者など）。 | `rdfs:label`, `ap:eligibilityCriteria` (資格基準) |
| `ap:Document` | 提出が必要な添付書類、または手続きの結果として発行される証明書。 | `rdfs:label`, `ap:isForm` (様式有無の真偽値) |
| `ap:Condition` | 手続きを申請するための前提条件や制限事項。 | `rdfs:label`, `ap:expression` (年齢や所得等の条件式) |
| `ap:Organization` | 管轄する行政機関、担当部署、窓口。 | `rdfs:label`, `ap:contactAddress`, `ap:businessHours` |
| `ap:InputItem` | 申請書などの様式内に記入する必要がある具体的な項目。 | `rdfs:label`, `ap:dataType` (文字列、数値、日付など) |
| `ap:LegalBasis` | 手続きの根拠となる法律、条例、条項。 | `rdfs:label`, `ap:sectionNumber` (条項番号) |
| `ap:UnclassifiedConcept` | 既存のクラスに分類できない未知の重要概念（スキーマ進化の候補）。 | `rdfs:label`, `ap:contextDescription`, `ap:suggestedProperties` |

### 2.2 プロパティ・関係性定義 (Relationships)

各エンティティ間の意味的な関係（エッジ）の定義です。

| プロパティ名 (URI) | 主語 (Domain) | 目的語 (Range) | 説明 |
| :--- | :--- | :--- | :--- |
| `ap:hasTargetActor` | `ap:Procedure` | `ap:Actor` | 手続きの対象者または申請を行うアクターを示します。 |
| `ap:requiresDocument` | `ap:Procedure` | `ap:Document` | 手続きの申請時に提出が必要な添付書類を示します。 |
| `ap:producesDocument` | `ap:Procedure` | `ap:Document` | 手続き完了時に交付される書類や結果通知書を示します。 |
| `ap:hasPrerequisite` | `ap:Procedure` | `ap:Condition` | 手続きを開始するために満たす必要がある前提条件を示します。 |
| `ap:administeredBy` | `ap:Procedure` | `ap:Organization` | 手続きを管轄または受付を行う組織・窓口を示します。 |
| `ap:basedOnLaw` | `ap:Procedure` | `ap:LegalBasis` | 手続きの根拠となる法令や条例を示します。 |
| `ap:nextProcedure` | `ap:Procedure` | `ap:Procedure` | 本手続きの完了後に続けて行う必要のある関連手続きを示します。 |

### 2.3 クラス関係図 (Mermaid Diagram)

```mermaid
classDiagram
    direction LR
    class Procedure {
        +String label
        +String description
        +String leadTime
    }
    class Actor {
        +String label
        +String eligibilityCriteria
    }
    class Document {
        +String label
        +Boolean isForm
    }
    class Condition {
        +String label
        +String expression
    }
    class Organization {
        +String label
        +String contactAddress
        +String businessHours
    }
    class LegalBasis {
        +String label
        +String sectionNumber
    }
    
    Procedure --> Actor : ap:hasTargetActor
    Procedure --> Document : ap:requiresDocument
    Procedure --> Document : ap:producesDocument
    Procedure --> Condition : ap:hasPrerequisite
    Procedure --> Organization : ap:administeredBy
    Procedure --> LegalBasis : ap:basedOnLaw
    Procedure --> Procedure : ap:nextProcedure
```

### 2.4 プログラミングレベルのモデル表現 (`app/domain/models/graph.py`)

グラフDBおよびAPIでやり取りする論理グラフデータの Pydantic モデルです。

```python
from pydantic import BaseModel, Field
from typing import Dict, Any, List

class GraphNode(BaseModel):
    id: str = Field(..., description="URI表現 (例: 'ap:Procedure_JidouTeate')")
    label: str = Field(..., description="クラス名 (例: 'ap:Procedure')")
    properties: Dict[str, Any] = Field(default_factory=dict)

class GraphEdge(BaseModel):
    source_id: str = Field(..., description="接続元ノードのID (URI)")
    target_id: str = Field(..., description="接続先ノードのID (URI)")
    relation_type: str = Field(..., description="関係性の型 (例: 'ap:requiresDocument')")
    properties: Dict[str, Any] = Field(default_factory=dict)

class ExtractionResult(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
```

---

## 3. ファイルの格納/管理ルール

システムが読み書きするファイルアセットの配置先ディレクトリとライフサイクルの定義です。

| パス | 種別 | ライフサイクル・管理ルール |
| :--- | :--- | :--- |
| `data/sources/` | ディレクトリ | アップロードされたオリジナルのドキュメント（PDF, DOCX等）を格納。データベース削除時に対応ファイルもクリーンアップ。 |
| `temp/render/{doc_id}/` | 一時ディレクトリ | PDF等から抽出した高解像度PNG画像群を配置。パイプライン処理完了後（Vision処理終了時）にディレクトリごと自動削除。 |
| `data/kuzu/` | ディレクトリ | グラフデータベース `Kùzu` を採用した場合の組み込みDB物理ストレージ。 |
| `docs/schema/ontology.ttl` | ファイル | W3C標準 OWL/TTL オントロジー定義ファイル。スキーマ進化承認時に自動更新。 |
| `app/interfaces/gateways/schemas/` | ディレクトリ | LLM抽出用の Pydantic / Zod バリデーションスキーマコード。進化承認時に自動再コンパイル。 |

---

## 4. オントロジー差分更新 (Clean Upsert) アルゴリズム

同一の `documentId` を持つドキュメントが再アップロードされた（または更新検知された）場合、他のドキュメントに基づくデータを破壊せずに、当該ドキュメント由来のデータのみを更新・クリーンアップするトランザクション処理アルゴリズムです。

```
【差分置換アルゴリズム】
1. 該当 documentId を持つすべてのエッジ(関係性)を削除
   (※関係性は特定の文脈に依存するため、ドキュメントの更新時に全削除して問題ない)
2. 該当 documentId が関連付けられているノードの参照を更新
   - ノードは複数のドキュメント間で共有（例：「申請者：保護者」）される可能性があるため、
     ノードの属性 `sourceDocumentIds`（配列）から当該 documentId を削除。
   - sourceDocumentIds が空になった（どのドキュメントからも参照されていない）ノードを削除。
3. 新しいドキュメントを解析してオントロジーを抽出。
4. 抽出データに含まれる未分類概念の有無を判定：
   - 未分類概念がない場合：即座にステップ5の本保存処理を実行。
   - 未分類概念がある場合：抽出データを一時保存（Pending）とし、AI Agentによる提案および開発者による承認・マッピング（スキーマ更新）完了後にステップ5を実行。
5. 新規抽出されたノードとエッジを本保存として登録：
   - 既存ノードがある場合：そのノードの `sourceDocumentIds` に当該 documentId を追加。
   - 新規ノードの場合：`sourceDocumentIds` = [documentId] で作成。
   - 新規エッジの場合：`properties.sourceDocumentId` = documentId で作成。
```

---

## 5. GraphRAG 連携仕様

### 5.1 LlamaIndex 用 JSON エクスポート
LlamaIndex や LangChain などの GraphRAG が読み込むための、標準的な JSON エクスポート形式です。

```json
{
  "nodes": [
    {
      "id": "ap:Procedure_JidouTeate_Shinsei",
      "type": "ap:Procedure",
      "properties": {
        "label": "児童手当の申請",
        "description": "児童手当の受給資格を得るための申請手続きです。",
        "sourceDocumentIds": ["doc-01"]
      }
    },
    {
      "id": "ap:Actor_Parent",
      "type": "ap:Actor",
      "properties": {
        "label": "児童の養育者（父母など）",
        "sourceDocumentIds": ["doc-01", "doc-02"]
      }
    }
  ],
  "relationships": [
    {
      "source": "ap:Procedure_JidouTeate_Shinsei",
      "target": "ap:Actor_Parent",
      "type": "ap:hasTargetActor",
      "properties": {
        "sourceDocumentId": "doc-01"
      }
    }
  ]
}
```

### 5.2 W3C標準 Turtle (.ttl) 形式のエクスポート
セマンティック分析やトリプルストアへのインポート用として、`rdflib` ライブラリを使用してシリアライズされる Turtle 形式です。

```turtle
@prefix ap: <http://example.org/ap/> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

ap:Procedure_JidouTeate_Shinsei rdf:type ap:Procedure ;
    rdfs:label "児童手当の申請" ;
    ap:description "児童手当の受給資格を得るための申請手続きです。" ;
    ap:hasTargetActor ap:Actor_Parent .

ap:Actor_Parent rdf:type ap:Actor ;
    rdfs:label "児童の養育者（父母など）" .
```
