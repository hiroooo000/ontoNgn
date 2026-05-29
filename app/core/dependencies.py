from typing import Any, List, Optional

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.domain.models.graph import ExtractionResult, GraphEdge, GraphNode
from app.domain.services.graph_repository import IGraphRepository
from app.domain.services.text_llm_service import ITextLLMService
from app.infrastructure.database.kuzu_db import KuzuDB
from app.interfaces.gateways.lmstudio_gateway import LMStudioGateway
from app.interfaces.repositories.kuzu_graph_repository import KuzuGraphRepository


def get_text_llm_service(settings: Settings = Depends(get_settings)) -> ITextLLMService:
    return LMStudioGateway(settings=settings)


class DummyGraphRepository(IGraphRepository):
    async def save_node(self, node: GraphNode) -> None:
        pass

    async def save_edge(self, edge: GraphEdge) -> None:
        pass

    async def get_node(self, node_id: str) -> Optional[GraphNode]:
        return None

    async def query_neighbors(self, node_id: str) -> List[GraphEdge]:
        return []

    async def export_all(self) -> ExtractionResult:
        return ExtractionResult(nodes=[], edges=[])

    async def find_nodes_by_type(self, label_type: str) -> List[GraphNode]:
        return []

    async def get_schema_definition(self) -> dict[str, Any]:
        return {}

    async def delete_document_graph(self, document_id: str) -> None:
        pass

    async def search_nodes_by_keywords(self, keywords: List[str], top_k: int) -> List[GraphNode]:
        return []

    async def get_subgraph(self, anchor_ids: List[str], max_hops: int) -> ExtractionResult:
        return ExtractionResult(nodes=[], edges=[])


def get_graph_repository(settings: Settings = Depends(get_settings)) -> IGraphRepository:
    db = KuzuDB(settings=settings)
    return KuzuGraphRepository(db=db)
