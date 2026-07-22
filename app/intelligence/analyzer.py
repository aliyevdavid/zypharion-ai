from __future__ import annotations

from dataclasses import dataclass

from app.intelligence.analysis_models import (
    AnalysisFinding,
    PageAnalysisResult,
    PageClassification,
    PageType,
)
from app.intelligence.models import BrowserIntelligenceResult


@dataclass(frozen=True)
class ClassificationCandidate:
    page_type: PageType
    score: int
    evidence: list[str]


def _collect_page_text(result: BrowserIntelligenceResult) -> str:
    text_parts = [
        result.title,
        result.meta_description or "",
    ]

    text_parts.extend(heading.text for heading in result.headings)
    text_parts.extend(button.text for button in result.buttons)
    text_parts.extend(link.text for link in result.links)
    text_parts.extend(
        input_item.placeholder or ""
        for input_item in result.inputs
    )
    text_parts.extend(
        input_item.name or ""
        for input_item in result.inputs
    )

    return " ".join(text_parts).lower()


def _has_input_type(
    result: BrowserIntelligenceResult,
    input_type: str,
) -> bool:
    return any(
        input_item.input_type.lower() == input_type.lower()
        for input_item in result.inputs
    )


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def _score_authentication_page(
    result: BrowserIntelligenceResult,
    page_text: str,
) -> ClassificationCandidate:
    score = 0
    evidence: list[str] = []

    if _has_input_type(result, "password"):
        score += 5
        evidence.append("Password input detected")

    if result.forms:
        score += 2
        evidence.append("Form detected")

    if _contains_any(
        page_text,
        (
            "login",
            "log in",
            "sign in",
            "signin",
            "username",
            "password",
            "forgot password",
        ),
    ):
        score += 3
        evidence.append("Authentication-related text detected")

    return ClassificationCandidate(
        page_type=PageType.AUTHENTICATION,
        score=score,
        evidence=evidence,
    )


def _score_search_page(
    result: BrowserIntelligenceResult,
    page_text: str,
) -> ClassificationCandidate:
    score = 0
    evidence: list[str] = []

    if _has_input_type(result, "search"):
        score += 5
        evidence.append("Search input detected")

    if _contains_any(
        page_text,
        (
            "search",
            "find",
            "results",
        ),
    ):
        score += 2
        evidence.append("Search-related text detected")

    if any(
        "search" in (input_item.placeholder or "").lower()
        for input_item in result.inputs
    ):
        score += 3
        evidence.append("Search placeholder detected")

    return ClassificationCandidate(
        page_type=PageType.SEARCH,
        score=score,
        evidence=evidence,
    )


def _score_documentation_page(
    result: BrowserIntelligenceResult,
    page_text: str,
) -> ClassificationCandidate:
    score = 0
    evidence: list[str] = []

    if _contains_any(
        page_text,
        (
            "documentation",
            "docs",
            "api reference",
            "developer guide",
            "getting started",
            "installation",
        ),
    ):
        score += 4
        evidence.append("Documentation-related text detected")

    if len(result.headings) >= 4:
        score += 2
        evidence.append("Multiple structured headings detected")

    if len(result.links) >= 8:
        score += 2
        evidence.append("High number of navigation links detected")

    return ClassificationCandidate(
        page_type=PageType.DOCUMENTATION,
        score=score,
        evidence=evidence,
    )


def _score_dashboard_page(
    result: BrowserIntelligenceResult,
    page_text: str,
) -> ClassificationCandidate:
    score = 0
    evidence: list[str] = []

    if _contains_any(
        page_text,
        (
            "dashboard",
            "analytics",
            "overview",
            "reports",
            "metrics",
            "activity",
        ),
    ):
        score += 4
        evidence.append("Dashboard-related text detected")

    if len(result.buttons) >= 4:
        score += 2
        evidence.append("Multiple interactive buttons detected")

    if len(result.forms) >= 2:
        score += 2
        evidence.append("Multiple forms detected")

    return ClassificationCandidate(
        page_type=PageType.DASHBOARD,
        score=score,
        evidence=evidence,
    )


def _score_form_page(
    result: BrowserIntelligenceResult,
) -> ClassificationCandidate:
    score = 0
    evidence: list[str] = []

    if result.forms:
        score += 3
        evidence.append("Form detected")

    if len(result.inputs) >= 3:
        score += 3
        evidence.append("Multiple input fields detected")

    if result.buttons:
        score += 1
        evidence.append("Form action button detected")

    return ClassificationCandidate(
        page_type=PageType.FORM,
        score=score,
        evidence=evidence,
    )


