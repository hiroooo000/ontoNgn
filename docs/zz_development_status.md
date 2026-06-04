# ontoNgn 開発状況サマリー (Development Status)

`docs/01_specification.md` に定義されている機能要件と、現在のコードベース（`app/` および `frontend/`）の実装状況を整理したステータス管理ドキュメントです。

## 実装済みの機能 (Implemented)

現在のシステムは、テキストからオントロジーを抽出し、グラフDBに保存・可視化する「中核部分」が実装されています。

*   **4. オントロジー生成API (Ontology Generation API)**
    *   `/api/v1/ontology/generate` エンドポイントとして実装済み。
    *   `GenerateOntologyUseCase` において、テキストからLLMを用いたオントロジーの抽出、既存ノード（アンカー）の検索、コンテキスト統合、進化フラグ（未知の概念）の判定処理が実装されています。
*   **5. 型安全なバリデーション (Type-safe Validation)**
    *   `ExtractionResult` や `GraphNode`, `GraphEdge` などの Pydantic スキーマを用いて、LLMからの入出力およびAPIのレスポンスが型安全に定義されています。
*   **6. DB非依存のオントロジー管理 (IGraphRepository)**
    *   クリーンアーキテクチャに基づき `IGraphRepository` インターフェースが定義されており、具象クラスとして `kuzu_graph_repository.py` (Kùzu DB) の実装が完了しています。
*   **10. グラフ可視化・探索機能 (Graph Visualization)**
    *   **バックエンド**: グラフ探索用APIとして `/api/v1/graph/search` および `/api/v1/graph/expand` が実装済みです。
    *   **フロントエンド**: Vue 3 SPAとして `GraphViewer.vue` が実装されており、バックエンドAPIと連携してネットワークグラフを描画する基盤が構築されています。

---

## 部分的に実装・または開発中 (Partially Implemented)

*   **1. ワークフロー制御エンジン (Workflow Orchestrator)**
    *   `GenerateOntologyUseCase` にて一部の連鎖処理（抽出→検索→統合→保存）は実装されていますが、仕様書にあるような **「非同期キューを用いた状態管理（Uploaded, Rendering 等のステータス遷移）」や「エラーリカバリ」等のパイプライン全体を管理する仕組みは未実装** です。

---

## 未実装の機能 (Not Implemented)

ドキュメントのインジェストや前処理（画像化・テキスト抽出）、および外部システム連携部分が未着手となっています。

*   **2. ドキュメント画像レンダリングAPI (Document Render API)**
    *   PDFやOfficeファイルを画像にレンダリングする処理・APIは存在しません。
*   **3. Visionテキスト抽出API (Vision Extraction API)**
    *   画像からレイアウト構造を保ったテキストを抽出するVision Model連携部分は未実装です。（現在はプレーンテキストを直接受け取る状態です）
*   **7. GraphRAG 連携（エクスポート機能）**
    *   構造化JSONやTurtle形式 (`.ttl`) で外部にエクスポートする機能・APIは未実装です。
*   **8. マルチランゲージ対応 (Multi-language Support)**
    *   エラーメッセージの多言語化や、抽出オントロジーの言語指定機能は組み込まれていません。
*   **9. ドキュメント収集エンジン (Ingestion Engine)**
    *   指定フォルダの定期スキャンやURLからの自動ダウンロードなど、自動収集の仕組みは未実装です。
*   **Schema Evolution API (スキーマ進化管理API)**
    *   未承認のオントロジーやスキーマ進化提案をユーザーが確認し、承認（クラス昇格/既存マッピング）または却下（データ破棄）する機能は未実装です。
