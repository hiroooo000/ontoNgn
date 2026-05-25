import pytest
from fastapi.testclient import TestClient
from playwright.sync_api import Page

from app.main import app

client = TestClient(app)


def test_read_root() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello from ontoNgn"}


# Playwrightを使用したUI（フロントエンド側）テストのダミースケルトン
# ※バックエンドAPIに直接アクセスするテストではないですが、環境が動作するか確認用です。
@pytest.mark.skip(reason="Run separately with Playwright enabled")
def test_playwright_dummy(page: Page) -> None:
    # 実際はFastAPIのサーバーを立ち上げてテストしますが、ここでは外部のURLを叩いてブラウザが動作するか確認します。
    page.goto("data:text/html,<h1>Test</h1>")
    assert page.content() == "<html><head></head><body><h1>Test</h1></body></html>"
