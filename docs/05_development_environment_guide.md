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

- **全テストの実行**
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

すべてのチェックとテストが通ることを確認した上で、変更をコミット・プッシュするようにしてください。

---

## 3. ローカル開発サーバーの起動とAPI動作確認 (Running the API Server)

FastAPI による Web API のローカル開発サーバーを起動し、Swagger UI から動作確認を行う手順です。

### 3.1. 環境変数ファイル (.env) の準備
サーバーを起動する前に、データベースのパスやLLM（LMStudio等）のAPIキーなどの環境変数を設定する必要があります。
リポジトリに含まれる設定の雛形ファイル `.env.example` を `.env` という名前に変更（`mv`）またはコピー（`cp`）して使用してください。

```bash
mv .env.example .env
# もしくは cp .env.example .env
```

ファイルを作成後、必要に応じて `.env` ファイル内の設定値（APIキーやエンドポイントなど）をご自身の環境に合わせて変更してください。

### 3.2. サーバーの起動
コンテナのターミナルで以下のコマンドを実行し、Uvicorn 開発サーバーを起動します。
`--reload` オプションを指定しているため、コードを変更すると自動的にサーバーが再起動します。

```bash
uv run task start-devsv
```
※ 内部的には `uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` が実行されます。

### 3.3. Swagger UI を使った API の動作確認
サーバーが起動したら、ブラウザで以下のURLにアクセスしてください。

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)

Swagger UI（対話型APIドキュメント）上から、直接APIの動作確認を行うことができます。

1. `/api/v1/ontology/generate` エンドポイントのアコーディオンを開きます。
2. 右側の **[Try it out]** ボタンをクリックします。
3. `Request body` が `text/plain` になっている入力欄に、解析したいテキスト（改行を含む行政ドキュメントなど）を直接貼り付けます。
4. **[Execute]** ボタンをクリックします。
5. しばらく待つと、下部の `Server response` エリアに、抽出されたオントロジー（ノードとエッジ）のJSON結果が返却されます。
