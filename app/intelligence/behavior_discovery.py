from __future__ import annotations

import re
from collections.abc import Iterable

from app.intelligence.analysis_models import PageClassification, PageType
from app.intelligence.behavior_models import (
    ApplicationBehavior,
    BehaviorSource,
    BehaviorType,
)
from app.intelligence.evidence_models import (
    EvidenceItem,
    EvidenceSource,
    EvidenceType,
)
from app.intelligence.models import BrowserIntelligenceResult, InputInfo


_SEARCH_TERMS = ("search", "query", "find", "lookup")
_AUTH_TERMS = ("login", "log in", "sign in", "signin", "authenticate")
_SUBMIT_TERMS = ("submit", "send", "save", "continue", "apply")
_TEST_CASE_TERMS = ("assert", "expected result", "step", "verify that")
_HTML_LIKE = re.compile(r"<\s*/?\s*[a-z][^>]*>", flags=re.IGNORECASE)
_SELECTOR_LIKE = re.compile(
    r"(?:^|\s)(?:[#.][\w-]+|[a-z][\w-]*[.#][\w-]+|\[[^\]]+\]|"
    r"//?[a-z][\w-]*|[a-z]+\s*>\s*[a-z]+)",
    flags=re.IGNORECASE,
)
_DATA_ENTRY_TYPES = {
    "date",
    "datetime-local",
    "email",
    "month",
    "number",
    "search",
    "tel",
    "text",
    "time",
    "url",
    "week",
}
_SUPPORTED_INPUT_TYPES = _DATA_ENTRY_TYPES | {
    "button",
    "checkbox",
    "color",
    "file",
    "hidden",
    "image",
    "password",
    "radio",
    "range",
    "reset",
    "submit",
}
_SUPPORTED_FORM_METHODS = {"get", "post", "dialog"}


def _clean(value: str | None) -> str:
    return " ".join((value or "").split())


def _meaningful(value: str | None) -> bool:
    return bool(re.search(r"[\w]", _clean(value), flags=re.UNICODE))


def _safe_observed_text(value: str | None) -> str | None:
    """Return normalized user-facing text that is safe for public evidence."""
    normalized = _clean(value)
    if (
        not _meaningful(normalized)
        or _HTML_LIKE.search(normalized)
        or _SELECTOR_LIKE.search(normalized)
        or _contains_term(normalized, _TEST_CASE_TERMS)
    ):
        return None
    return normalized


def _contains_term(value: str, terms: Iterable[str]) -> bool:
    normalized = value.casefold()
    return any(term in normalized for term in terms)


def _input_signal(input_item: InputInfo) -> str:
    input_type = _clean(input_item.input_type).casefold()
    return f"Input observed: type={input_type}"


def _supported_input(input_item: InputInfo) -> bool:
    return _clean(input_item.input_type).casefold() in _SUPPORTED_INPUT_TYPES


def _is_search_input(input_item: InputInfo) -> bool:
    if not _supported_input(input_item):
        return False
    signal = " ".join(
        value
        for value in (
            _clean(input_item.input_type),
            _safe_observed_text(input_item.name),
            _safe_observed_text(input_item.placeholder),
        )
        if value
    )
    return (
        input_item.input_type.casefold() == "search"
        or _contains_term(signal, _SEARCH_TERMS)
    )


def _evidence(
    evidence_type: EvidenceType,
    descriptions: Iterable[str],
) -> list[EvidenceItem]:
    unique_descriptions: dict[str, str] = {}
    for description in descriptions:
        normalized = _clean(description)
        if _meaningful(normalized):
            unique_descriptions.setdefault(normalized.casefold(), normalized)
    return [
        EvidenceItem(
            type=evidence_type,
            source=EvidenceSource.DETERMINISTIC,
            description=description,
        )
        for description in unique_descriptions.values()
    ]


def _behavior(
    behavior_type: BehaviorType,
    source: BehaviorSource,
    name: str,
    description: str,
    evidence_type: EvidenceType,
    evidence: Iterable[str],
) -> ApplicationBehavior:
    return ApplicationBehavior(
        behavior_type=behavior_type,
        name=name,
        description=description,
        source=source,
        evidence=_evidence(evidence_type, evidence),
    )


