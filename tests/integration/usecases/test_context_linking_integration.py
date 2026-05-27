import json
from pathlib import Path
from typing import Any, AsyncGenerator, List

import pytest
import pytest_asyncio

from app.core.config import Settings
from app.domain.models.graph import ExtractionResult, GraphNode
from app.domain.services.text_llm_service import ITextLLMService
from app.infrastructure.database.kuzu_db import KuzuDB
from app.interfaces.repositories.kuzu_graph_repository import KuzuGraphRepository
from app.usecases.generate_ontology import GenerateOntologyUseCase


class MockLLMService(ITextLLMService):
    """
    結合テスト用のモックLLMサービス。
    LLM APIを実際に叩かずに、ダミーのキーワードや推論結果を即座に返す。
    """

    async def generate_ontology(self, text_content: str) -> ExtractionResult:
        raise NotImplementedError("This method is not used in context linking tests.")

    async def extract_anchor_keywords(self, text_content: str) -> List[str]:
        return ["ダミーキーワード"]

    async def validate_anchor(self, text_content: str, candidate_node: GraphNode) -> bool:
        return True

    async def generate_links(self, new_graph: ExtractionResult, context_subgraph: ExtractionResult) -> ExtractionResult:
        # 実際の処理では推論してリンクを繋ぐが、テストでは入力グラフをそのまま返す
        return new_graph


@pytest_asyncio.fixture(scope="session")
async def temp_kuzu_db() -> AsyncGenerator[KuzuDB, None]:
    """KuzuDBのテスト用インスタンスを提供するフィクスチャ（結果は残される）"""
    # KuzuDBはシングルトンのため、念のため初期化
    KuzuDB._instance = None

    db_path = Path("tests/test_output.kuzu_db")
    settings = Settings(kuzu_db_path=str(db_path))
    db = KuzuDB(settings=settings)

    yield db

    # クリーンアップ
    db.conn.close()
    KuzuDB._instance = None


# 保存されたJSONファイルのパスを取得
TEST_DATA_DIR = Path(__file__).parent / "test_data" / "context_linking_inputs"
json_files = list(TEST_DATA_DIR.glob("*.json"))


@pytest.mark.asyncio
@pytest.mark.parametrize("json_file", json_files, ids=[f.name for f in json_files])
async def test_execute_context_linking_with_json(json_file: Path, temp_kuzu_db: KuzuDB) -> None:
    """
    各JSONファイルを読み込み、コンテキスト統合とDB保存処理が正常に動作するかをテストする。
    """
    # JSONの読み込みとパース
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    raw_graph = ExtractionResult.model_validate(data)

    # モックとリポジトリの準備
    mock_llm = MockLLMService()
    repo = KuzuGraphRepository(temp_kuzu_db)
    usecase = GenerateOntologyUseCase(llm_service=mock_llm, graph_repository=repo)

    # 実行
    text_content = "dummy text content for anchor extraction"
    final_graph = await usecase.execute_context_linking(raw_graph, text_content)

    # 基本的な検証: 返却されたグラフのノード数が元データと同じ以上であること
    assert len(final_graph.nodes) >= len(raw_graph.nodes)

    # 未分類概念 (UnclassifiedConcept) が存在する場合の固有ルールの検証
    has_unclassified = any(node.properties.get("type") == "ap:UnclassifiedConcept" for node in raw_graph.nodes)
    if has_unclassified:
        # 進化フラグが立つこと
        assert final_graph.needs_evolution is True
        # 未分類概念ノードに status="pending" が付与されていること
        for node in final_graph.nodes:
            if node.properties.get("type") == "ap:UnclassifiedConcept":
                assert node.properties.get("status") == "pending"
    else:
        # フラグが立たないこと
        assert final_graph.needs_evolution is False

    # ========== DBにデータが正しく保存されたことの検証 ==========
    conn = temp_kuzu_db.get_connection()

    # 共有DBになっているため、このテストケースで追加されたノード/エッジの数のみを検証する
    node_ids = [n.id for n in final_graph.nodes]

    # ノードがDBに保存されているか確認
    res_node_count: Any = conn.execute(
        "MATCH (n:Entity) WHERE n.id IN $ids RETURN COUNT(n)", parameters={"ids": node_ids}
    )
    node_count_result = res_node_count.get_next()
    assert node_count_result[0] == len(final_graph.nodes), "DBに保存されたノード数が一致しません"

    # エッジがDBに保存されているか確認
    # 実際に保存されるべき有効なエッジの数を事前に計算して比較する
    saved_node_ids = {n.id for n in final_graph.nodes}
    valid_edge_count = sum(
        1 for e in final_graph.edges if e.source_id in saved_node_ids and e.target_id in saved_node_ids
    )

    res_edge_count: Any = conn.execute(
        "MATCH (src:Entity)-[r:Relation]->(dst:Entity) WHERE src.id IN $ids AND dst.id IN $ids RETURN COUNT(r)",
        parameters={"ids": node_ids},
    )
    edge_count_result = res_edge_count.get_next()
    assert edge_count_result[0] >= valid_edge_count, "DBに保存されたエッジ数が不足しています"

    # status="pending" となっているノードがDB上でも正しく保存されているか確認
    if has_unclassified:
        res_pending_nodes: Any = conn.execute(
            "MATCH (n:Entity) WHERE n.id IN $ids AND "
            'n.properties_json CONTAINS \'"status": "pending"\' RETURN COUNT(n)',
            parameters={"ids": node_ids},
        )
        pending_nodes_result = res_pending_nodes.get_next()
        expected_pending_count = sum(1 for node in final_graph.nodes if node.properties.get("status") == "pending")
        assert pending_nodes_result[0] == expected_pending_count, "DB上のpendingノード数が一致しません"
