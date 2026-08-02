from app.intelligence.analysis_models import PageType
from app.intelligence.analyzer import analyze_browser_intelligence
from app.intelligence.models import (
    BrowserIntelligenceResult,
    ButtonInfo,
    ExtractionWarning,
    FormInfo,
    HeadingInfo,
    ImageInfo,
    InputInfo,
    PageMetrics,
)


def _build_result(
    *,
    title: str = "Test Page",
    headings: list[HeadingInfo] | None = None,
    forms: list[FormInfo] | None = None,
    buttons: list[ButtonInfo] | None = None,
    inputs: list[InputInfo] | None = None,
    images: list[ImageInfo] | None = None,
    console_errors: list[str] | None = None,
) -> BrowserIntelligenceResult:
    return BrowserIntelligenceResult(
        requested_url="https://example.com",
        final_url="https://example.com/",
        title=title,
        status_code=200,
        success=True,
        headings=headings or [],
        forms=forms or [],
        buttons=buttons or [],
        inputs=inputs or [],
        images=images or [],
        console_errors=console_errors or [],
        metrics=PageMetrics(load_time_ms=100),
    )


def test_analyzer_classifies_authentication_page() -> None:
    browser_result = _build_result(
        title="Sign In",
        forms=[FormInfo(action="/login", method="post")],
        buttons=[ButtonInfo(text="Login", button_type="submit")],
        inputs=[
            InputInfo(
                name="username",
                input_type="text",
                required=True,
            ),
            InputInfo(
                name="password",
                input_type="password",
                required=True,
            ),
        ],
    )

    analysis = analyze_browser_intelligence(browser_result)

    assert analysis.classification.page_type == PageType.AUTHENTICATION
    assert analysis.classification.confidence > 0.5
    assert "Password input detected" in analysis.classification.evidence
    assert "password_input" in analysis.detected_features
    assert "forms" in analysis.detected_features


def test_analyzer_classifies_search_page() -> None:
    browser_result = _build_result(
        title="Search",
        inputs=[
            InputInfo(
                name="query",
                input_type="search",
                placeholder="Search products",
            )
        ],
        buttons=[
            ButtonInfo(
                text="Search",
                button_type="submit",
            )
        ],
    )

    analysis = analyze_browser_intelligence(browser_result)

    assert analysis.classification.page_type == PageType.SEARCH
    assert "search_input" in analysis.detected_features


def test_analyzer_reports_missing_image_alt_text() -> None:
    browser_result = _build_result(
        images=[
            ImageInfo(
                src="https://example.com/image.png",
                alt=None,
            )
        ]
    )

    analysis = analyze_browser_intelligence(browser_result)

    assert any(
        finding.category == "accessibility"
        and finding.severity == "warning"
        for finding in analysis.findings
    )

    assert "Run a dedicated accessibility audit" in (
        analysis.recommendations
    )


def test_analyzer_reports_console_errors() -> None:
    browser_result = _build_result(
        console_errors=["ReferenceError: value is not defined"]
    )

    analysis = analyze_browser_intelligence(browser_result)

    assert "console_errors" in analysis.detected_features

    assert any(
        finding.category == "reliability"
        for finding in analysis.findings
    )

    assert (
        "Investigate browser console errors before release"
        in analysis.recommendations
    )


def test_analyzer_uses_unknown_when_no_signals_exist() -> None:
    browser_result = _build_result(
        title="",
    )

    analysis = analyze_browser_intelligence(browser_result)

    assert analysis.classification.page_type == PageType.UNKNOWN
    assert analysis.classification.confidence == 0.25
    assert analysis.classification.evidence == [
        "No strong classification signals detected"
    ]


def test_analyzer_accepts_browser_result_with_extraction_warning() -> None:
    browser_result = _build_result(title="Documentation")
    browser_result.warnings.append(
        ExtractionWarning(
            category="links",
            code="links_extraction_failed",
            message="Link content could not be extracted.",
        )
    )

    analysis = analyze_browser_intelligence(browser_result)

    assert analysis.classification.page_type == PageType.DOCUMENTATION