def discover_application_behaviors(
    result: BrowserIntelligenceResult,
    classification: PageClassification | None = None,
) -> list[ApplicationBehavior]:
    """Discover deterministic page-observable capabilities.

    Discovery describes only signals present in this browser snapshot. It is
    intentionally independent of AI and is neither a complete application
    model nor a source of test cases, selectors, steps, or assertions.
    """
    behaviors: list[ApplicationBehavior] = []

    meaningful_links = [
        link
        for link in result.links
        if _safe_observed_text(link.text)
        and bool(_clean(link.href))
        and not _clean(link.href).casefold().startswith(("#", "javascript:"))
    ]
    if meaningful_links:
        behaviors.append(
            _behavior(
                BehaviorType.NAVIGATION,
                BehaviorSource.LINK,
                "Link navigation",
                "The page exposes meaningful links for navigation.",
                EvidenceType.BEHAVIOR,
                (
                    f"Link observed: label={_safe_observed_text(link.text)}"
                    for link in meaningful_links
                ),
            )
        )

    password_inputs = [
        item
        for item in result.inputs
        if _clean(item.input_type).casefold() == "password"
    ]
    search_inputs = [item for item in result.inputs if _is_search_input(item)]
    data_inputs = [
        item
        for item in result.inputs
        if _clean(item.input_type).casefold() in _DATA_ENTRY_TYPES
        and item not in search_inputs
    ]

    if password_inputs:
        behaviors.append(
            _behavior(
                BehaviorType.AUTHENTICATION,
                BehaviorSource.INPUT,
                "Credential authentication",
                "The page accepts a password credential.",
                EvidenceType.STRUCTURE,
                (
                    _input_signal(item)
                    for item in password_inputs
                ),
            )
        )
    if search_inputs:
        behaviors.append(
            _behavior(
                BehaviorType.SEARCH,
                BehaviorSource.INPUT,
                "Search input",
                "The page accepts search-like input.",
                EvidenceType.STRUCTURE,
                (
                    _input_signal(item)
                    for item in search_inputs
                ),
            )
        )
    if data_inputs:
        behaviors.append(
            _behavior(
                BehaviorType.DATA_ENTRY,
                BehaviorSource.INPUT,
                "Data entry",
                "The page accepts general user-entered data.",
                EvidenceType.STRUCTURE,
                (
                    _input_signal(item)
                    for item in data_inputs
                ),
            )
        )

    button_labels = [
        label
        for button in result.buttons
        if (label := _safe_observed_text(button.text)) is not None
    ]
    auth_buttons = [
        label for label in button_labels if _contains_term(label, _AUTH_TERMS)
    ]
    search_buttons = [
        label for label in button_labels if _contains_term(label, _SEARCH_TERMS)
    ]
    submit_buttons = [
        label
        for button in result.buttons
        if (label := _safe_observed_text(button.text)) is not None
        and (
            (button.button_type or "").casefold() == "submit"
            or _contains_term(_clean(button.text), _SUBMIT_TERMS)
        )
    ]
    action_buttons = [
        label
        for label in button_labels
        if label not in submit_buttons
        and label not in auth_buttons
        and label not in search_buttons
    ]

    for behavior_type, name, description, labels in (
        (
            BehaviorType.AUTHENTICATION,
            "Authentication action",
            "The page exposes an authentication action.",
            auth_buttons,
        ),
        (
            BehaviorType.SEARCH,
            "Search action",
            "The page exposes an action to perform a search.",
            search_buttons,
        ),
        (
            BehaviorType.FORM_SUBMISSION,
            "Submission action",
            "The page exposes an action that submits user data.",
            submit_buttons,
        ),
        (
            BehaviorType.USER_ACTION,
            "Page action",
            "The page exposes a meaningful user action.",
            action_buttons,
        ),
    ):
        if labels:
            behaviors.append(
                _behavior(
                    behavior_type,
                    BehaviorSource.BUTTON,
                    name,
                    description,
                    EvidenceType.BEHAVIOR,
                    (f"Button observed: label={label}" for label in labels),
                )
            )

    meaningful_forms = [
        form
        for form in result.forms
        if _clean(form.method).casefold() in _SUPPORTED_FORM_METHODS
    ]
    if meaningful_forms:
        form_evidence = [
            f"Form observed: method={_clean(form.method).casefold()}"
            for form in meaningful_forms
        ]
        behaviors.append(
            _behavior(
                BehaviorType.FORM_SUBMISSION,
                BehaviorSource.FORM,
                "Form submission",
                "The page exposes one or more forms for submitting data.",
                EvidenceType.STRUCTURE,
                form_evidence,
            )
        )
        if password_inputs:
            behaviors.append(
                _behavior(
                    BehaviorType.AUTHENTICATION,
                    BehaviorSource.FORM,
                    "Authentication form",
                    "A form and password input indicate credential authentication.",
                    EvidenceType.STRUCTURE,
                    [*form_evidence, "Password input is present on the same page."],
                )
            )
        if search_inputs or search_buttons:
            behaviors.append(
                _behavior(
                    BehaviorType.SEARCH,
                    BehaviorSource.FORM,
                    "Search form",
                    "A form and search signal indicate search behavior.",
                    EvidenceType.STRUCTURE,
                    [
                        *form_evidence,
                        "Search input or action is present on the same page.",
                    ],
                )
            )

    existing_types = {behavior.behavior_type for behavior in behaviors}
    classification_mapping = {
        PageType.AUTHENTICATION: BehaviorType.AUTHENTICATION,
        PageType.SEARCH: BehaviorType.SEARCH,
        PageType.FORM: BehaviorType.FORM_SUBMISSION,
    }
    if classification and (
        behavior_type := classification_mapping.get(classification.page_type)
    ):
        if behavior_type not in existing_types:
            behaviors.append(
                _behavior(
                    behavior_type,
                    BehaviorSource.CLASSIFICATION,
                    (
                        classification.page_type.value.replace("_", " ").title()
                        + " capability"
                    ),
                    "The deterministic page classification indicates this capability.",
                    EvidenceType.STRUCTURE,
                    [f"Page classified as {classification.page_type.value}."],
                )
            )

    return behaviors
