import sys

from playwright.sync_api import TimeoutError, sync_playwright


def run_e2e_test():
    print("=== Graph UI E2E Manual Test (Playwright) ===")
    url = "http://127.0.0.1:8000/graph"

    with sync_playwright() as p:
        try:
            print("Launching browser...")
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            print(f"Navigating to {url} ...")
            page.goto(url)

            print("Waiting for network container to render...")
            page.wait_for_selector("div.w-full.h-screen.absolute", timeout=5000)
            print("✅ SUCCESS: Network container rendered.")

            print("Waiting for search form...")
            page.wait_for_selector('input[type="text"][placeholder="Keyword..."]', timeout=5000)
            print("✅ SUCCESS: Search form rendered.")

            # Interact with search
            print("Simulating search interaction...")
            page.fill('input[type="text"][placeholder="Keyword..."]', "test-query")
            page.click('button[type="submit"]')

            # Wait for loading indicator (might be fast, just check if no errors occurred)
            print("✅ SUCCESS: Search submitted without errors.")

            browser.close()
            print("=== E2E Test Complete: All checks passed! ===")

        except TimeoutError as e:
            print(f"❌ ERROR: Element not found within timeout. Details: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ ERROR: Connection failed or unexpected error. Is the server running? Details: {e}")
            sys.exit(1)


if __name__ == "__main__":
    run_e2e_test()
