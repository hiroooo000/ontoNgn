# ontoNgn (Ontology Engine) ドキュメント体系

本プロジェクトにおける設計ドキュメントの構成は以下の通りです。
ドキュメントは目的別にファイルを分割しており、各ファイル名の先頭には読むべき順序を示すプレフィックス（連番）を付与しています。

## ルート・ドキュメント (`docs/` フォルダ直下)

- **`00_document_structure.md`** (本ファイル)
  - プロジェクトのドキュメント体系と、各ファイルが担う役割を定義しています。
- **`01_specification.md`**
  - ソリューションの機能仕様書。背景課題、アプローチ、本システムで「何を実現するか（機能要件・非機能要件）」を定義します。
- **`02_system_design.md`**
  - 全体設計書。クリーンアーキテクチャに基づくアーキテクチャ構成、機能一覧、処理のフロー図などを定義します。
- **`03_data_model_design.md`**
  - データモデル設計書。RDBのスキーマ、オントロジー（知識グラフ）のクラス設計・関係性、ファイルの管理ルールなどを定義します。
- **`04_technology_decisions_report.md`**
  - 技術選定・比較検討報告書。データベースやフロントエンド（HTMX等）の技術スタックに関する採用理由や検討経緯を記録しています。
- **`zz_development_status.md`**
  - 現在の開発状況・実装済み機能と未実装機能の管理を行うステータス管理ドキュメントです。

## 詳細設計ドキュメント (`docs/detail_design/` フォルダ)

`02_system_design.md` で定義されている各機能固有の、実装するうえで必要となる詳細な設計内容やコードレベルのインターフェース定義を機能ごとに分割して格納しています。

- **`01_workflow_orchestrator.md`**
  - ワークフロー制御エンジンによるパイプラインのステート管理、非同期タスクキューの連動、エラーリカバリ、およびドキュメント収集の起点処理の詳細。
- **`02_document_render.md`**
  - ドキュメントを画像化する処理（Document Render API）の実装詳細。
- **`03_vision_extraction.md`**
  - 画像からの構造化テキスト抽出（Vision Extraction API）のインターフェースとGateway実装。
- **`04_ontology_generation.md`**
  - LLMを用いたオントロジー生成（Ontology Generation API）のインターフェース、Pydanticスキーマ定義、およびGateway実装。
- **`05_ontology_linking.md`**
  - 新規抽出されたオントロジーと既存グラフとの関連付け・リンク生成を行うエンジンの設計。
- **`06_ontology_evolution.md`**
  - 未分類概念の判定と提案を行うAI Agent（Ontology Evolution Agent）の設計。
- **`07_schema_compiler.md`**
  - スキーマ進化提案をPydantic/OWLファイルに反映するSchema Compilerの実装設計。
- **`08_schema_evolution_api.md`**
  - スキーマ進化提案に対するユーザーの承認・却下等のアクションを受け付けるAPI。
- **`09_graph_repository.md`**
  - データベース非依存を担保するためのGraph Repositoryインターフェース（DI）設計。
- **`10_console_ui.md`**
  - 処理状態ダッシュボードやスキーマ進化のフィードバック収集を担うフロントエンドSPAの設計。
- **`11_graph_visualization.md`**
  - 蓄積されたノードとエッジを動的に探索・可視化するネットワークグラフUIの設計。
