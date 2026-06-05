from app.domain.models.graph import ExtractionResult, GraphEdge, GraphNode
from app.domain.services.graph_repository import IGraphRepository


class GraphCrudUseCase:
    def __init__(self, graph_repository: IGraphRepository) -> None:
        self.graph_repository = graph_repository

    async def ingest_ontology(self, extraction_result: ExtractionResult) -> None:
        """
        抽出されたオントロジー（ノードおよびエッジのリスト）を一括でDBに保存（Upsert）します。
        """
        for node in extraction_result.nodes:
            await self.graph_repository.save_node(node)
        for edge in extraction_result.edges:
            await self.graph_repository.save_edge(edge)

    async def create_or_update_node(self, node: GraphNode) -> None:
        """単一のノードを作成または更新します。"""
        await self.graph_repository.save_node(node)

    async def delete_node(self, node_id: str) -> None:
        """指定したIDのノードを削除します。"""
        await self.graph_repository.delete_node(node_id)

    async def create_or_update_edge(self, edge: GraphEdge) -> None:
        """単一のエッジを作成または更新します。"""
        await self.graph_repository.save_edge(edge)

    async def delete_edge(self, source_id: str, target_id: str) -> None:
        """指定したsourceとtargetを持つエッジを削除します。"""
        await self.graph_repository.delete_edge(source_id, target_id)
