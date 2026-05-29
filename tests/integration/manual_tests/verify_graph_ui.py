import asyncio

from app.core.config import get_settings
from app.domain.models.graph import GraphEdge, GraphNode
from app.infrastructure.database.kuzu_db import KuzuDB
from app.interfaces.repositories.kuzu_graph_repository import KuzuGraphRepository


async def main() -> None:
    print("Graph UI Verification Script")
    print("============================")

    settings = get_settings()
    db_path = settings.kuzu_db_path
    print(f"Using Kuzu DB Path: {db_path}")

    db = KuzuDB(settings=settings)
    repo = KuzuGraphRepository(db=db)

    try:
        # Dummy nodes
        node1 = GraphNode(id="doc_1", label="Document", properties={"name": "test_document.txt", "type": "file"})
        node2 = GraphNode(
            id="concept_1",
            label="ap:UnclassifiedConcept",
            properties={"name": "test_concept", "description": "This is a test concept"},
        )
        node3 = GraphNode(
            id="concept_2",
            label="ap:UnclassifiedConcept",
            properties={"name": "another_concept", "description": "Another one"},
        )

        print("Inserting dummy nodes...")
        await repo.save_node(node1)
        await repo.save_node(node2)
        await repo.save_node(node3)

        # Dummy edges
        edge1 = GraphEdge(
            source_id="doc_1", target_id="concept_1", relation_type="contains", properties={"confidence": 0.95}
        )
        edge2 = GraphEdge(
            source_id="concept_1", target_id="concept_2", relation_type="related_to", properties={"strength": "high"}
        )

        print("Inserting dummy edges...")
        await repo.save_edge(edge1)
        await repo.save_edge(edge2)

        print("\nDummy data setup complete!")
        print("\n--- Manual Verification Steps ---")
        print("1. Start the development server if not already running:")
        print("   $ uv run task start-devsv")
        print("2. Open your browser and navigate to:")
        print("   http://localhost:8000/graph")
        print("3. In the left pane, search for 'test'.")
        print("4. Verify that you see nodes connected by edges.")
        print("5. Click on 'test_concept' or 'test_document.txt' and verify the properties appear in the left pane.")

    except Exception as e:
        print(f"Error during setup: {e}")


if __name__ == "__main__":
    asyncio.run(main())
