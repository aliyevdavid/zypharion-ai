from unittest.mock import MagicMock, patch

from app.automation.smoke_runner import run_smoke_tests


def test_smoke_runner_validates_navigation_status_and_title() -> None:
    response = MagicMock(status=200, ok=True)
    page = MagicMock(url="https://example.test/final")
    page.goto.return_value = response
    page.title.return_value = "Test Page"
    browser = MagicMock()
    browser.new_page.return_value = page
    playwright = MagicMock()
    playwright.chromium.launch.return_value = browser
    manager = MagicMock()
    manager.__enter__.return_value = playwright

    with patch(
        "app.automation.smoke_runner.sync_playwright",
        return_value=manager,
    ):
        result = run_smoke_tests("https://example.test")

    assert result["success"] is True
    assert result["status_code"] == 200
    assert result["title"] == "Test Page"
    assert result["final_url"] == "https://example.test/final"
    page.goto.assert_called_once_with(
        "https://example.test",
        wait_until="domcontentloaded",
    )
    browser.close.assert_called_once_with()
