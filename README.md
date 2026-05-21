# ontoNgn (Ontology Engine)

ontoNgn（オント・エンジン）は、多様な種類の文書（社内規定、操作マニュアル、行政案内など）を解析し、ドメイン独自のオントロジー（知識グラフ）を自動的・汎用的に生成・提供するバックグラウンド実行エンジンです。

バックエンドには **TypeScript (NestJS)** を採用し、**マルチモーダルLLM (Vision Model)** を用いてドキュメントのビジュアル情報（表や図のレイアウト）を損なわずに意味関係を直接抽出します。生成されたオントロジーは、GraphRAG（グラフ検索拡張生成）などの基盤データとしてAPI経由でリアルタイムに提供されます。

本システムは、APIを提供するバックエンドエンジン（サービス）として動作し、スキーマの自律進化に対する人間の承認などの一部機能のために最小限の **ontoNgn Console (Developer UI)** を提供します。

## 主な機能

1. **ドキュメント・レンダリング・パイプライン**
   - **PDF/Word/Excel の画像化**: アップロードされたドキュメントの各ページを、ビジュアル構造（表、図、レイアウト）を損なわずに解析するため、高解像度のPNG画像にレンダリングします。
   - Word (`.docx`) や Excel (`.xlsx`) は、LibreOffice 等を用いてPDFに一度変換した後、ページ画像としてレンダリングします。
2. **マルチモーダルLLM抽出エンジン**
   - LMStudio 等でローカルホストされたマルチモーダルLLMとの連携。
   - 設定ファイル（`.env` / `config.yaml`）による利用LLM（APIエンドポイント、モデルパラメータ）の動的切り替え。
   - ページの画像とテキスト情報から、ドメイン概念の要素（エンティティと関係性）をZodスキーマに従って直接抽出。
3. **AI駆動型スキーマ進化 (Schema Evolution)**
   - 抽出された未知の概念を `OntologyEvolutionAgent` が自律的に一次判定し、新規クラス昇格や既存プロパティへのマッピング提案を自動生成。
   - 開発者がコンソール画面で「承認」すると、ZodバリデーターコードとOWL定義（ontology.ttl）が動的に再コンパイルされます。
4. **DB非依存のオントロジー管理 (Clean Architecture)**
   - W3C標準のセマンティックウェブ規格（RDF/OWL、Turtle、JSON-LD）をサポート。
   - 設定ひとつで、**Kùzu (MIT)**、**Apache AGE (PostgreSQL)**、**Neo4j**、**インメモリRDF** 等の多様なデータベースを切り替え可能な抽象リポジトリ設計。
5. **GraphRAG（グラフ検索拡張生成）連携**
   - LlamaIndex.TS や LangChain.js、外部グラフDBへロード可能な形式でデータをエクスポート・API提供。

## 技術スタック

- **言語・フレームワーク**: TypeScript / NestJS (Node.js)
- **オントロジー操作**: `n3` (RDF/JS標準準拠のパーサー/シリアライザー)
- **ドキュメント処理**: `pdfjs-dist` (PDF画像レンダリング), LibreOffice CLI (Word/Excel変換用)
- **LLM/RAG連携**: `openai` (LMStudio 接続用), `llamaindex` (LlamaIndex.TS)
- **テスト**: `vitest`

## ディレクトリ構成

システムは、データ永続化や外部API（LLM）への結合度を下げるため、**クリーンアーキテクチャ**を採用しています。

```text
d:/dev/ontrogy/
├── docs/                       # 設計ドキュメント
│   └── architecture_design.md  # 詳細設計書（機能・アーキテクチャ・オントロジー定義）
├── src/                        # NestJS ソースコード
│   ├── main.ts                 # エントリーポイント
│   ├── app.module.ts           # アプリケーションルートモジュール
│   ├── domain/                 # ドメインレイヤー（ビジネスモデル、サービス/リポジトリインターフェース）
│   │   ├── models/             # GraphNode, GraphEdge, Procedure 等のドメインエンティティ
│   │   └── services/           # IGraphRepository, ILLMService などのインターフェース
│   ├── usecases/               # ユースケースレイヤー（オントロジー抽出、RAGエクスポート等）
│   ├── interfaces/             # インターフェースアダプター層
│   │   ├── api/                # Web API コントローラー (Fastify/Express)
│   │   ├── gateways/           # LMStudio連携、Neo4j/Kuzu/AGE/RDFリポジトリの具象実装
│   │   └── renderers/          # 各種ファイルを画像にレンダリングする変換器
│   └── infrastructure/         # インフラストラクチャ（設定読み込み、DI構成など）
├── package.json                # npm 依存パッケージ
├── tsconfig.json               # TypeScript コンパイル設定
└── README.md                   # 本ドキュメント
```

## セットアップと起動方法 (設計フェーズ)

詳細設計については、[docs/architecture_design.md](file:///d:/dev/ontrogy/docs/architecture_design.md) を参照してください。
実装開始時の環境構築手順は、今後の実装フェーズにおいて追加されます。
