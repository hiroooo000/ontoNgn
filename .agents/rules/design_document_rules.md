# ontoNgn 設計ドキュメント構成ルール (Design Document Structure Rules)

本ルールは、`ontoNgn` プロジェクトにおける設計書の構成、役割分担、および各ファイルの記述内容を規定するものです。
AIエージェント（Antigravity等）が、本リポジトリの設計書を作成、修正、または追加する際には、以下の構成ルールを厳格に遵守しなければなりません。

---

## 1. 基本方針 (General Principles)

設計書は、以下の**3段階の設計書およびデータモデル定義書**（合計4つのMarkdownファイル）に分割して管理します。情報が異なるファイル間で混在したり、重複したりすることを防ぐため、各ファイルの役割に沿って記述を行ってください。

また、設計書内のファイル間リンクは `file:///workspaces/ontrogy/docs/[filename].md` 形式のワークスペース絶対パスで記述してください。

---

## 2. 各ファイルの役割と記述内容 (File Roles and Contents)

### 2.1 仕様書 ([specification.md](file:///workspaces/ontrogy/docs/specification.md))
システムのコンセプト（背景・課題・狙い）、要件、および大枠の技術仕様と利用方法を記載します。

*   **ソリューションのコンセプト**: 課題定義、Vision LLM を用いた自動生成アプローチ、GraphRAG への適合性など。
*   **ソリューションの機能仕様**: 機能要件、非機能要件、および「フロントエンド・ロジックレス (Thin Client / Dumb UI)」などの設計方針。
*   **ソリューションのアーキテクチャ仕様**: なぜ Python + FastAPI + HTMX なのか、なぜ DB 非依存設計なのかなどのアーキテクチャ決定事項と背景。
*   **ソリューションの使い方**: 開発環境の起動方法、基本的な解析フロー、代表的な API の利用例。

### 2.2 全体設計書 ([system_design.md](file:///workspaces/ontrogy/docs/system_design.md))
システムの全体的な静的・動的構造を視覚化し、機能と処理の対応関係を記載します。

*   **ソフトウェアアーキテクチャの全体構成**: クリーンアーキテクチャのレイヤー定義とディレクトリ構造。
*   **機能一覧および各機能の概要**: 各主要モジュールの役割の定義。
*   **各機能を構成する処理一覧**: 各APIエンドポイントや内部ユースケースの処理定義。
*   **処理フロー図**: `flowchart TD` (Mermaid) によるシステム全体の処理フロー。
*   **クラス図**: `classDiagram` (Mermaid) によるクリーンアーキテクチャに基づく依存関係。
*   **シーケンス図**: `sequenceDiagram` (Mermaid) による処理シーケンス。

### 2.3 データモデル定義書 ([data_model_design.md](file:///workspaces/ontrogy/docs/data_model_design.md))
データベース構造、永続化モデル、およびファイル・オントロジーの管理ルールを記載します。

*   **RDBに関するデータモデル定義**: `DocumentSource`（ドキュメント管理、ステータス、ハッシュ等）の Pydantic 定義およびテーブル物理設計。将来的な pgvector / JSONB の適用方針。
*   **オントロジーに関するデータモデル定義**: クラス定義、プロパティ・関係性定義、`classDiagram` (Mermaid) によるクラス関係図、Pydantic モデル表現 (`GraphNode`, `GraphEdge`, `ExtractionResult`)。
*   **ファイルの格納/管理ルール**: ソースファイル、一時画像、組み込みDB、OWL/TTL、Pydantic定義等のディレクトリ配置およびライフサイクルルール。
*   **その他データに関する設計内容**: オントロジー差分更新（参照カウント方式）アルゴリズム、GraphRAG 連携仕様（LlamaIndex用 JSON および Turtle 形式のエクスポートフォーマット）。

### 2.4 詳細設計書 ([detailed_design.md](file:///workspaces/ontrogy/docs/detailed_design.md))
各処理の具体的なロジック、クラス設計、実装コード・擬似コードを記載します。

*   **処理ごとの詳細設計**:
    *   データベース接続・抽象リポジトリの Python 抽象クラスおよび DI プロバイダコード。
    *   ドキュメントレンダラーの LibreOffice / pdf2image 変換コード。
    *   Vision / Text LLM 抽象サービス、Pydantic バリデーション、LMStudioGateway の実装コード。
    *   スキーマ進化 AI Agent (`OntologyEvolutionAgent`) と SchemaCompiler の実装コード・プロンプト。
    *   ドキュメント収集（Ingestion）エンジン（Upload, Scanner, Downloader）の処理詳細。

---

## 3. エージェントへの指示事項 (Instructions for Agents)

1.  **情報の分離の徹底**: 処理の具体的なコードを `specification.md` や `system_design.md` に記述してはなりません。また、ビジネス要件を `detailed_design.md` に記述してはなりません。
2.  **一貫性の維持**: `system_design.md` の「処理一覧」を追加・変更した場合は、必ず `detailed_design.md` に対応する詳細ロジックを追記し、必要に応じて `data_model_design.md` のデータ構造を更新してください。
3.  **リンクの検証**: 設計ドキュメントを変更した際は、ファイル間の Markdown リンクが切れていないか、また Mermaid 図の構文エラーがないかを必ず検証してください。
