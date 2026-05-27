from abc import ABC, abstractmethod

from app.domain.models.graph import ExtractionResult, GraphNode


class ITextLLMService(ABC):
    @abstractmethod
    async def generate_ontology(self, text_content: str) -> ExtractionResult:
        """構造化テキストからオントロジーデータを抽出"""
        pass

    @abstractmethod
    async def extract_anchor_keywords(self, text_content: str) -> list[str]:
        """テキストから中心概念（アンカーキーワード）を抽出"""
        pass

    @abstractmethod
    async def validate_anchor(self, text_content: str, candidate_node: GraphNode) -> bool:
        """テキスト内容と既存ノード候補が関連しているかを検証"""
        pass

    @abstractmethod
    async def generate_links(self, new_graph: ExtractionResult, context_subgraph: ExtractionResult) -> ExtractionResult:
        """新規オントロジーと既存サブグラフを統合推論し、リンク（エッジ）を生成"""
        pass
