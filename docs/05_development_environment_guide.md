# 開発環境ガイド (Development Environment Guide)

本ドキュメントは、プロジェクト `ontoNgn` における開発環境の初期セットアップ手順と、日々の開発ワークフロー（Lint、型チェック、テストの実施方法）について解説します。

---

## 1. 環境セットアップ手順 (Setup Instructions)

リポジトリをクローンした後、開発を開始するために以下の手順を実行してください。

### 1.1. DevContainer でプロジェクトを開く
本プロジェクトは DevContainer を利用して環境をコンテナ化しています。
1. VSCode でクローンしたリポジトリのルートフォルダを開きます。
2. 画面右下に表示される「Reopen in Container」ポップアップをクリックするか、コマンドパレット (`Ctrl+Shift+P` / `Cmd+Shift+P`) から **`Dev Containers: Reopen in Container`** を選択します。
3. コンテナのビルドが完了するまで待ちます。
   - ※ この過程で、Python 3.12 や LibreOffice、およびパッケージマネージャの `uv`、Playwrightのシステム依存ライブラリが自動インストールされます。

### 1.2. パッケージの同期とインストール
コンテナが起動し、VSCodeのターミナルが開いたら、以下のコマンドを実行してプロジェクトの依存パッケージをインストールします。

```bash
uv sync
```
これにより、`pyproject.toml` と `uv.lock` に基づいて高速にパッケージがインストールされ、仮想環境 (`.venv`) が構成されます。

### 1.3. フロントエンド (Vue 3) パッケージのインストール
本プロジェクトはバックエンド(Python)とフロントエンド(Node.js/Vue 3)が分離されたSPA構成です。フロントエンドの依存パッケージもインストールします。

```bash
cd frontend
npm install
cd ..
```

### 1.3. Playwright（UIテスト自動化ツール）のブラウザインストール
UI/E2Eテストを実行するために必要なブラウザバイナリをインストールします。

```bash
uv run playwright install
```
これで開発環境の基本的なセットアップは完了です。

---

## 2. 開発ワークフローとテストの実施方法 (Workflow & Testing)

日々の開発において、コード品質を保つために以下のツールを使用します。すべてのコマンドはコンテナのターミナル上で実行してください。

### 2.1. コードフォーマットと Lint チェック (Ruff)
本プロジェクトでは、コードの整形および構文チェックに **Ruff** を使用しています。

- **Lint チェックの実行**
  ```bash
  uv run ruff check .
  ```
- **Lint エラーの自動修正（インポート順序など）**
  ```bash
  uv run ruff check --fix .
  ```
- **コードフォーマット（整形）の実行**
  ```bash
  uv run ruff format .
  ```

### 2.2. 静的型解析 (Mypy)
Pythonの型ヒントが正しく記述されているかを確認するために **Mypy** を使用します。

- **型チェックの実行**
  ```bash
  uv run mypy .
  ```
  `Success: no issues found` と表示されれば問題ありません。

### 2.3. テストの実施 (Pytest & Playwright)
単体テストやAPIテスト、および Playwright を利用した UI（ヘッドレスブラウザ）テストの実行には **pytest** を使用します。

- **全テストの実行 (およびCIワークフロー)**
  ```bash
  uv run task ci
  ```
  ※ `task ci` を実行すると、以下の処理が順次行われます。
  1. **Lintおよびフォーマットチェック**（エラーがあれば修正を促します）
  2. **過去のテストDBのクリーンアップ**（`tests/test_output.kuzu_db/` を削除）
  3. **テストの実行**
  テスト完了後、結合テストで生成されたデータは `tests/test_output.kuzu_db/` ディレクトリにKuzuDBファイルとして保存されたままになります。これにより、テスト実行後に実際に出力されたグラフデータを後から検証・確認することが可能です。

- **(補足) テストランナー(pytest)の直接実行**
  ```bash
  uv run pytest
  ```
- **詳細な出力（Verbose）でテストを実行**
  ```bash
  uv run pytest -v
  ```
- **特定のテストファイルのみを実行**
  ```bash
  uv run pytest tests/test_main.py
  ```
- **標準出力（print等）を表示させながらテストを実行**
  ```bash
  uv run pytest -s
  ```

