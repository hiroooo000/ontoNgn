from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.dependencies import get_graph_repository
from app.domain.models.graph import ExtractionResult, GraphEdge, GraphNode
from app.domain.services.graph_repository import IGraphRepository
from app.usecases.graph_crud import GraphCrudUseCase

router = APIRouter()


def get_graph_crud_usecase(repo: IGraphRepository = Depends(get_graph_repository)) -> GraphCrudUseCase:
    return GraphCrudUseCase(repo)


@router.post("/ingest")
async def ingest_graph(
    extraction_result: ExtractionResult,
    usecase: GraphCrudUseCase = Depends(get_graph_crud_usecase),
) -> dict[str, Any]:
    try:
        await usecase.ingest_ontology(extraction_result)
        return {
            "status": "success",
            "nodes_upserted": len(extraction_result.nodes),
            "edges_upserted": len(extraction_result.edges),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/nodes")
async def create_or_update_node(
    node: GraphNode,
    usecase: GraphCrudUseCase = Depends(get_graph_crud_usecase),
) -> dict[str, str]:
    try:
        await usecase.create_or_update_node(node)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nodes/{node_id}")
async def get_node(
    node_id: str,
    repo: IGraphRepository = Depends(get_graph_repository),
) -> GraphNode:
    node = await repo.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node


@router.delete("/nodes/{node_id}")
async def delete_node(
    node_id: str,
    usecase: GraphCrudUseCase = Depends(get_graph_crud_usecase),
) -> dict[str, str]:
    try:
        await usecase.delete_node(node_id)
        return {"status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/edges")
async def create_or_update_edge(
    edge: GraphEdge,
    usecase: GraphCrudUseCase = Depends(get_graph_crud_usecase),
) -> dict[str, str]:
    try:
        await usecase.create_or_update_edge(edge)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/edges")
async def delete_edge(
    source_id: str = Query(...),
    target_id: str = Query(...),
    usecase: GraphCrudUseCase = Depends(get_graph_crud_usecase),
) -> dict[str, str]:
    try:
        await usecase.delete_edge(source_id, target_id)
        return {"status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
        return {"nodes": [], "edges": [], "hits": []}

    anchor_ids = [node.id for node in anchors]

    # アンカーを起点とするサブグラフを取得
    extraction_result = await repo.get_subgraph(anchor_ids=anchor_ids, max_hops=hops)

    # 戻り値の形式
    if hasattr(extraction_result, "nodes"):
        nodes = [n.model_dump() if hasattr(n, "model_dump") else n for n in extraction_result.nodes]
        edges = [e.model_dump() if hasattr(e, "model_dump") else e for e in extraction_result.edges]
        hits = [n.model_dump() if hasattr(n, "model_dump") else n for n in anchors]
        return {"nodes": nodes, "edges": edges, "hits": hits}

    if isinstance(extraction_result, dict):
        extraction_result["hits"] = [n.model_dump() if hasattr(n, "model_dump") else n for n in anchors]
        return extraction_result

    return {"nodes": [], "edges": [], "hits": []}


@router.get("/expand")
async def expand_graph(
    node_id: str = Query(..., description="起点となるノードID"),
    hops: int = Query(1, description="展開するホップ数"),
    repo: IGraphRepository = Depends(get_graph_repository),
) -> dict[str, list[Any]]:
    # 指定されたノードを起点とするサブグラフを取得
    extraction_result = await repo.get_subgraph(anchor_ids=[node_id], max_hops=hops)

    if hasattr(extraction_result, "nodes"):
        nodes = [n.model_dump() if hasattr(n, "model_dump") else n for n in extraction_result.nodes]
        edges = [e.model_dump() if hasattr(e, "model_dump") else e for e in extraction_result.edges]
        return {"nodes": nodes, "edges": edges}

    if isinstance(extraction_result, dict):
        return extraction_result

    return {"nodes": [], "edges": []}
