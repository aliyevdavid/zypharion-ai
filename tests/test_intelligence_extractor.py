from app.intelligence.extractor import analyze_page


def test_analyze_page_extracts_example_domain_metadata() -> None:
    result = analyze_page("https://example.com")

    assert result.success is True
    assert result.status_code == 200
    assert result.title == "Example Domain"
    assert result.final_url.startswith("https://example.com")
    assert result.metrics.load_time_ms >= 0

    assert any(
        heading.level == 1 and heading.text == "Example Domain"
        for heading in result.headings
    )

    assert len(result.links) >= 1
    assert result.links[0].href.startswith("https://")