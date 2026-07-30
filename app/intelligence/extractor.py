from __future__ import annotations

from time import perf_counter
from urllib.parse import urljoin, urlparse

from playwright.sync_api import Page, sync_playwright

from app.core.settings import get_settings
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


def _normalize_text(value: str | None) -> str:
    """
    Normalize whitespace and safely handle missing text values.
    """
    return " ".join((value or "").split())


def _is_external_link(page_url: str, target_url: str) -> bool:
    """
    Return True when the target URL belongs to a different host.
    """
    page_host = urlparse(page_url).netloc.lower()
    target_host = urlparse(target_url).netloc.lower()

    return bool(target_host and target_host != page_host)


def _get_optional_attribute(
    page: Page,
    selector: str,
    attribute_name: str,
) -> str | None:
    """
    Return an attribute from the first matching element.

    Optional metadata elements may not exist on every page. Checking the
    locator count first prevents Playwright from waiting for the full default
    timeout when the selector is absent.
    """
    locator = page.locator(selector)

    if locator.count() == 0:
        return None

    return locator.first.get_attribute(attribute_name)


def _evaluate_all(
    page: Page,
    selector: str,
    expression: str,
) -> list[dict[str, object]]:
    records = page.locator(selector).evaluate_all(expression)

    if not isinstance(records, list):
        raise TypeError("Browser snapshot must return a list")

    return records


def _extract_headings(page: Page) -> list[HeadingInfo]:
    headings: list[HeadingInfo] = []

    for level in range(1, 7):
        records = _evaluate_all(
            page,
            f"h{level}",
            """
            elements => elements.map(element => ({
                text: element.innerText,
            }))
            """,
        )

        for record in records:
            text = _normalize_text(record.get("text"))
            if text:
                headings.append(
                    HeadingInfo(
                        level=level,
                        text=text,
                    )
                )

    return headings


def _extract_links(page: Page) -> list[LinkInfo]:
    links: list[LinkInfo] = []
    records = _evaluate_all(
        page,
        "a[href]",
        """
        elements => elements.map(element => ({
            text: element.innerText,
            href: element.getAttribute("href"),
        }))
        """,
    )

    for record in records:
        raw_href = record.get("href")
        if not raw_href:
            continue

        absolute_href = urljoin(page.url, raw_href)

        links.append(
            LinkInfo(
                text=_normalize_text(record.get("text")),
                href=absolute_href,
                is_external=_is_external_link(
                    page_url=page.url,
                    target_url=absolute_href,
                ),
            )
        )

    return links


def _extract_images(page: Page) -> list[ImageInfo]:
    images: list[ImageInfo] = []
    records = _evaluate_all(
        page,
        "img",
        """
        elements => elements.map(element => ({
            src: element.getAttribute("src"),
            alt: element.getAttribute("alt"),
        }))
        """,
    )

    for record in records:
        raw_src = record.get("src")
        if not raw_src:
            continue

        images.append(
            ImageInfo(
                src=urljoin(page.url, raw_src),
                alt=record.get("alt"),
            )
        )

    return images


def _extract_forms(page: Page) -> list[FormInfo]:
    forms: list[FormInfo] = []
    records = _evaluate_all(
        page,
        "form",
        """
        elements => elements.map(element => ({
            action: element.getAttribute("action"),
            method: element.getAttribute("method"),
        }))
        """,
    )

    for record in records:
        raw_action = record.get("action")
        method = (record.get("method") or "get").lower()
        forms.append(
            FormInfo(
                action=(
                    urljoin(page.url, raw_action)
                    if raw_action
                    else None
                ),
                method=method,
            )
        )

    return forms


def _extract_buttons(page: Page) -> list[ButtonInfo]:
    buttons: list[ButtonInfo] = []
    records = _evaluate_all(
        page,
        "button",
        """
        elements => elements.map(element => ({
            text: element.innerText,
            button_type: element.getAttribute("type"),
        }))
        """,
    )

    for record in records:
        buttons.append(
            ButtonInfo(
                text=_normalize_text(record.get("text")),
                button_type=record.get("button_type"),
            )
        )

    return buttons


def _extract_inputs(page: Page) -> list[InputInfo]:
    inputs: list[InputInfo] = []
    records = _evaluate_all(
        page,
        "input",
        """
        elements => elements.map(element => ({
            name: element.getAttribute("name"),
            input_type: element.getAttribute("type"),
            placeholder: element.getAttribute("placeholder"),
            required: element.hasAttribute("required"),
        }))
        """,
    )

    for record in records:
        inputs.append(
            InputInfo(
                name=record.get("name"),
                input_type=record.get("input_type") or "text",
                placeholder=record.get("placeholder"),
                required=bool(record.get("required", False)),
            )
        )

    return inputs


def analyze_page(url: str) -> BrowserIntelligenceResult:
    """
    Open a page with Playwright and return structured browser intelligence.
    """
    settings = get_settings()
    console_errors: list[str] = []

    started_at = perf_counter()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=settings.playwright_headless,
        )

        try:
            page = browser.new_page()
            page.set_default_timeout(settings.playwright_timeout_ms)

            page.on(
                "console",
                lambda message: (
                    console_errors.append(message.text)
                    if message.type == "error"
                    else None
                ),
            )

            response = page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=settings.playwright_timeout_ms,
            )

            meta_description = _get_optional_attribute(
                page=page,
                selector='meta[name="description"]',
                attribute_name="content",
            )

            raw_canonical_url = _get_optional_attribute(
                page=page,
                selector='link[rel="canonical"]',
                attribute_name="href",
            )

            canonical_url = (
                urljoin(page.url, raw_canonical_url)
                if raw_canonical_url
                else None
            )

            return BrowserIntelligenceResult(
                requested_url=url,
                final_url=page.url,
                title=page.title(),
                meta_description=meta_description,
                canonical_url=canonical_url,
                status_code=response.status if response else None,
                success=response.ok if response else False,
                headings=_extract_headings(page),
                links=_extract_links(page),
                images=_extract_images(page),
                forms=_extract_forms(page),
                buttons=_extract_buttons(page),
                inputs=_extract_inputs(page),
                console_errors=console_errors,
                metrics=PageMetrics(
                    load_time_ms=max(
                        0,
                        round((perf_counter() - started_at) * 1000),
                    )
                ),
            )
        finally:
            browser.close()
