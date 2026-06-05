# ontoNgn 開発状況サマリー (Development Status)

`docs/02_system_design.md` に定義されている機能一覧（01〜11の主要モジュール）と、現在のコードベース（`app/` および `frontend/`）の実装状況を整理したステータス管理ドキュメントです。

## 実装済みの機能 (Implemented)

現在のシステムは、テキストからオントロジーを抽出し、グラフDBに保存・可視化する「中核部分」が実装されています。

*   **04. Ontology Generation API**
    *   `/api/v1/ontology/generate` エンドポイント実装済み。テキストからLLMを用いたオントロジーの抽出処理が動作します。
*   **09. Graph Repository**
    *   クリーンアーキテクチャに基づき `IGraphRepository` が定義され、具象として `Kùzu DB` (`kuzu_graph_repository.py`) の実装が完了しています。
*   **11. Graph Visualization UI**
    *   **バックエンド**: グラフ探索用API (`/api/v1/graph/search`, `/expand`) が実装済みです。
    *   **フロントエンド**: Vue 3 SPA (`GraphViewer.vue`) が実装されており、`vis-network` を用いてネットワークグラフを描画する基盤が構築されています。

---

## 部分的に実装・または開発中 (Partially Implemented)

*   **01. Workflow Orchestrator**
    *   `GenerateOntologyUseCase` にて一部の連鎖処理（抽出→検索→統合→保存）は実装されていますが、本来の仕様である **「非同期キューを用いた状態管理（Uploaded, Rendering 等のステータス遷移）」「エラーリカバリ」および「ドキュメント自動収集（Ingestion Engine）」は未実装** です。

---

## 未実装の機能 (Not Implemented)

ドキュメントのインジェストや前処理（画像化・テキスト抽出）、およびスキーマの進化（人間の承認）に関する部分が未着手となっています。

*   **02. Document Render API**
    *   PDFやOfficeファイルを画像にレンダリングする処理・APIは未実装です。
*   **03. Vision Extraction API**
    *   画像からレイアウト構造を保ったテキストを抽出するVision Model連携部分は未実装です。（現在はプレーンテキストを直接受け取る状態です）
*   **05. Ontology Linking Engine**
    *   インターフェースは定義されていますが、抽出時の既存ノード（アンカー）検索およびコンテキスト統合の実ロジックは未実装です。
*   **06. Ontology Evolution Agent**
    *   未知の概念にフラグをセットするのみで、AIエージェントによるクラス昇格・マッピング提案の生成ロジックは未実装です。
*   **07. Schema Compiler**
    *   承認されたスキーマ進化をPydanticやOWLファイルに動的に書き換えるコンパイラ機能は未実装です。
*   **08. Schema Evolution API**
    *   未承認のオントロジーやスキーマ進化提案をユーザーが確認し、承認・却下する機能は未実装です。
*   **10. Console UI (SPA)**
    *   処理状態ダッシュボードやスキーマ進化のフィードバックを行うHTMXを用いた管理画面は未実装です。

---

## その他の未実装項目 (Enhancements & Integrations)

*   **Export API (GraphRAG / Turtle)**
    *   構造化JSONやTurtle形式 (`.ttl`) で外部にエクスポートする連携API機能は未実装です。
*   **マルチランゲージ対応**
    *   エラーメッセージの多言語化や、抽出オントロジーの言語指定機能は組み込まれていません。
