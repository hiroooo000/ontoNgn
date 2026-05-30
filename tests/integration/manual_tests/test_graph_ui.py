import asyncio

import httpx


async def main() -> None:
    print("=== Graph UI Manual Integration Test ===")

    url = "http://127.0.0.1:8000/graph"
    print(f"Testing GET {url} ...")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)

            if response.status_code == 200:
                print("✅ SUCCESS: Received 200 OK")
                print(f"Content-Type: {response.headers.get('content-type')}")

                # Check for key Vite HTML markers instead of vis-network
                if 'id="app"' in response.text:
                    print('✅ SUCCESS: Found Vue app container <div id="app"></div>')
                else:
                    print("❌ ERROR: Could not find Vue app container in HTML")
            else:
                print(f"❌ ERROR: Received status code {response.status_code}")

    except httpx.ConnectError:
        print("❌ ERROR: Connection failed. Make sure the FastAPI server is running (e.g., `uv run task start-devsv`)")

    print("=== Test Complete ===")


if __name__ == "__main__":
    asyncio.run(main())
