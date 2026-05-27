import asyncio
import os
import shutil
import sys

# プロジェクトのルートディレクトリをパスに追加してappモジュールを読み込めるようにする
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from app.core.config import Settings
from app.domain.models.graph import GraphEdge, GraphNode
from app.infrastructure.database.kuzu_db import KuzuDB
from app.interfaces.repositories.kuzu_graph_repository import KuzuGraphRepository


async def main() -> None:
    # 1. 一時的なDBをセットアップ
    test_db_dir = "./test_manual_kuzu_db"
    test_db_path = f"{test_db_dir}/test.db"

    # 既存のテストDBがあれば削除してクリーンな状態にする
    if os.path.exists(test_db_dir):
        shutil.rmtree(test_db_dir)

    settings = Settings(kuzu_db_path=test_db_path)

    # KuzuDBはシングルトンのため、一度_instanceをクリア（テスト用）
    KuzuDB._instance = None
    db = KuzuDB(settings=settings)
    repo = KuzuGraphRepository(db)

    print("=== KuzuGraphRepository 手動テスト ===")

    # 2. ノードの保存と取得
    print("\n1. ノードを作成しています...")
    node1 = GraphNode(
        id="ap:Node1", label="Concept", properties={"name": "Artificial Intelligence", "sourceDocumentIds": ["doc1"]}
    )
    node2 = GraphNode(
        id="ap:Node2", label="Concept", properties={"name": "Machine Learning", "sourceDocumentIds": ["doc1"]}
    )

    await repo.save_node(node1)
    await repo.save_node(node2)

    saved_node = await repo.get_node("ap:Node1")
    assert saved_node is not None
    print(f"取得したノード: {saved_node.id} - Properties: {saved_node.properties}")

    # 3. エッジ（リレーション）の保存
    print("\n2. エッジを作成しています (Node1 -> Node2)...")
    edge = GraphEdge(source_id="ap:Node1", target_id="ap:Node2", relation_type="includes", properties={"weight": 1.0})
    await repo.save_edge(edge)

    # 4. キーワード検索
    print("\n3. キーワード 'Machine' で検索しています...")
    search_results = await repo.search_nodes_by_keywords(["Machine"], top_k=5)
    for res in search_results:
        print(f"検索ヒット: {res.id} - {res.properties}")

    # 5. 部分グラフ(Subgraph)の取得
    print("\n4. Node1からの部分グラフ（1ホップ）を取得しています...")
    subgraph = await repo.get_subgraph(["ap:Node1"], max_hops=1)
    print(f"部分グラフ ノード数: {len(subgraph.nodes)}")
    print(f"部分グラフ エッジ数: {len(subgraph.edges)}")
    for e in subgraph.edges:
        print(f"  Edge: {e.source_id} -[{e.relation_type}]-> {e.target_id}")

    # 6. ドキュメントグラフの削除
    print("\n5. ドキュメント 'doc1' に紐づくグラフを削除しています...")
    await repo.delete_document_graph("doc1")

    deleted_node = await repo.get_node("ap:Node1")
    print(f"削除後のNode1 (Noneになるはずです): {deleted_node}")

    print("\n=== テスト終了 ===")

    # クリーンアップ
    if os.path.exists(test_db_dir):
        shutil.rmtree(test_db_dir)
        print(f"\nテスト用DB '{test_db_dir}' を削除しました。")


if __name__ == "__main__":
    asyncio.run(main())
