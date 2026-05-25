from abc import ABC, abstractmethod
from typing import Any, List, Optional

from app.domain.models.graph import ExtractionResult, GraphEdge, GraphNode


class IGraphRepository(ABC):
    @abstractmethod
    async def save_node(self, node: GraphNode) -> None:
        """ノードを永続化（作成または更新）します。"""
        pass

    @abstractmethod
    async def save_edge(self, edge: GraphEdge) -> None:
        """エッジを永続化（作成または更新）します。"""
        pass

    @abstractmethod
    async def get_node(self, node_id: str) -> Optional[GraphNode]:
        """一意なID (URI) からノードを取得します。"""
        pass

    @abstractmethod
    async def query_neighbors(self, node_id: str) -> List[GraphEdge]:
        """対象ノードに隣接するエッジ群を取得します。"""
        pass

    @abstractmethod
    async def export_all(self) -> ExtractionResult:
        """全ノード・エッジの集合を取得します。"""
        pass

    @abstractmethod
    async def find_nodes_by_type(self, label_type: str) -> List[GraphNode]:
        """指定されたクラス・タイプ（例：ap:UnclassifiedConcept）の全ノードを取得します。"""
        pass

    @abstractmethod
    async def get_schema_definition(self) -> dict[str, Any]:
        """現在データベースに適用されているスキーマ定義メタデータを取得します。"""
        pass
