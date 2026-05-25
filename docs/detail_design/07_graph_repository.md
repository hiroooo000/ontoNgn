# 07. Graph Repository 詳細設計

特定データベース（Neo4j, Apache AGE, Kùzu等）への依存を排除するため、ドメイン層に共通インターフェースを定義し、FastAPI の Dependency Injection システムにより動的にバインドします。

## 1. リポジトリインターフェース (`app/domain/services/graph_repository.py`)

```python
from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.models.graph import GraphNode, GraphEdge, ExtractionResult

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
    async def get_schema_definition(self) -> dict:
        """現在データベースに適用されているスキーマ定義メタデータを取得します。"""
        pass
```

## 2. 依存性注入（DI）定義 (`app/core/dependencies.py`)

環境変数 `GRAPH_DB_TYPE` を用いて、実行時に有効にする具象リポジトリを決定します。

```python
from fastapi import Depends
from app.core.config import get_settings, Settings
from app.domain.services.graph_repository import IGraphRepository
from app.interfaces.gateways.neo4j_repository import Neo4jGraphRepository
from app.interfaces.gateways.age_repository import AgeGraphRepository
from app.interfaces.gateways.kuzu_repository import KuzuGraphRepository
from app.interfaces.gateways.rdf_repository import InMemoryRdfRepository

def get_graph_repository(settings: Settings = Depends(get_settings)) -> IGraphRepository:
    db_type = settings.graph_db_type.lower()
    
    if db_type == 'neo4j':
        return Neo4jGraphRepository(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password
        )
    elif db_type == 'apache_age':
        return AgeGraphRepository(dsn=settings.postgres_dsn)
    elif db_type == 'kuzu':
        return KuzuGraphRepository(db_path=settings.kuzu_db_path)
    else:
        # デフォルトはインメモリRDF（N3 / rdflib）
        return InMemoryRdfRepository(output_path=settings.rdf_output_path)
```
