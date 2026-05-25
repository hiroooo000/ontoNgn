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
これで開発環境のセットアップは完了です。

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
