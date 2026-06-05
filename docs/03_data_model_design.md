# 03. Data Architecture & Global Governance (データモデル全体方針)
Version: 2.1.0

---

## 0. データアーキテクチャ・ガバナンス方針

本システムでは、マイクロサービス的・疎結合なアーキテクチャを維持するため、**各モジュール（境界づけられたコンテキスト）が自身のデータスキーマを所有する**ことを原則とします。

### 0.1 ドキュメント記載のルール
- **詳細なテーブル定義の分離**: 各機能が利用するデータベーステーブルのER図、および詳細なカラム定義は、**本ドキュメントには記載せず、各機能の詳細設計書（`docs/detail_design/xx_*.md`）に記載**します。
- **グローバルルールの定義**: 本ドキュメントでは、システム全体で守るべき命名規則、技術スタックの選定理由、および「どの機能がどのテーブルを所有しているか」のインデックスのみを定義します。

### 0.2 グローバルデータ規約
1. **主キー (Primary Key)**: 原則としてすべてのテーブルの主キーは `UUID (v4)` を採用する。
2. **日時データ (Timestamps)**: すべての日時データは UTC で保存し、テーブルには `created_at`, `updated_at` を標準で持たせる。
3. **論理削除と物理削除**: トランザクションデータ（実行履歴など）は物理削除を避け論理削除やアーカイブ戦略を推奨する。ただし、一時的な中間データ（抽出前テキストなど）はストレージ節約のため物理削除を許容する。
4. **非構造化データの扱い**: スキーマレスな動的パラメータやJSONペイロードは、PostgreSQL等の `JSONB` カラムを活用して保存する。

---

## 1. データベース技術スタックと使い分け

ontoNgnでは、用途に合わせて複数のデータストアを使い分けます。

1. **Relational Database (PostgreSQL / SQLite)**
   - **用途**: ワークフローの定義・実行履歴、ドキュメントのメタデータ、ユーザー承認待ちのタスクなど、トランザクション性の高い管理データ。
   - **特性**: `JSONB` を活用し、一部スキーマレスなJSONペイロードを保存可能とする。
2. **Graph Database (Kùzu / Neo4j)**
   - **用途**: 抽出されたオントロジー（ノードとエッジ）の保存、および GraphRAG によるサブグラフ検索。
3. **File System / Object Storage**
   - **用途**: アップロードされたPDF原本、抽出プロセスで生成された一時的な画像ファイル（PNG）、コンパイルされたOWLファイル等の保存。

---

## 2. モジュールごとのテーブル管轄インデックス (Ownership Map)

各モジュールが所有するリレーショナルデータベースのテーブル一覧です。詳細は各リンク先の詳細設計書を参照してください。

| 管轄モジュール | 詳細設計ドキュメント | 所有する主なテーブル | 役割 |
| :--- | :--- | :--- | :--- |
| **Workflow Orchestrator** | [01_workflow_orchestrator.md](detail_design/01_workflow_orchestrator.md) | `workflows`<br>`workflow_executions`<br>`node_executions` | DAG定義と実行トラッキング。Vue Flow互換のJSON等を扱う。 |
| **Document Management** | [12_document_management.md](detail_design/12_document_management.md) | `document_sources` | ドキュメントのアップロード履歴、ステータス、ファイルパスの管理。 |
| **Schema Evolution** | [08_schema_evolution_api.md](detail_design/08_schema_evolution_api.md) | `evolution_proposals` | 未分類概念に対するAIの提案と、ユーザーの承認（Pending）状態の管理。 |

---

## 3. オントロジーに関するデータモデル定義（GraphDB領域）

任意のドキュメントから汎用的な概念体系を構築するためのオントロジー構造設計です。初期のドメインモデルとして「行政手続き」を定義しています。

### 3.1 クラス定義 (Entities)
行政手続きを構成する主要な概念（ノード）の定義です。

| クラス名 (URIプレフィックス: `ap:`) | 説明 | 主要プロパティ |
| :--- | :--- | :--- |
| `ap:Procedure` | 行政手続きそのもの（申請、届出など）。 | `rdfs:label`, `ap:description`, `ap:leadTime` |
| `ap:Actor` | 手続きを行う対象者（申請者、代理人、扶養者など）。 | `rdfs:label`, `ap:eligibilityCriteria` |
| `ap:Document` | 提出が必要な添付書類、または結果として発行される証明書。 | `rdfs:label`, `ap:isForm` |
| `ap:Condition` | 手続きを申請するための前提条件や制限事項。 | `rdfs:label`, `ap:expression` |
| `ap:Organization` | 管轄する行政機関、担当部署、窓口。 | `rdfs:label`, `ap:contactAddress` |
| `ap:InputItem` | 申請書などの様式内に記入する必要がある具体的な項目。 | `rdfs:label`, `ap:dataType` |
| `ap:LegalBasis` | 手続きの根拠となる法律、条例、条項。 | `rdfs:label`, `ap:sectionNumber` |
| `ap:UnclassifiedConcept` | 既存のクラスに分類できない未知の重要概念。 | `rdfs:label`, `ap:contextDescription` |

