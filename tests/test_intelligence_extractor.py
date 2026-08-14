from contextlib import ExitStack
from unittest.mock import MagicMock, patch

import pytest

from app.intelligence.extractor import (
    _PageMetadata,
    _extract_buttons,
    _extract_forms,
    _extract_headings,
    _extract_images,
    _extract_inputs,
    _extract_links,
    _extract_metadata,
    analyze_page,
)
from app.intelligence.models import (
    BrowserIntelligenceResult,
    ButtonInfo,
    FormInfo,
    HeadingInfo,
    ImageInfo,
    InputInfo,
    LinkInfo,
    PageMetrics,
)


def _run_mocked_analysis(
    failures: set[str] | None = None,
    metadata: _PageMetadata | None = None,
) -> tuple[BrowserIntelligenceResult, MagicMock]:
    failures = failures or set()
    page = MagicMock()
    page.url = "https://example.test/final"
    response = MagicMock(status=200, ok=True)
    page.goto.return_value = response
    browser = MagicMock()
    browser.new_page.return_value = page
    playwright = MagicMock()
    playwright.chromium.launch.return_value = browser
    manager = MagicMock()
    manager.__enter__.return_value = playwright

    values = {
        "_extract_metadata": metadata
        or _PageMetadata(
            "Example",
            "Description",
            "https://example.test/canonical",
        ),
        "_extract_headings": [HeadingInfo(level=1, text="Kept heading")],
        "_extract_links": [
            LinkInfo(
                text="Kept link",
                href="https://example.test/link",
                is_external=False,
            )
        ],
        "_extract_images": [
            ImageInfo(
                src="https://example.test/image.png",
                alt="Kept image",
            )
        ],
        "_extract_forms": [
            FormInfo(
                action="https://example.test/submit",
                method="post",
            )
        ],
        "_extract_buttons": [ButtonInfo(text="Kept button", button_type="button")],
        "_extract_inputs": [InputInfo(name="kept", input_type="text")],
        "_extract_console_errors": ["kept console error"],
        "_extract_metrics": PageMetrics(load_time_ms=12),
    }

    with ExitStack() as stack:
        stack.enter_context(
            patch(
                "app.intelligence.extractor.sync_playwright",
                return_value=manager,
            )
        )
        for name, value in values.items():
            mocked = stack.enter_context(
                patch(f"app.intelligence.extractor.{name}")
            )
            if name in failures:
                mocked.side_effect = RuntimeError(
                    f"raw secret from {name} C:\\private\\browser"
                )
            else:
                mocked.return_value = value
        result = analyze_page("https://example.test")

    return result, browser


def test_extract_buttons_builds_button_info_from_ordered_snapshot() -> None:
    page = MagicMock()
    locator = page.locator.return_value
    locator.evaluate_all.return_value = [
        {
            "text": "  First\n  button ",
            "button_type": "submit",
        },
        {
            "text": "\tSecond   button\t",
            "button_type": None,
        },
    ]

    result = _extract_buttons(page)

    page.locator.assert_called_once_with("button")
    assert result == [
        ButtonInfo(text="First button", button_type="submit"),
        ButtonInfo(text="Second button", button_type=None),
    ]


def test_extract_inputs_preserves_order_defaults_and_optional_fields() -> None:
    page = MagicMock()
    page.locator.return_value.evaluate_all.return_value = [
        {
            "name": "email",
            "input_type": "email",
            "placeholder": "Email address",
            "required": True,
        },
        {
            "name": None,
            "input_type": None,
            "placeholder": None,
            "required": False,
        },
    ]

    assert _extract_inputs(page) == [
        InputInfo(
            name="email",
            input_type="email",
            placeholder="Email address",
            required=True,
        ),
        InputInfo(
            name=None,
            input_type="text",
            placeholder=None,
            required=False,
        ),
    ]
    page.locator.assert_called_once_with("input")


