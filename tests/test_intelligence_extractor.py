from unittest.mock import MagicMock

from app.intelligence.extractor import (
    _extract_buttons,
    _extract_forms,
    _extract_headings,
    _extract_images,
    _extract_inputs,
    _extract_links,
    analyze_page,
)
from app.intelligence.models import (
    ButtonInfo,
    FormInfo,
    HeadingInfo,
    ImageInfo,
    InputInfo,
    LinkInfo,
)


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