### 3.2 プロパティ・関係性定義 (Relationships)

| プロパティ名 (URI) | 主語 (Domain) | 目的語 (Range) | 説明 |
| :--- | :--- | :--- | :--- |
| `ap:hasTargetActor` | `ap:Procedure` | `ap:Actor` | 手続きの対象者または申請を行うアクター。 |
| `ap:requiresDocument` | `ap:Procedure` | `ap:Document` | 手続きの申請時に提出が必要な添付書類。 |
| `ap:producesDocument` | `ap:Procedure` | `ap:Document` | 手続き完了時に交付される書類や結果通知書。 |
| `ap:hasPrerequisite` | `ap:Procedure` | `ap:Condition` | 手続きを開始するために満たす必要がある前提条件。 |
| `ap:administeredBy` | `ap:Procedure` | `ap:Organization` | 手続きを管轄または受付を行う組織・窓口。 |
| `ap:basedOnLaw` | `ap:Procedure` | `ap:LegalBasis` | 手続きの根拠となる法令や条例。 |
| `ap:nextProcedure` | `ap:Procedure` | `ap:Procedure` | 本手続きの完了後に続けて行う必要のある関連手続き。 |

### 3.3 クラス関係図 (Mermaid Diagram)

```mermaid
classDiagram
    direction LR
    class Procedure
    class Actor
    class Document
    class Condition
    class Organization
    class LegalBasis
    
    Procedure --> Actor : ap:hasTargetActor
    Procedure --> Document : ap:requiresDocument
    Procedure --> Document : ap:producesDocument
    Procedure --> Condition : ap:hasPrerequisite
    Procedure --> Organization : ap:administeredBy
    Procedure --> LegalBasis : ap:basedOnLaw
    Procedure --> Procedure : ap:nextProcedure
```

### 3.4 プログラミングレベルのモデル表現 (`app/domain/models/graph.py`)

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

## 4. ファイルの格納/管理ルール

システムが読み書きするファイルアセットの配置先ディレクトリとライフサイクルの定義です。

| パス | 種別 | ライフサイクル・管理ルール |
| :--- | :--- | :--- |
| `data/sources/` | ディレクトリ | アップロードされたオリジナルのドキュメント（PDF等）を格納。データベース削除時に対応ファイルもクリーンアップ。 |
| `temp/render/{doc_id}/` | 一時ディレクトリ | PDF等から抽出した高解像度PNG画像群を配置。パイプライン処理完了後に自動削除。 |
| `data/kuzu/` | ディレクトリ | グラフデータベース `Kùzu` を採用した場合の組み込みDB物理ストレージ。 |
| `docs/schema/ontology.ttl` | ファイル | W3C標準 OWL/TTL オントロジー定義ファイル。スキーマ進化承認時に自動更新。 |
| `app/interfaces/gateways/schemas/` | ディレクトリ | LLM抽出用の Pydantic / Zod バリデーションスキーマコード。進化承認時に自動再コンパイル。 |

---

## 5. オントロジー差分更新 (Clean Upsert) アルゴリズム

同一の `documentId` を持つドキュメントが再アップロードされた場合、当該ドキュメント由来のデータのみを更新・クリーンアップするトランザクション処理アルゴリズムです。

```
【差分置換アルゴリズム】
1. 該当 documentId を持つすべてのエッジ(関係性)を削除
2. 該当 documentId が関連付けられているノードの参照を更新
   - ノードの属性 `sourceDocumentIds` から当該 documentId を削除。
   - sourceDocumentIds が空になったノードを削除。
3. 新しいドキュメントを解析してオントロジーを抽出。
4. 抽出データに含まれる未分類概念の有無を判定：
   - なし：即座にステップ5の本保存処理を実行。
   - あり：一時保存（Pending）とし、AI Agentによる提案および開発者による承認完了後にステップ5を実行。
5. 新規抽出されたノードとエッジを本保存として登録（sourceDocumentIdsの更新）。
```

---

## 6. GraphRAG 連携仕様

### 6.1 LlamaIndex 用 JSON エクスポート
LlamaIndex や LangChain などの GraphRAG が読み込むための、標準的な JSON エクスポート形式です。

```json
{
  "nodes": [
    {
      "id": "ap:Procedure_JidouTeate_Shinsei",
      "type": "ap:Procedure",
      "properties": {
        "label": "児童手当の申請",
        "sourceDocumentIds": ["doc-01"]
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

### 6.2 W3C標準 Turtle (.ttl) 形式のエクスポート
セマンティック分析やトリプルストアへのインポート用です。

```turtle
@prefix ap: <http://example.org/ap/> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

ap:Procedure_JidouTeate_Shinsei rdf:type ap:Procedure ;
    rdfs:label "児童手当の申請" ;
    ap:hasTargetActor ap:Actor_Parent .
```
