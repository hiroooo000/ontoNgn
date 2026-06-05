from app.domain.models.graph import ExtractionResult
from app.domain.services.text_llm_service import ITextLLMService


class GenerateOntologyUseCase:
    def __init__(self, llm_service: ITextLLMService) -> None:
        self.llm_service = llm_service

    async def execute(self, text_content: str) -> ExtractionResult:
        # Step 1: LLMによる生データの抽出
        result = await self.llm_service.generate_ontology(text_content)

        # Step 2: 未分類概念の判定
        has_unclassified = any(node.properties.get("type") == "ap:UnclassifiedConcept" for node in result.nodes)

        if has_unclassified:
            result.needs_evolution = True
            for node in result.nodes:
                if node.properties.get("type") == "ap:UnclassifiedConcept":
                    node.properties["status"] = "pending"

        return result
