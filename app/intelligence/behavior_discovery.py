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


def _clean(value: str | None) -> str:
    return " ".join((value or "").split())


def _meaningful(value: str | None) -> bool:
    return bool(re.search(r"[\w]", _clean(value), flags=re.UNICODE))


def _contains_term(value: str, terms: Iterable[str]) -> bool:
    normalized = value.casefold()
    return any(term in normalized for term in terms)


def _input_signal(input_item: InputInfo) -> str:
    parts = [
        f"type={_clean(input_item.input_type).casefold() or 'text'}",
    ]
    if _meaningful(input_item.name):
        parts.append(f"name={_clean(input_item.name)}")
    if _meaningful(input_item.placeholder):
        parts.append(f"placeholder={_clean(input_item.placeholder)}")
    return ", ".join(parts)


def _is_search_input(input_item: InputInfo) -> bool:
    signal = " ".join(
        (
            input_item.input_type,
            input_item.name or "",
            input_item.placeholder or "",
        )
    )
    return (
        input_item.input_type.casefold() == "search"
        or _contains_term(signal, _SEARCH_TERMS)
    )


def _evidence(
    evidence_type: EvidenceType,
    descriptions: Iterable[str],
) -> list[EvidenceItem]:
    unique_descriptions = dict.fromkeys(descriptions)
    return [
        EvidenceItem(
            type=evidence_type,
            source=EvidenceSource.DETERMINISTIC,
            description=description,
        )
        for description in unique_descriptions
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
    """Discover page-observable capabilities without creating test scenarios."""
    behaviors: list[ApplicationBehavior] = []

    meaningful_links = [
        link
        for link in result.links
        if _meaningful(link.text)
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
                    f"Link observed: text={_clean(link.text)}, href={_clean(link.href)}"
                    for link in meaningful_links
                ),
            )
        )

    password_inputs = [
        item for item in result.inputs if item.input_type.casefold() == "password"
    ]
    search_inputs = [item for item in result.inputs if _is_search_input(item)]
    data_inputs = [
        item
        for item in result.inputs
        if item.input_type.casefold() in _DATA_ENTRY_TYPES
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
                    f"Password input observed: {_input_signal(item)}"
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
                    f"Search-like input observed: {_input_signal(item)}"
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
                    f"Data-entry input observed: {_input_signal(item)}"
                    for item in data_inputs
                ),
            )
        )

    button_labels = [_clean(button.text) for button in result.buttons]
    button_labels = [label for label in button_labels if _meaningful(label)]
    auth_buttons = [
        label for label in button_labels if _contains_term(label, _AUTH_TERMS)
    ]
    search_buttons = [
        label for label in button_labels if _contains_term(label, _SEARCH_TERMS)
    ]
    submit_buttons = [
        _clean(button.text)
        for button in result.buttons
        if _meaningful(button.text)
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

    if result.forms:
        form_evidence = [
            f"Form observed: method={_clean(form.method).casefold() or 'get'}"
            + (f", action={_clean(form.action)}" if _meaningful(form.action) else "")
            for form in result.forms
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
