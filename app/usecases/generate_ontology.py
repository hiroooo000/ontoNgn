from app.domain.models.graph import ExtractionResult
from app.domain.services.graph_repository import IGraphRepository
from app.domain.services.text_llm_service import ITextLLMService


class GenerateOntologyUseCase:
    def __init__(self, llm_service: ITextLLMService, graph_repository: IGraphRepository):
        self.llm_service = llm_service
        self.graph_repository = graph_repository

    async def execute(self, text_content: str) -> ExtractionResult:
        # 1. LLMを用いてテキストからオントロジー（ノード・エッジ）を抽出
        result = await self.llm_service.generate_ontology(text_content)

        # 2. 抽出されたノードをデータベースへ保存
        for node in result.nodes:
            await self.graph_repository.save_node(node)

        # 3. 抽出されたエッジをデータベースへ保存
        for edge in result.edges:
            await self.graph_repository.save_edge(edge)

        return result