def test_extract_forms_resolves_actions_and_normalizes_methods() -> None:
    page = MagicMock()
    page.url = "https://example.test/account/page"
    page.locator.return_value.evaluate_all.return_value = [
        {"action": "../submit", "method": "POST"},
        {"action": None, "method": None},
        {"action": "", "method": ""},
    ]

    assert _extract_forms(page) == [
        FormInfo(action="https://example.test/submit", method="post"),
        FormInfo(action=None, method="get"),
        FormInfo(action=None, method="get"),
    ]
    page.locator.assert_called_once_with("form")


def test_extract_images_resolves_sources_and_skips_missing_sources() -> None:
    page = MagicMock()
    page.url = "https://example.test/assets/page"
    page.locator.return_value.evaluate_all.return_value = [
        {"src": "logo.png", "alt": "Logo"},
        {"src": "/hero.png", "alt": None},
        {"src": None, "alt": "Missing"},
        {"src": "", "alt": "Empty"},
    ]

    assert _extract_images(page) == [
        ImageInfo(src="https://example.test/assets/logo.png", alt="Logo"),
        ImageInfo(src="https://example.test/hero.png", alt=None),
    ]
    page.locator.assert_called_once_with("img")


def test_extract_links_preserves_order_and_skips_missing_hrefs() -> None:
    page = MagicMock()
    page.url = "https://example.test/docs/page"
    page.locator.return_value.evaluate_all.return_value = [
        {"text": "  Local\n link ", "href": "../guide"},
        {"text": " External   link ", "href": "https://other.test/path"},
        {"text": "Missing", "href": None},
        {"text": "Empty", "href": ""},
    ]

    assert _extract_links(page) == [
        LinkInfo(
            text="Local link",
            href="https://example.test/guide",
            is_external=False,
        ),
        LinkInfo(
            text="External link",
            href="https://other.test/path",
            is_external=True,
        ),
    ]
    page.locator.assert_called_once_with("a[href]")


def test_extract_headings_preserves_level_grouped_order() -> None:
    page = MagicMock()
    snapshots = {
        "h1": [
            {"text": " First   heading "},
            {"text": " \n\t "},
            {"text": "Second h1"},
        ],
        "h2": [{"text": "\n H2 heading \t"}],
        "h3": [],
        "h4": [{"text": "H4 heading"}],
        "h5": [],
        "h6": [{"text": "H6 heading"}],
    }
    page.locator.side_effect = lambda selector: MagicMock(
        evaluate_all=MagicMock(return_value=snapshots[selector])
    )

    assert _extract_headings(page) == [
        HeadingInfo(level=1, text="First heading"),
        HeadingInfo(level=1, text="Second h1"),
        HeadingInfo(level=2, text="H2 heading"),
        HeadingInfo(level=4, text="H4 heading"),
        HeadingInfo(level=6, text="H6 heading"),
    ]
    assert [call.args[0] for call in page.locator.call_args_list] == [
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
    ]


def _metadata_page(
    *,
    title: str = "Example",
    description: str | None = "Description",
    canonical: str | None = "/canonical",
) -> MagicMock:
    page = MagicMock()
    page.url = "https://example.test/final"
    page.title.return_value = title

    def locator(selector: str) -> MagicMock:
        value = (
            description
            if selector == 'meta[name="description"]'
            else canonical
        )
        result = MagicMock()
        result.count.return_value = 0 if value is None else 1
        result.first.get_attribute.return_value = value
        return result

    page.locator.side_effect = locator
    return page


def test_extract_metadata_preserves_all_successful_values() -> None:
    metadata = _extract_metadata(_metadata_page())

    assert metadata == _PageMetadata(
        "Example",
        "Description",
        "https://example.test/canonical",
    )


