import asyncio
import os
import shutil
from typing import List

from app.core.config import Settings
from app.domain.models.graph import ExtractionResult, GraphNode
from app.domain.services.text_llm_service import ITextLLMService
from app.infrastructure.database.kuzu_db import KuzuDB
from app.interfaces.repositories.kuzu_graph_repository import KuzuGraphRepository
from app.usecases.generate_ontology import GenerateOntologyUseCase


# 検証用のモックLLMサービス
class MockLLMService(ITextLLMService):
    async def generate_ontology(self, text_content: str) -> ExtractionResult:
        # LLMが未分類概念（UnclassifiedConcept）を抽出したと仮定
        unclass_node = GraphNode(
            id="ap:UnclassifiedTarget",
            label="未知の申請先",
            properties={"type": "ap:UnclassifiedConcept", "description": "テキストに含まれるが分類できない概念"},
        )
        return ExtractionResult(nodes=[unclass_node], edges=[])

    async def extract_anchor_keywords(self, text_content: str) -> List[str]:
        return []

    async def validate_anchor(self, text_content: str, candidate_node: GraphNode) -> bool:
        return True

    async def generate_links(self, new_graph: ExtractionResult, context_subgraph: ExtractionResult) -> ExtractionResult:
        return new_graph


async def verify() -> None:
    print("=== 検証用スクリプトを開始します ===")

    # 1. 一時的なデータベースをセットアップ
    test_db_path = "./tests/integration/manual_tests/test_db"
    if os.path.exists(test_db_path):
        shutil.rmtree(test_db_path)

    settings = Settings(kuzu_db_path=test_db_path)
    db = KuzuDB(settings)
    repo = KuzuGraphRepository(db)
    llm_service = MockLLMService()

    usecase = GenerateOntologyUseCase(llm_service, repo)

    # 2. ユースケースを実行（未分類概念を含む文章を入力したと仮定）
    print("\n【処理中】ユースケースを実行しています...")
    result = await usecase.execute("このテキストには未知の概念が含まれています。")

    # 3. 戻り値の確認（APIレスポンスのモック）
    print("\n【検証1】戻り値の needs_evolution フラグの確認")
    print(f"-> result.needs_evolution = {result.needs_evolution}")
    if result.needs_evolution:
        print("✅ 成功: needs_evolution が True に設定されています。")
    else:
        print("❌ 失敗: needs_evolution が False です。")

    # 4. データベースの保存状態の確認
    print("\n【検証2】データベース上の status='pending' の確認")
    # DBから ap:UnclassifiedConcept を検索してプロパティを確認
    nodes_in_db = await repo.find_nodes_by_type("ap:UnclassifiedConcept")

    if nodes_in_db:
        target = nodes_in_db[0]
        status = target.properties.get("status")
        print(f"-> DBに保存されたノードID: {target.id}")
        print(f"-> プロパティ内のstatus: {status}")

        if status == "pending":
            print("✅ 成功: DB内で status='pending' が付与されて保存されています。")
        else:
            print("❌ 失敗: pending ステータスが付与されていません。")
    else:
        print("❌ 失敗: DBに UnclassifiedConcept が保存されていません。")

    if os.path.exists(test_db_path):
        shutil.rmtree(test_db_path)


if __name__ == "__main__":
    asyncio.run(verify())
