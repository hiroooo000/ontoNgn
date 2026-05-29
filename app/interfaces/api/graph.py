from typing import Any

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_graph_repository
from app.domain.services.graph_repository import IGraphRepository

router = APIRouter()


@router.get("/search")
async def search_graph(
    q: str = Query(..., description="検索キーワード"),
    hops: int = Query(1, description="展開するホップ数"),
    limit: int = Query(50, description="取得する最大アンカー数"),
    repo: IGraphRepository = Depends(get_graph_repository),
) -> dict[str, list[Any]]:
    # キーワードに合致するノードを検索
    anchors = await repo.search_nodes_by_keywords(keywords=[q], top_k=limit)

    if not anchors:
        return {"nodes": [], "edges": []}

    anchor_ids = [node.id for node in anchors]

    # アンカーを起点とするサブグラフを取得
    extraction_result = await repo.get_subgraph(anchor_ids=anchor_ids, max_hops=hops)

    # 戻り値の形式 (ExtractionResultはPydanticモデル)
    # kuzu_graph_repository.pyの実装によってはExtractionResultではなく辞書を返す可能性があるが、
    # 定義としては ExtractionResult を返すようになっている。

    # Pydanticモデルの場合はmodel_dump()、辞書の場合はそのまま返す
    if hasattr(extraction_result, "nodes"):
        nodes = [n.model_dump() if hasattr(n, "model_dump") else n for n in extraction_result.nodes]
        edges = [e.model_dump() if hasattr(e, "model_dump") else e for e in extraction_result.edges]
        return {"nodes": nodes, "edges": edges}

    if isinstance(extraction_result, dict):
        return extraction_result

    return {"nodes": [], "edges": []}