@pytest.mark.parametrize(
    ("failed_operation", "expected"),
    [
        (
            "title",
            _PageMetadata(
                "",
                "Description",
                "https://example.test/canonical",
                True,
            ),
        ),
        (
            "description",
            _PageMetadata(
                "Example",
                None,
                "https://example.test/canonical",
                True,
            ),
        ),
        (
            "canonical",
            _PageMetadata("Example", "Description", None, True),
        ),
    ],
)
def test_extract_metadata_isolates_sub_field_failures(
    failed_operation: str,
    expected: _PageMetadata,
) -> None:
    page = _metadata_page()
    if failed_operation == "title":
        page.title.side_effect = RuntimeError("raw title secret")
    else:
        original_locator = page.locator.side_effect

        def failing_locator(selector: str) -> MagicMock:
            if (
                failed_operation == "description"
                and selector == 'meta[name="description"]'
            ) or (
                failed_operation == "canonical"
                and selector == 'link[rel="canonical"]'
            ):
                raise RuntimeError("raw metadata secret")
            return original_locator(selector)

        page.locator.side_effect = failing_locator

    assert _extract_metadata(page) == expected


def test_extract_metadata_multiple_failures_share_failure_flag() -> None:
    page = _metadata_page()
    page.title.side_effect = RuntimeError("raw title secret")
    page.locator.side_effect = RuntimeError("raw locator secret")

    assert _extract_metadata(page) == _PageMetadata("", None, None, True)


@pytest.mark.parametrize("missing_field", ["description", "canonical"])
def test_extract_metadata_normal_absence_is_not_failure(
    missing_field: str,
) -> None:
    page = _metadata_page(
        description=None if missing_field == "description" else "Description",
        canonical=None if missing_field == "canonical" else "/canonical",
    )

    metadata = _extract_metadata(page)

    assert metadata.extraction_failed is False
    assert getattr(
        metadata,
        "meta_description" if missing_field == "description" else "canonical_url",
    ) is None


def test_analyze_page_all_categories_succeed_without_warnings() -> None:
    result, browser = _run_mocked_analysis()

    assert result.success is True
    assert result.warnings == []
    assert result.title == "Example"
    assert result.headings[0].text == "Kept heading"
    assert result.links[0].text == "Kept link"
    assert result.images[0].alt == "Kept image"
    assert result.forms[0].method == "post"
    assert result.buttons[0].text == "Kept button"
    assert result.inputs[0].name == "kept"
    assert result.console_errors == ["kept console error"]
    assert result.metrics.load_time_ms == 12
    browser.close.assert_called_once_with()


def test_metadata_sub_failure_preserves_navigation_metrics_and_warning() -> None:
    result, browser = _run_mocked_analysis(
        metadata=_PageMetadata(
            "",
            "Description",
            "https://example.test/canonical",
            True,
        )
    )

    assert result.requested_url == "https://example.test"
    assert result.final_url == "https://example.test/final"
    assert result.status_code == 200
    assert result.success is True
    assert result.title == ""
    assert result.meta_description == "Description"
    assert result.canonical_url == "https://example.test/canonical"
    assert result.metrics == PageMetrics(load_time_ms=12)
    assert [warning.model_dump(mode="json") for warning in result.warnings] == [
        {
            "category": "metadata",
            "code": "metadata_extraction_failed",
            "message": "Page metadata could not be fully extracted.",
        }
    ]
    assert "raw" not in result.model_dump_json()
    browser.close.assert_called_once_with()


def test_multiple_metadata_sub_failures_produce_one_warning() -> None:
    result, _ = _run_mocked_analysis(
        metadata=_PageMetadata("", None, None, True)
    )

    assert [warning.category.value for warning in result.warnings] == [
        "metadata"
    ]


def test_metrics_failure_is_independent_from_metadata_failure() -> None:
    result, _ = _run_mocked_analysis(
        {"_extract_metrics"},
        metadata=_PageMetadata("Example", None, None, True),
    )

    assert result.title == "Example"
    assert result.metrics == PageMetrics(load_time_ms=0)
    assert [warning.category.value for warning in result.warnings] == [
        "metadata",
        "metrics",
    ]


