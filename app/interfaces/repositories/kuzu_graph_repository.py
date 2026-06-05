import json
from typing import Any, List, Optional

from app.domain.models.graph import ExtractionResult, GraphEdge, GraphNode
from app.domain.services.graph_repository import IGraphRepository
from app.infrastructure.database.kuzu_db import KuzuDB


class KuzuGraphRepository(IGraphRepository):
    def __init__(self, db: KuzuDB) -> None:
        self.conn = db.get_connection()

    async def save_node(self, node: GraphNode) -> None:
        # MERGE (n:Entity {id: $id})
        # ON MATCH SET n.label = $label, n.properties_json = $props
        # ON CREATE SET n.label = $label, n.properties_json = $props
        query = """
        MERGE (n:Entity {id: $id})
        ON MATCH SET n.label = $label, n.properties_json = $props, n.sourceDocumentIds = $doc_ids
        ON CREATE SET n.label = $label, n.properties_json = $props, n.sourceDocumentIds = $doc_ids
        """
        params = {
            "id": node.id,
            "label": node.label,
            "props": json.dumps(node.properties, ensure_ascii=False),
            "doc_ids": [],  # We can implement sourceDocumentIds later if needed
        }
        self.conn.execute(query, parameters=params)

    async def get_node(self, node_id: str) -> Optional[GraphNode]:
        query = "MATCH (n:Entity {id: $id}) RETURN n.label, n.properties_json"
        res: Any = self.conn.execute(query, parameters={"id": node_id})

        if not res.has_next():
            return None

        row: Any = res.get_next()
        label = row[0]
        properties = json.loads(row[1]) if row[1] else {}
        return GraphNode(id=node_id, label=label, properties=properties)

    async def save_edge(self, edge: GraphEdge) -> None:
        # MERGE (src:Entity {id: $src_id})-[r:Relation {relation_type: $rel_type}]->(dst:Entity {id: $dst_id})
        # Note: In Kuzu, MATCHing nodes first then MERGEing rel is standard if you don't want to create nodes.
        # But for upserting edge properties:
        query = """
        MATCH (src:Entity {id: $src_id})
        MATCH (dst:Entity {id: $dst_id})
        MERGE (src)-[r:Relation {relation_type: $rel_type}]->(dst)
        ON MATCH SET r.properties_json = $props
        ON CREATE SET r.properties_json = $props
        """
        params = {
            "src_id": edge.source_id,
            "dst_id": edge.target_id,
            "rel_type": edge.relation_type,
            "props": json.dumps(edge.properties, ensure_ascii=False),
        }
        self.conn.execute(query, parameters=params)

    async def query_neighbors(self, node_id: str) -> List[GraphEdge]:
        query = """
        MATCH (src:Entity {id: $id})-[r:Relation]->(dst:Entity)
        RETURN src.id, dst.id, r.relation_type, r.properties_json
        """
        res: Any = self.conn.execute(query, parameters={"id": node_id})
        edges = []
        while res.has_next():
            row: Any = res.get_next()
            src = row[0]
            dst = row[1]
            rel_type = row[2]
            props = json.loads(row[3]) if row[3] else {}
            edges.append(GraphEdge(source_id=src, target_id=dst, relation_type=rel_type, properties=props))
        return edges

    async def export_all(self) -> ExtractionResult:
        nodes = []
        res_nodes: Any = self.conn.execute("MATCH (n:Entity) RETURN n.id, n.label, n.properties_json")
        while res_nodes.has_next():
            r: Any = res_nodes.get_next()
            nodes.append(GraphNode(id=r[0], label=r[1], properties=json.loads(r[2]) if r[2] else {}))

        edges = []
        query_edges = (
            "MATCH (src:Entity)-[r:Relation]->(dst:Entity) RETURN src.id, dst.id, r.relation_type, r.properties_json"
        )
        res_edges: Any = self.conn.execute(query_edges)
        while res_edges.has_next():
            r_edge: Any = res_edges.get_next()
            edges.append(
                GraphEdge(
                    source_id=r_edge[0],
                    target_id=r_edge[1],
                    relation_type=r_edge[2],
                    properties=json.loads(r_edge[3]) if r_edge[3] else {},
                )
            )

        return ExtractionResult(nodes=nodes, edges=edges)

    async def find_nodes_by_type(self, label_type: str) -> List[GraphNode]:
        query = "MATCH (n:Entity {label: $label}) RETURN n.id, n.label, n.properties_json"
        res: Any = self.conn.execute(query, parameters={"label": label_type})
        nodes = []
        while res.has_next():
            r: Any = res.get_next()
            nodes.append(GraphNode(id=r[0], label=r[1], properties=json.loads(r[2]) if r[2] else {}))
        return nodes

    async def get_schema_definition(self) -> dict[str, Any]:
        schema: dict[str, list[str]] = {"node_tables": [], "rel_tables": []}
        res: Any = self.conn.execute("CALL show_tables() RETURN *")
        while res.has_next():
            row: Any = res.get_next()
            table_name = row[1]
            table_type = row[2]
            if table_type == "NODE":
                schema["node_tables"].append(table_name)
            elif table_type == "REL":
                schema["rel_tables"].append(table_name)
        return schema

    async def delete_document_graph(self, document_id: str) -> None:
        # In Kuzu, filtering by JSON properties is limited, but assuming properties_json
        # contains sourceDocumentIds. A proper way is to pull nodes, modify/delete,
        # then write back if Kuzu doesn't support json array operations well.
        # But we will do a simple MATCH to find nodes that have this document_id
        # For a robust implementation, we fetch all nodes, update properties, and delete if empty
        nodes = []
        res: Any = self.conn.execute("MATCH (n:Entity) RETURN n.id, n.label, n.properties_json")
        while res.has_next():
            row: Any = res.get_next()
            nodes.append((row[0], row[1], json.loads(row[2]) if row[2] else {}))

        for node_id, label, props in nodes:
            doc_ids = props.get("sourceDocumentIds", [])
            if document_id in doc_ids:
                doc_ids.remove(document_id)
                if not doc_ids:
                    # Delete the node entirely
                    self.conn.execute("MATCH (n:Entity {id: $id}) DETACH DELETE n", parameters={"id": node_id})
                else:
                    # Update properties
                    props["sourceDocumentIds"] = doc_ids
                    self.conn.execute(
                        "MATCH (n:Entity {id: $id}) SET n.properties_json = $props",
                        parameters={"id": node_id, "props": json.dumps(props, ensure_ascii=False)},
                    )

        # Edges should similarly be deleted, but DETACH DELETE takes care of edges connected to deleted nodes.
        # If edges also have sourceDocumentIds, we'd need similar logic.

    async def search_nodes_by_keywords(self, keywords: List[str], top_k: int) -> List[GraphNode]:
        # Very naive implementation for local Kuzu DB: fetch all and filter in Python
        # Real implementation would use Kuzu's full-text search extension or vector search
        nodes = []
        res: Any = self.conn.execute("MATCH (n:Entity) RETURN n.id, n.label, n.properties_json")
        while res.has_next():
            row: Any = res.get_next()
            node_id = row[0]
            label = row[1]
            props = json.loads(row[2]) if row[2] else {}

            # Simple keyword matching across all string property values
            text_content = " ".join(str(v) for v in props.values()).lower()
            if any(kw.lower() in text_content for kw in keywords):
                nodes.append(GraphNode(id=node_id, label=label, properties=props))
                if len(nodes) >= top_k:
                    break
        return nodes

    async def get_subgraph(self, anchor_ids: List[str], max_hops: int) -> ExtractionResult:
        nodes = {}
        edges = []

        for anchor_id in anchor_ids:
            # Recursive CTE equivalent in cypher (using variable length paths)
            query = f"""
            MATCH p = (n:Entity {{id: $id}})-[r:Relation*1..{max_hops}]-(m:Entity)
            RETURN nodes(p), rels(p)
            """
            try:
                res: Any = self.conn.execute(query, parameters={"id": anchor_id})
                while res.has_next():
                    res.get_next()
                    # Due to Kuzu python API structure, path_nodes and path_rels might be returned differently.
                    # We will implement a simplified 1-hop fallback if complex path fails:
            except Exception:
                # Fallback to simple 1 hop logic for max_hops=1 to keep it robust
                # (For production, Kuzu paths parsing would be fully implemented)
                pass

            # BFS to find all nodes up to max_hops
            current_level = {anchor_id}
            visited_nodes = set()

            for _ in range(max_hops):
                next_level = set()
                for nid in current_level:
                    if nid in visited_nodes:
                        continue
                    visited_nodes.add(nid)

                    # Fetch neighbors using undirected match to traverse
                    query_neighbors = "MATCH (src:Entity {id: $nid})-[r:Relation]-(dst:Entity) RETURN dst.id"
                    res_n: Any = self.conn.execute(query_neighbors, parameters={"nid": nid})
                    while res_n.has_next():
                        rn: Any = res_n.get_next()
                        next_level.add(rn[0])
                current_level = next_level

            # Add the last level to visited
            visited_nodes.update(current_level)

            # Fetch all nodes
            for nid in visited_nodes:
                node = await self.get_node(nid)
                if node:
                    nodes[node.id] = node

        # Fetch all edges between the gathered nodes
        if nodes:
            node_ids = list(nodes.keys())
            query_edges = """
            MATCH (src:Entity)-[r:Relation]->(dst:Entity)
            WHERE src.id IN $node_ids AND dst.id IN $node_ids
            RETURN src.id, dst.id, r.relation_type, r.properties_json
            """
            res_e: Any = self.conn.execute(query_edges, parameters={"node_ids": node_ids})
            while res_e.has_next():
                re: Any = res_e.get_next()
                edge = GraphEdge(
                    source_id=re[0], target_id=re[1], relation_type=re[2], properties=json.loads(re[3]) if re[3] else {}
                )
                if edge not in edges:
                    edges.append(edge)

        return ExtractionResult(nodes=list(nodes.values()), edges=edges)

    async def delete_node(self, node_id: str) -> None:
        query = "MATCH (n:Entity {id: $id}) DETACH DELETE n"
        self.conn.execute(query, parameters={"id": node_id})

    async def delete_edge(self, source_id: str, target_id: str) -> None:
        query = """
        MATCH (src:Entity {id: $src_id})-[r:Relation]->(dst:Entity {id: $dst_id})
        DELETE r
        """
        self.conn.execute(query, parameters={"src_id": source_id, "dst_id": target_id})
