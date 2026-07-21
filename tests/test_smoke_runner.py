from app.automation.smoke_runner import run_smoke_tests


def test_smoke_runner_returns_success_for_example_dot_com() -> None:
    result = run_smoke_tests("https://example.com")

    assert result["success"] is True
    assert result["status_code"] == 200
    assert result["title"] == "Example Domain"
    assert result["final_url"].startswith("https://example.com")