@pytest.mark.parametrize(
    ("operation", "field", "category", "code", "message"),
    [
        (
            "_extract_metadata",
            "title",
            "metadata",
            "metadata_extraction_failed",
            "Page metadata could not be fully extracted.",
        ),
        (
            "_extract_headings",
            "headings",
            "headings",
            "headings_extraction_failed",
            "Heading content could not be extracted.",
        ),
        (
            "_extract_links",
            "links",
            "links",
            "links_extraction_failed",
            "Link content could not be extracted.",
        ),
        (
            "_extract_images",
            "images",
            "images",
            "images_extraction_failed",
            "Image content could not be extracted.",
        ),
        (
            "_extract_forms",
            "forms",
            "forms",
            "forms_extraction_failed",
            "Form content could not be extracted.",
        ),
        (
            "_extract_buttons",
            "buttons",
            "buttons",
            "buttons_extraction_failed",
            "Button content could not be extracted.",
        ),
        (
            "_extract_inputs",
            "inputs",
            "inputs",
            "inputs_extraction_failed",
            "Input content could not be extracted.",
        ),
        (
            "_extract_console_errors",
            "console_errors",
            "console",
            "console_extraction_failed",
            "Console errors could not be extracted.",
        ),
    ],
)
def test_localized_collection_failure_uses_safe_fallback_and_warning(
    operation: str,
    field: str,
    category: str,
    code: str,
    message: str,
) -> None:
    result, browser = _run_mocked_analysis({operation})

    assert result.success is True
    assert getattr(result, field) in ("", [])
    assert result.headings or field == "headings"
    assert result.links or field == "links"
    assert result.warnings[0].model_dump(mode="json") == {
        "category": category,
        "code": code,
        "message": message,
    }
    serialized = result.model_dump_json()
    assert "raw secret" not in serialized
    assert "private" not in serialized
    browser.close.assert_called_once_with()


def test_metrics_failure_returns_valid_fallback_and_warning() -> None:
    result, _ = _run_mocked_analysis({"_extract_metrics"})

    assert result.success is True
    assert result.metrics == PageMetrics(load_time_ms=0)
    assert result.warnings[0].category.value == "metrics"
    assert result.warnings[0].code.value == "metrics_extraction_failed"


def test_multiple_failures_produce_ordered_distinct_warnings() -> None:
    result, _ = _run_mocked_analysis(
        {"_extract_metadata", "_extract_links", "_extract_metrics"}
    )

    assert [warning.category.value for warning in result.warnings] == [
        "metadata",
        "links",
        "metrics",
    ]
    assert len({warning.code for warning in result.warnings}) == 3
    assert result.headings[0].text == "Kept heading"
    assert result.images[0].alt == "Kept image"


def test_warning_and_fallback_lists_are_fresh_per_analysis() -> None:
    first, _ = _run_mocked_analysis({"_extract_links"})
    second, _ = _run_mocked_analysis({"_extract_links"})

    first.links.append(
        LinkInfo(text="New", href="https://example.test/new", is_external=False)
    )
    first.warnings.clear()

    assert second.links == []
    assert len(second.warnings) == 1


def test_navigation_failure_remains_complete_failure_and_cleans_up() -> None:
    page = MagicMock()
    page.goto.side_effect = RuntimeError("navigation failed")
    browser = MagicMock()
    browser.new_page.return_value = page
    playwright = MagicMock()
    playwright.chromium.launch.return_value = browser
    manager = MagicMock()
    manager.__enter__.return_value = playwright

    with patch(
        "app.intelligence.extractor.sync_playwright",
        return_value=manager,
    ), pytest.raises(RuntimeError, match="navigation failed"):
        analyze_page("https://example.test")

    browser.close.assert_called_once_with()


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