def _score_marketing_page(
    result: BrowserIntelligenceResult,
    page_text: str,
) -> ClassificationCandidate:
    score = 0
    evidence: list[str] = []

    has_marketing_text = _contains_any(
        page_text,
        (
            "learn more",
            "get started",
            "contact us",
            "pricing",
            "features",
            "solutions",
        ),
    )

    if has_marketing_text:
        score += 3
        evidence.append("Marketing-related text detected")

    if result.images:
        score += 1
        evidence.append("Visual content detected")

    if result.headings:
        score += 1
        evidence.append("Prominent heading content detected")

    has_informational_content = bool(
        result.title.strip()
        or result.meta_description
        or result.headings
        or result.links
        or result.images
    )

    if (
        has_informational_content
        and not result.forms
        and not _has_input_type(result, "password")
    ):
        score += 1
        evidence.append("Informational page structure detected")

    return ClassificationCandidate(
        page_type=PageType.MARKETING,
        score=score,
        evidence=evidence,
    )


def _calculate_confidence(score: int) -> float:
    if score <= 0:
        return 0.25

    return min(0.99, round(0.45 + (score * 0.05), 2))


def _classify_page(
    result: BrowserIntelligenceResult,
) -> PageClassification:
    page_text = _collect_page_text(result)

    candidates = [
        _score_authentication_page(result, page_text),
        _score_search_page(result, page_text),
        _score_documentation_page(result, page_text),
        _score_dashboard_page(result, page_text),
        _score_form_page(result),
        _score_marketing_page(result, page_text),
    ]

    best_candidate = max(
        candidates,
        key=lambda candidate: candidate.score,
    )

    if best_candidate.score == 0:
        return PageClassification(
            page_type=PageType.UNKNOWN,
            confidence=0.25,
            evidence=["No strong classification signals detected"],
        )

    return PageClassification(
        page_type=best_candidate.page_type,
        confidence=_calculate_confidence(best_candidate.score),
        evidence=best_candidate.evidence,
    )


def _detect_features(
    result: BrowserIntelligenceResult,
) -> list[str]:
    features: list[str] = []

    if result.forms:
        features.append("forms")

    if result.buttons:
        features.append("interactive_buttons")

    if result.links:
        features.append("navigation_links")

    if result.images:
        features.append("images")

    if _has_input_type(result, "password"):
        features.append("password_input")

    if _has_input_type(result, "email"):
        features.append("email_input")

    if _has_input_type(result, "search"):
        features.append("search_input")

    if result.console_errors:
        features.append("console_errors")

    return features


def _build_findings(
    result: BrowserIntelligenceResult,
) -> list[AnalysisFinding]:
    findings: list[AnalysisFinding] = []

    missing_alt_count = sum(
        1
        for image in result.images
        if not image.alt or not image.alt.strip()
    )

    if missing_alt_count:
        findings.append(
            AnalysisFinding(
                category="accessibility",
                message=(
                    f"{missing_alt_count} image(s) are missing "
                    "alternative text"
                ),
                severity="warning",
            )
        )

    if result.console_errors:
        findings.append(
            AnalysisFinding(
                category="reliability",
                message=(
                    f"{len(result.console_errors)} browser console "
                    "error(s) were detected"
                ),
                severity="warning",
            )
        )

    required_inputs = sum(
        1
        for input_item in result.inputs
        if input_item.required
    )

    if required_inputs:
        findings.append(
            AnalysisFinding(
                category="form",
                message=(
                    f"{required_inputs} required input field(s) detected"
                ),
                severity="info",
            )
        )

    return findings


def _build_recommendations(
    result: BrowserIntelligenceResult,
    findings: list[AnalysisFinding],
) -> list[str]:
    recommendations: list[str] = [
        "Add this page to automated smoke-test coverage",
    ]

    if result.forms:
        recommendations.append(
            "Create positive and negative validation tests for detected forms"
        )

    if any(
        finding.category == "accessibility"
        for finding in findings
    ):
        recommendations.append(
            "Run a dedicated accessibility audit"
        )

    if result.console_errors:
        recommendations.append(
            "Investigate browser console errors before release"
        )

    return recommendations


def analyze_browser_intelligence(
    result: BrowserIntelligenceResult,
) -> PageAnalysisResult:
    """
    Interpret structured browser observations and return explainable insights.
    """
    classification = _classify_page(result)
    findings = _build_findings(result)

    return PageAnalysisResult(
        requested_url=result.requested_url,
        final_url=result.final_url,
        title=result.title,
        classification=classification,
        detected_features=_detect_features(result),
        findings=findings,
        recommendations=_build_recommendations(
            result=result,
            findings=findings,
        ),
    )