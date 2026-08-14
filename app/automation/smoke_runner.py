from playwright.sync_api import sync_playwright


def run_smoke_tests(url: str) -> dict:
    """
    Runs a basic browser smoke test against a target URL.
    """

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()

        response = page.goto(url, wait_until="domcontentloaded")

        result = {
            "url": url,
            "final_url": page.url,
            "title": page.title(),
            "status_code": response.status if response else None,
            "success": response.ok if response else False,
        }

        browser.close()
        return result


if __name__ == "__main__":
    smoke_result = run_smoke_tests("https://example.com")
    print(smoke_result)