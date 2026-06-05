import asyncio
import json

import httpx

BASE_URL = "http://localhost:8000"


async def run_manual_test() -> None:
    print("Starting manual test for Ontology Ingest Flow...")

    # 1. Generate Ontology
    print("\n[Step 1] Calling POST /api/v1/ontology/generate")
    text_input = "The quick brown fox jumps over the lazy dog."

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/ontology/generate", content=text_input, headers={"Content-Type": "text/plain"}
            )
        except httpx.ConnectError:
            print("Failed to connect to the server. Is it running? (uv run uvicorn app.main:app --reload)")
            return
            
        if response.status_code != 200:
            print(f"Failed to generate ontology: {response.status_code}")
            print(response.text)
            return

        extraction_result = response.json()
        nodes_len = len(extraction_result.get("nodes", []))
        edges_len = len(extraction_result.get("edges", []))
        print(f"Success! Extracted {nodes_len} nodes and {edges_len} edges.")

        if not extraction_result.get("nodes"):
            print("No nodes extracted, ending test early.")
            return

        # 2. Ingest Ontology into GraphDB
        print("\n[Step 2] Calling POST /api/v1/graph/ingest")
        ingest_response = await client.post(f"{BASE_URL}/api/v1/graph/ingest", json=extraction_result)
        if ingest_response.status_code != 200:
            print(f"Failed to ingest ontology: {ingest_response.status_code}")
            print(ingest_response.text)
            return

        ingest_data = ingest_response.json()
        print(f"Success! Ingest response: {json.dumps(ingest_data, indent=2)}")

        # 3. Verify by fetching the first node
        first_node_id = extraction_result["nodes"][0]["id"]
        print(f"\n[Step 3] Verifying node creation. Calling GET /api/v1/graph/nodes/{first_node_id}")

        get_response = await client.get(f"{BASE_URL}/api/v1/graph/nodes/{first_node_id}")
        if get_response.status_code == 200:
            print("Success! Node retrieved successfully:")
            print(json.dumps(get_response.json(), indent=2))
        else:
            print(f"Failed to retrieve node: {get_response.status_code}")
            print(get_response.text)

        # 4. Clean up the node
        print(f"\n[Step 4] Cleaning up. Calling DELETE /api/v1/graph/nodes/{first_node_id}")
        delete_response = await client.delete(f"{BASE_URL}/api/v1/graph/nodes/{first_node_id}")
        if delete_response.status_code == 200:
            print("Success! Node deleted successfully.")
        else:
            print(f"Failed to delete node: {delete_response.status_code}")

    print("\nManual test completed successfully.")


if __name__ == "__main__":
    asyncio.run(run_manual_test())
