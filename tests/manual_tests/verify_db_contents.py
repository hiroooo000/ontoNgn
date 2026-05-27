import asyncio
import json
from pathlib import Path
from typing import Any

from app.core.config import Settings
from app.domain.models.graph import ExtractionResult, GraphNode
from app.domain.services.text_llm_service import ITextLLMService
from app.infrastructure.database.kuzu_db import KuzuDB
from app.interfaces.repositories.kuzu_graph_repository import KuzuGraphRepository
from app.usecases.generate_ontology import GenerateOntologyUseCase


class MockLLMService(ITextLLMService):
    async def generate_ontology(self, text_content: str) -> ExtractionResult:
        raise NotImplementedError()

    async def extract_anchor_keywords(self, text_content: str) -> list[str]:
        return ["ダミーキーワード"]

    async def validate_anchor(self, text_content: str, candidate_node: GraphNode) -> bool:
        return True

    async def generate_links(self, new_graph: ExtractionResult, context_subgraph: ExtractionResult) -> ExtractionResult:
        return new_graph


async def main() -> None:
    print("=== DB格納の視覚的確認スクリプト ===")

    # テスト用データのパス
    json_path = Path("tests/integration/usecases/test_data/context_linking_inputs/case1_base_procedure.json")
    if not json_path.exists():
        print(f"エラー: テストデータが見つかりません ({json_path})")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    raw_graph = ExtractionResult.model_validate(data)

    # 実際のKuzuDBディレクトリを指定（実行後にファイルが残るので確認可能）
    db_path = "./test_manual_kuzu_db"
    settings = Settings(kuzu_db_path=db_path)

    # 念のためシングルトンをリセット
    KuzuDB._instance = None
    db = KuzuDB(settings=settings)
    repo = KuzuGraphRepository(db)
    mock_llm = MockLLMService()

    usecase = GenerateOntologyUseCase(llm_service=mock_llm, graph_repository=repo)

    print("\n[1] データをDBに格納しています...")
    text_content = "dummy text content"
    await usecase.execute_context_linking(raw_graph, text_content)
    print("格納完了！\n")

    print("[2] DBに直接Cypherクエリを発行し、格納されたデータを取得します...")
    conn = db.get_connection()

    # ノードの取得
    print("\n--- 【DB内のノード (一部抜粋)】 ---")
    res_nodes: Any = conn.execute("MATCH (n:Entity) RETURN n.id, n.label, n.properties_json LIMIT 5")  # type: ignore
    node_count = 0
    while res_nodes.has_next():
        row = res_nodes.get_next()
        print(f"ID: {row[0]:<25} | Label: {row[1]:<20} | Props: {row[2]}")
        node_count += 1

    res_total_nodes: Any = conn.execute("MATCH (n:Entity) RETURN COUNT(n)")  # type: ignore
    total_nodes = res_total_nodes.get_next()[0]
    print(f"-> 取得したノード計: {total_nodes} 件")

    # エッジの取得
    print("\n--- 【DB内のエッジ (一部抜粋)】 ---")
    res_edges: Any = conn.execute("MATCH (src)-[r:Relation]->(dst) RETURN src.id, r.relation_type, dst.id LIMIT 5")  # type: ignore
    edge_count = 0
    while res_edges.has_next():
        row = res_edges.get_next()
        print(f"Source: {row[0]:<15} -[{row[1]}]-> Target: {row[2]}")
        edge_count += 1

    res_total_edges: Any = conn.execute("MATCH ()-[r:Relation]->() RETURN COUNT(r)")  # type: ignore
    total_edges = res_total_edges.get_next()[0]
    print(f"-> 取得したエッジ計: {total_edges} 件")

    print("\n=== 視覚的確認完了 ===")


if __name__ == "__main__":
    asyncio.run(main())
