from app.domain.models.graph import ExtractionResult
from app.domain.services.graph_repository import IGraphRepository
from app.domain.services.text_llm_service import ITextLLMService


class GenerateOntologyUseCase:
    def __init__(self, llm_service: ITextLLMService, graph_repository: IGraphRepository) -> None:
        self.llm_service = llm_service
        self.graph_repository = graph_repository

    async def execute(self, text_content: str) -> ExtractionResult:
        # Step 1: LLMによる生データの抽出
        raw_graph = await self.llm_service.generate_ontology(text_content)

        # Step 2: アンカーキーワードの抽出
        anchor_keywords = await self.llm_service.extract_anchor_keywords(text_content)

        # Step 3: アンカーキーワードから既存ノードを検索
        candidate_nodes = []
        if anchor_keywords:
            candidate_nodes = await self.graph_repository.search_nodes_by_keywords(anchor_keywords, top_k=3)

        # Step 4: 検索されたノード候補を検証
        valid_anchor_ids = []
        for candidate in candidate_nodes:
            is_valid = await self.llm_service.validate_anchor(text_content, candidate)
            if is_valid:
                valid_anchor_ids.append(candidate.id)

        # Step 5: サブグラフの取得
        context_subgraph = ExtractionResult(nodes=[], edges=[])
        if valid_anchor_ids:
            context_subgraph = await self.graph_repository.get_subgraph(valid_anchor_ids, max_hops=1)

        # Step 6: コンテキスト統合とリンク生成
        final_graph = await self.llm_service.generate_links(raw_graph, context_subgraph)

        # 未分類概念の判定
        has_unclassified = any(node.properties.get("type") == "ap:UnclassifiedConcept" for node in final_graph.nodes)

        if has_unclassified:
            final_graph.needs_evolution = True
            for node in final_graph.nodes:
                if node.properties.get("type") == "ap:UnclassifiedConcept":
                    node.properties["status"] = "pending"

        # 抽出されたノードとエッジを保存
        for node in final_graph.nodes:
            await self.graph_repository.save_node(node)
        for edge in final_graph.edges:
            await self.graph_repository.save_edge(edge)

        return final_graph
