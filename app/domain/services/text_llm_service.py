from abc import ABC, abstractmethod

from app.domain.models.graph import ExtractionResult


class ITextLLMService(ABC):
    @abstractmethod
    async def generate_ontology(self, text_content: str) -> ExtractionResult:
        """構造化テキストからオントロジーデータを抽出"""
        pass
