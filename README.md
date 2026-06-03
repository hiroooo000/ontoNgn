# ontoNgn (Ontology Engine)

ontoNgn（オント・エンジン）は、多様な種類の文書（社内規定、操作マニュアル、行政案内など）を解析し、ドメイン独自のオントロジー（知識グラフ）を自動的・汎用的に生成・提供するバックグラウンド実行エンジンです。

バックエンドには **Python (FastAPI)** を採用し、**マルチモーダルLLM (Vision Model)** を用いてドキュメントのビジュアル情報（表や図のレイアウト）を損なわずに意味関係を直接抽出します。生成されたオントロジーは、GraphRAG（グラフ検索拡張生成）などの基盤データとしてAPI経由でリアルタイムに提供されます。

本システムは、APIを提供するバックエンドエンジン（サービス）として動作し、スキーマの自律進化に対する人間の承認などの一部機能のために最小限の **ontoNgn Console (Developer UI)** を **Vue 3 (SPA)** として提供します。

## 主な機能

1. **ドキュメント・レンダリング・パイプライン**
   - **PDF/Word/Excel の画像化**: アップロードされたドキュメントの各ページを、ビジュアル構造（表、図、レイアウト）を損なわずに解析するため、高解像度のPNG画像にレンダリングします。
   - Word (`.docx`) や Excel (`.xlsx`) は、LibreOffice 等を用いてPDFに一度変換した後、ページ画像としてレンダリングします。
2. **マルチモーダルLLM抽出エンジン**
   - LMStudio 等でローカルホストされたマルチモーダルLLMとの連携。
   - 設定ファイル（`.env` / `config.py`）による利用LLM（APIエンドポイント、モデルパラメータ）の動的切り替え。
   - ページの画像とテキスト情報から、ドメイン概念の要素（エンティティと関係性）をPydanticスキーマに従って直接抽出。
3. **AI駆動型スキーマ進化 (Schema Evolution)**
   - 抽出された未知の概念を `OntologyEvolutionAgent` が自律的に一次判定し、新規クラス昇格や既存プロパティへのマッピング提案を自動生成。
   - 開発者がコンソール画面で「承認」すると、PydanticバリデーターコードとOWL定義（ontology.ttl）が動的に再コンパイルされます。
4. **DB非依存のオントロジー管理 (Clean Architecture)**
   - W3C標準のセマンティックウェブ規格（RDF/OWL、Turtle、JSON-LD）をサポート。
   - 設定ひとつで、**Kùzu (MIT)**、**Apache AGE (PostgreSQL)**、**Neo4j**、**インメモリRDF** 等の多様なデータベースを切り替え可能な抽象リポジトリ設計。
5. **GraphRAG（グラフ検索拡張生成）連携**
   - LlamaIndex や LangChain、外部グラフDBへロード可能な形式でデータをエクスポート・API提供。
   - PostgreSQL (`pgvector`) を用いたベクトル検索との統合も視野に入れたアーキテクチャ。

## 技術スタック

- **バックエンド (API)**: Python / FastAPI / Pydantic
- **フロントエンド (UI)**: TypeScript / Vue 3 / Vite
- **パッケージ管理・仮想環境**: uv (Python), npm (Node.js)
- **コード品質・テスト**: Ruff, mypy, pytest, Playwright, Vitest
- **データベース (Graph/Vector)**: Kùzu, Apache AGE, Neo4j, pgvector (PostgreSQL)

## ディレクトリ構成

システムは、データ永続化や外部API（LLM）への結合度を下げるため、**クリーンアーキテクチャ**を採用しています。

```text
ontrogy/
├── docs/                       # 設計ドキュメント (システム設計、仕様、開発ガイド等)
├── app/                        # FastAPI バックエンド ソースコード
│   ├── main.py                 # エントリーポイント
│   ├── core/                   # 環境設定と共通基盤
│   ├── domain/                 # ドメインレイヤー（ビジネスモデル、サービス/リポジトリインターフェース）
│   ├── usecases/               # ユースケースレイヤー（オントロジー抽出、RAGエクスポート等）
│   ├── workflows/              # ワークフロー制御層
│   ├── interfaces/             # インターフェースアダプター層（APIルーター、Gateway、Renderer等）
│   └── infrastructure/         # インフラストラクチャ層（DBセッション等）
├── frontend/                   # Vue 3 フロントエンド ソースコード (SPA)
│   ├── src/                    # UIソースコード
│   └── package.json            # npm 依存パッケージ
├── tests/                      # テストコード (pytest, Playwright)
├── pyproject.toml              # Python 依存パッケージ (uv)
├── uv.lock                     # uv ロックファイル
└── README.md                   # 本ドキュメント
```

## セットアップと起動方法

本プロジェクトのアーキテクチャ詳細については [docs/02_system_design.md](file:///workspaces/ontrogy/docs/02_system_design.md) を、
ローカルでの環境構築・開発サーバーの起動方法・テストの実行については [docs/05_development_environment_guide.md](file:///workspaces/ontrogy/docs/05_development_environment_guide.md) を参照してください。
