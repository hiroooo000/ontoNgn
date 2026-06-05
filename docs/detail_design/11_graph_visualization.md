# 11. Graph Visualization (グラフ可視化機能) 詳細設計

## 1. 対象機能の概要・処理一覧

Kùzu DB内に蓄積されたオントロジーデータ（ノードおよびエッジ）を視覚的に探索・確認するためのUIおよびAPIです。
大規模なグラフ全体を一度に描画することによるパフォーマンス低下を防ぐため、**「キーワード検索を起点としたサブグラフの表示」**アプローチを採用しています。

### 処理一覧
1. **キーワード検索**: ユーザーが入力したキーワードから関連するアンカーノードを検索する。
2. **サブグラフ展開**: 検索されたアンカーノード、または画面上で選択したノードを起点として、指定ホップ数（Nホップ以内）のサブグラフを取得する。
3. **グラフ描画・物理演算**: フロントエンドにて `vis-network` を用い、ノードとエッジを物理演算（Force-directed）レイアウトで描画・再配置する。
4. **詳細情報表示**: 画面上のノード・エッジをクリックした際に、プロパティ詳細情報をツールチップ/サイドパネルで表示する。

## 2. モジュール構成図・クラス図

### モジュール構成図
```mermaid
classDiagram
    direction TB
    
    namespace Frontend_Vue {
        class GraphCanvas {
            <<vis-network>>
        }
        class SidebarPanel
        class GraphApiClient
    }
    
    namespace Backend_FastAPI {
        class GraphRouter
    }
    
    namespace Repositories {
        class IGraphRepository
    }

    SidebarPanel --> GraphApiClient : 検索・展開要求
    GraphCanvas --> GraphApiClient : ノードダブルクリック(Expand)
    GraphApiClient --> GraphRouter : REST API通信
    GraphRouter --> IGraphRepository : DBクエリ実行
```

### クラス図（API入出力スキーマ）
```mermaid
classDiagram
    class GraphSearchResponse {
        <<Pydantic Schema>>
        +List~GraphNode~ nodes
        +List~GraphEdge~ edges
        +List~GraphNode~ hits
    }
    
    class GraphExpandResponse {
        <<Pydantic Schema>>
        +List~GraphNode~ nodes
        +List~GraphEdge~ edges
    }
```

## 3. 処理フロー図・シーケンス図

### 処理フロー図
```mermaid
flowchart TD
    A["サイドバーでキーワード入力・検索"] --> B["GET /api/v1/graph/search"]
    B --> C["DB: アンカーノード検索 (hits)"]
    C --> D["DB: アンカー起点のサブグラフ取得 (nodes/edges)"]
    D --> E["フロントエンドへJSON返却"]
    E --> F["vis-networkキャンバス初期化・描画"]
    F --> G{"キャンバス上でノードをダブルクリック?"}
    G -- Yes --> H["GET /api/v1/graph/expand (特定ノードID)"]
    H --> I["DB: 新たな起点からサブグラフ取得"]
    I --> J["取得結果を既存のvis-networkデータセットにマージして再描画"]
    G -- No --> K["操作待機 (Tooltip表示等)"]
```

### シーケンス図
```mermaid
sequenceDiagram
    actor User
    participant UI as Vue Frontend (vis-network)
    participant API as GraphRouter
    participant DB as IGraphRepository

    User->>UI: 検索「児童手当」(hops=1)
    UI->>API: GET /graph/search?q=児童手当&hops=1
    
    API->>DB: search_nodes_by_keywords(["児童手当"])
    DB-->>API: アンカーノード群 (hits)
    
    API->>DB: get_subgraph(anchor_ids, max_hops=1)
    DB-->>API: 関連サブグラフ (nodes/edges)
    
    API-->>UI: GraphSearchResponse
    UI->>UI: 物理演算レイアウト描画
    UI-->>User: グラフ表示完了
    
    User->>UI: ノードAをダブルクリック (Expand)
    UI->>API: GET /graph/expand?node_id=A&hops=1
    API->>DB: get_subgraph([A], max_hops=1)
    DB-->>API: 追加サブグラフ
    API-->>UI: GraphExpandResponse
    UI->>UI: 既存グラフにノード・エッジを追加マージして再配置
```

## 4. APIインターフェース仕様 / 入出力データ（スキーマ）

### 4.1 検索起点のグラフ取得
- **`GET /api/v1/graph/search`**
- **Query Params**: `q` (キーワード), `hops` (デフォルト1), `limit` (デフォルト50)
- **Response**: `nodes`, `edges`, `hits` (アンカーとなったノードリスト) のリストを含むJSON。

### 4.2 指定ノードからのサブグラフ展開
- **`GET /api/v1/graph/expand`**
- **Query Params**: `node_id` (起点ノードID), `hops` (デフォルト1)
- **Response**: `nodes`, `edges` のリストを含むJSON（既存UIへのマージ用）。

## 5. 異常系・エラーハンドリング

| 想定されるエラー | 原因 | 対応方針 |
| :--- | :--- | :--- |
| **検索ヒットなし** | キーワードに合致するノードがDBに存在しない | 空のレスポンス（`nodes=[]`, `hits=[]`）を返し、フロントエンド側で「該当ノードが見つかりません」と表示する。 |
| **ノード数が多すぎる** | ハブとなっているノードを展開した等 | DBクエリ側で `limit` を設け（例: 500ノード）、超過した場合は警告メッセージ付きで制限されたサブグラフを返す。 |
| **バックエンド通信エラー** | APIサーバーダウン | フロントエンドでエラーをCatchし、画面にエラー通知（Toast）を表示する。 |

## 6. 依存する環境変数・外部設定

- **フロントエンドビルド**: Vue 3 / Vite のビルド環境。開発時はVite dev-server を用いる。本番稼働時はビルド済みの静的ファイルをFastAPI (`StaticFiles`) から配信するため、設定パス（`STATIC_DIR` 等）の整合性が必要。
- **グラフ描画ライブラリ**: `vis-network` (NPMパッケージ)

## 7. テスト方針

- **単体テスト (バックエンド)**:
  - `GraphRouter` の各エンドポイントを `TestClient` で呼び出し、`IGraphRepository` をモック化して、`hops` や `limit` パラメータが正しく伝搬されるかを検証。
- **単体テスト (フロントエンド)**:
  - `Vitest` を用いて、APIクライアントモジュールが正しく `GraphSearchResponse` をパースし、vis-network 用のデータセットにマージできるかをテスト。