### 2.4. フロントエンド (JavaScript/Vue) のテスト
フロントエンドのUIコンポーネントやロジックの単体テストには **Vitest** を使用します。

- **JS単体テストの実行**
  ```bash
  cd frontend
  npm run test
  ```

すべてのチェックとテストが通ることを確認した上で、変更をコミット・プッシュするようにしてください。

### 2.4. グラフデータベース (KuzuDB) の格納データの目視確認
テストコードの実行だけでなく、実際にデータがKuzuDBにどのように格納されるか（日本語文字列が正しくデコードされているか等）を視覚的に確認するための専用スクリプトを用意しています。

- **目視確認スクリプトの実行**
  ```bash
  PYTHONPATH=. uv run python tests/manual_tests/verify_db_contents.py
  ```
このスクリプトを実行すると、テスト用のJSONデータが一時的なKuzuDBに保存され、その後直接Cypherクエリが発行されてDB内の「ノード一覧」と「エッジ一覧」が標準出力（コンソール）に表示されます。DBへの永続化ロジックの動作確認に活用してください。

---

## 3. ローカル開発サーバーの起動とAPI動作確認 (Running the API Server)

FastAPI による Web API のローカル開発サーバーを起動し、Swagger UI から動作確認を行う手順です。

### 3.1. 環境変数ファイル (.env) の準備
サーバーを起動する前に、データベースのパスやLLM（LMStudio等）のAPIキーなどの環境変数を設定する必要があります。
リポジトリに含まれる設定の雛形ファイル `.env.template` を、動作環境に合わせて以下のいずれかの名前に変更（コピー）して使用してください。

- **`.env.dev`** : ローカル開発・マニュアルテスト用（`task start-devsv` などで使用）
- **`.env.test`** : CI / 自動テスト用（`task ci` などで使用）
- **`.env.prod`** : 本番環境用

```bash
cp .env.template .env.dev
cp .env.template .env.test
```

ファイルを作成後、必要に応じて `.env.dev` や `.env.test` ファイル内の設定値（DBパス、APIキー、エンドポイントなど）をご自身の環境に合わせて変更してください。
FastAPI の設定読み込みは `APP_ENV` 環境変数を参照して自動的に適切なファイルを選択します（未指定の場合は `.env.test` をデフォルトとします）。

### 3.2. 開発サーバーの起動 (バックエンド & フロントエンド)
本システムはバックエンドとフロントエンドが分離しているため、開発時はそれぞれのサーバーを立ち上げる必要があります。VSCodeでターミナルを2つ開いて実行してください。

**ターミナル1: バックエンド (FastAPI) の起動**
コンテナのターミナルで以下のコマンドを実行し、Uvicorn 開発サーバーを起動します。
`--reload` オプションを指定しているため、コードを変更すると自動的にサーバーが再起動します。

```bash
uv run task start-devsv
```
※ 内部的には `uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` が実行されます。

**ターミナル2: フロントエンド (Vue 3 + Vite) の起動**
```bash
cd frontend
npm run dev
```
これにより Vite の高速な開発サーバーが起動し、ホットリロード (HMR) が有効になります。フロントエンドの開発画面は通常 `http://localhost:5173` で確認できます。

> **結合テスト(Playwright)実行時の注意**
> E2Eテストや本番環境へのデプロイ時は、フロントエンドをビルド（`npm run build`）し、出力された `dist/` ディレクトリを FastAPI が直接静的ファイルとしてマウント・配信する仕組みになります。開発時のみ2つのサーバーを独立して立ち上げます。

### 3.3. Swagger UI を使った API の動作確認
サーバーが起動したら、ブラウザで以下のURLにアクセスしてください。

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)

Swagger UI（対話型APIドキュメント）上から、直接APIの動作確認を行うことができます。

1. `/api/v1/ontology/generate` エンドポイントのアコーディオンを開きます。
2. 右側の **[Try it out]** ボタンをクリックします。
3. `Request body` が `text/plain` になっている入力欄に、解析したいテキスト（改行を含む行政ドキュメントなど）を直接貼り付けます。
4. **[Execute]** ボタンをクリックします。
5. しばらく待つと、下部の `Server response` エリアに、抽出されたオントロジー（ノードとエッジ）のJSON結果が返却されます。
