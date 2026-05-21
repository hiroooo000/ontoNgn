# ontoNgn データモデル設計書 (Ontology Model Design)
Version: 1.0.0

---

## 1. 概要
本ドキュメントは、汎用オントロジー生成・提供エンジン **「ontoNgn」** が各種ドキュメントから自動的・自律的に抽出・管理する知識グラフ（オントロジー）のデータモデル設計です。
本システムは初期ドメイン（テンプレート）として「行政手続き」を対象としたクラス設計を採用していますが、データモデル自体は完全に抽象化されており、他のドキュメントドメイン（開発マニュアル、企業規定、規約など）にも柔軟に適用・拡張できる設計となっています。
本モデルは、マルチモーダルLLMによってドキュメントから抽出され、各種グラフデータベース（Neo4j, PostgreSQL/Apache AGE, Kùzu等）やRDFストアで共通して扱われる意味定義の基盤となります。

---

## 2. ネームスペースと接頭辞 (Namespaces)

本オントロジーでは、以下の接頭辞（Prefix）を使用します。

- `ap:` (Administrative Procedure): `http://example.org/ap/` (本システム独自の手続き語彙)
- `rdf:`: `http://www.w3.org/1999/02/22-rdf-syntax-ns#` (基本的なリソース記述)
- `rdfs:`: `http://www.w3.org/2000/01/rdf-schema#` (クラス・ラベルの定義)
- `owl:`: `http://www.w3.org/2002/07/owl#` (オントロジーの構造定義)

---

## 3. クラス定義 (Entities)

行政手続きを構成する主要な要素（ノード）の定義です。

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

---

## 4. プロパティ・関係性定義 (Relationships)

各エンティティ間の関係（エッジ）の定義です。

| プロパティ名 (URI) | 主語 (Domain) | 目的語 (Range) | 説明 |
| :--- | :--- | :--- | :--- |
| `ap:hasTargetActor` | `ap:Procedure` | `ap:Actor` | 手続きの対象者または申請を行うアクターを示します。 |
| `ap:requiresDocument` | `ap:Procedure` | `ap:Document` | 手続きの申請時に提出が必要な添付書類を示します。 |
| `ap:producesDocument` | `ap:Procedure` | `ap:Document` | 手続き完了時に交付される書類や結果通知書を示します。 |
| `ap:hasPrerequisite` | `ap:Procedure` | `ap:Condition` | 手続きを開始するために満たす必要がある前提条件を示します。 |
| `ap:administeredBy` | `ap:Procedure` | `ap:Organization` | 手続きを管轄または受付を行う組織・窓口を示します。 |
| `ap:basedOnLaw` | `ap:Procedure` | `ap:LegalBasis` | 手続きの根拠となる法令や条例を示します。 |
| `ap:nextProcedure` | `ap:Procedure` | `ap:Procedure` | 本手続きの完了後に続けて行う必要のある関連手続きを示します。 |

---

## 5. クラス関係図 (Mermaid Diagram)

各クラス間の関係性をビジュアル化した図です。

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

---

## 6. GraphRAG用途におけるセマンティック設計

本データモデルは、GraphRAGが知識グラフ（Knowledge Graph）としてインポート・解釈しやすいよう以下の工夫を行っています。

1. **参照の標準化**:
   - すべてのエンティティは `ap:Procedure_JidouTeate_Shinsei` のように一意なIDを持ち、ドキュメントを跨いで同じ概念（例：同じ `ap:Actor_Parent`）が再利用されることで、知識の網の目が自動形成されます。
2. **メタデータの追跡**:
   - 各エンティティおよび関係性には `sourceDocumentIds` や `sourceDocumentId` などのメタデータ属性を付与し、「どのドキュメントの記述に基づいているか」を常にトレースできるようにしています。

---

## 7. スキーマの進化（Schema Evolution）への対応

対象ドキュメントは多岐にわたり、更新によって新しい種類の概念、属性、役割等の「未知の概念」が出現します。これに動的に追従し、オントロジーの品質をコントロールするための設計です。

### 7.1 AI駆動型スキーマ拡張ライフサイクル

本システムでは、未知の概念の登録を単なる「手動の管理表」とせず、**AI Agent（`OntologyEvolutionAgent`）**が一時判定と具体的なスキーマ定義の提案を自律的に行い、人間は提案された定義（クラス名、型、属性値）の「確認と承認」のみを行うAIエージェントアプリケーション（engine + console）として設計します。

1. **未知概念の検出 (Discovery)**:
   - ドキュメント解析時、LLMが既存スキーマの定義クラスに合致しない重要な未知概念を発見した場合、一時的に `ap:UnclassifiedConcept` のインスタンスノードとしてグラフ内に退避させます。
   - その際、出現文脈（`ap:contextDescription`）、および想定される属性構造（`ap:suggestedProperties`）をノードプロパティに紐付けます。

2. **AI Agent による一時評価と提案生成 (AI Agent Triage & Proposal)**:
   - `OntologyEvolutionAgent` は、未処理の `ap:UnclassifiedConcept` を検出すると起動します。
   - 既存のオントロジースキーマ定義（OWL/Zod等）との類似性、セマンティックな関係性を分析し、以下のいずれかの提案（`EvolutionProposal`）を自律生成します。
     - **[昇格提案 (PROMOTE_CLASS)]**: 新規クラスとしての定義を推奨。適切なクラス名（例: `ap:SupportDivision`）、日本語ラベル、各プロパティ（型付）のZodコード、説明文、および判断理由を設計・提案。
     - **[統合提案 (MAP_TO_PROPERTY)]**: 既存クラス（例: `ap:Organization`）の属性にマッピング可能と判定し、マッピング先のルールを設計・提案。
     - **[却下提案 (DISCARD)]**: 単なるキーワードやノイズ、抽出ミスのため破棄を推奨。

3. **管理者の意思決定 (Human Approval)**:
   - 管理者は、エージェントが作成した提案（理由付き）と、抽出元ドキュメントの画像・テキスト箇所を確認します。
   - 提案内容（クラス名やデータ型）に微調整を加えた上で、「承認」または「却下」を判断します。

4. **スキーマの自動コンパイル (Compilation)**:
   - 管理者が承認を実行すると、システムは自動的に Zod バリデーターコードおよび `ontology.ttl` ファイルを動的に再生成（コンパイル）します。
   - これにより、次回以降のドキュメント解析から新概念が正式なクラスとして自動抽出されるようになります。
