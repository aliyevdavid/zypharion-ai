import json
from abc import ABC, abstractmethod

from app.ai.engine import AIEngine
from app.ai.models import (
    AIIntelligenceResult,
    AIPageClassification,
    AIRecommendation,
    AIRequest,
    RecommendationPriority,
)
from app.intelligence.analysis_models import PageAnalysisResult


class AIIntelligenceEngine(ABC):
    """
    Provider-independent contract for page-focused AI intelligence.
    """

    @abstractmethod
    def classify_page(
        self,
        analysis: PageAnalysisResult,
    ) -> AIPageClassification:
        """Classify a deterministically analyzed page."""
        raise NotImplementedError

    @abstractmethod
    def generate_summary(
        self,
        analysis: PageAnalysisResult,
    ) -> str:
        """Generate a concise summary of a page analysis."""
        raise NotImplementedError

    @abstractmethod
    def generate_recommendations(
        self,
        analysis: PageAnalysisResult,
    ) -> list[AIRecommendation]:
        """Generate structured recommendations for a page analysis."""
        raise NotImplementedError

    def analyze(
        self,
        analysis: PageAnalysisResult,
    ) -> AIIntelligenceResult:
        """Build the complete AI intelligence result."""
        return AIIntelligenceResult(
            classification=self.classify_page(analysis),
            summary=self.generate_summary(analysis),
            recommendations=self.generate_recommendations(analysis),
        )


class DeterministicIntelligenceEngine(AIIntelligenceEngine):
    """
    Stable local placeholder for the future model-backed engine.

    This implementation only reformats existing deterministic analysis. It
    performs no model inference and makes no network requests.
    """

    def classify_page(
        self,
        analysis: PageAnalysisResult,
    ) -> AIPageClassification:
        evidence = analysis.classification.evidence
        reasoning = (
            "; ".join(evidence)
            if evidence
            else "No classification evidence was available."
        )

        return AIPageClassification(
            category=analysis.classification.page_type.value,
            confidence=analysis.classification.confidence,
            reasoning=reasoning,
        )

    def generate_summary(
        self,
        analysis: PageAnalysisResult,
    ) -> str:
        title = analysis.title.strip() or "Untitled page"
        page_type = analysis.classification.page_type.value

        return (
            f"{title} was deterministically classified as {page_type}. "
            f"Detected {len(analysis.detected_features)} feature(s) and "
            f"{len(analysis.findings)} finding(s)."
        )

    def generate_recommendations(
        self,
        analysis: PageAnalysisResult,
    ) -> list[AIRecommendation]:
        return [
            AIRecommendation(
                title=f"Recommendation {index}",
                description=description,
                priority=RecommendationPriority.MEDIUM,
            )
            for index, description in enumerate(
                analysis.recommendations,
                start=1,
            )
        ]


class LLMIntelligenceEngine(AIIntelligenceEngine):
    """
    Page-intelligence adapter backed by a provider-neutral AI engine.
    """

    def __init__(self, ai_engine: AIEngine) -> None:
        self._ai_engine = ai_engine

    def analyze(
        self,
        analysis: PageAnalysisResult,
    ) -> AIIntelligenceResult:
        """Generate and validate structured page intelligence."""
        return self._generate_result(analysis)

    def classify_page(
        self,
        analysis: PageAnalysisResult,
    ) -> AIPageClassification:
        return self._generate_result(analysis).classification

    def generate_summary(
        self,
        analysis: PageAnalysisResult,
    ) -> str:
        return self._generate_result(analysis).summary

    def generate_recommendations(
        self,
        analysis: PageAnalysisResult,
    ) -> list[AIRecommendation]:
        return self._generate_result(analysis).recommendations

    def _generate_result(
        self,
        analysis: PageAnalysisResult,
    ) -> AIIntelligenceResult:
        response = self._ai_engine.generate(
            self._build_request(analysis)
        )
        response_data = json.loads(response.content)

        return AIIntelligenceResult.model_validate(response_data)

    @staticmethod
    def _build_request(
        analysis: PageAnalysisResult,
    ) -> AIRequest:
        context = {
            "title": analysis.title,
            "final_url": analysis.final_url,
            "deterministic_classification": {
                "page_type": analysis.classification.page_type.value,
                "confidence": analysis.classification.confidence,
                "evidence": analysis.classification.evidence,
            },
            "detected_features": analysis.detected_features,
            "findings": [
                finding.model_dump(mode="json")
                for finding in analysis.findings
            ],
            "deterministic_recommendations": analysis.recommendations,
        }

        return AIRequest(
            instruction=(
                "Return only JSON with classification "
                "{category, confidence, reasoning}, summary, and "
                "recommendations [{title, description, priority}]. "
                "Recommendation priority must be low, medium, or high."
            ),
            context=json.dumps(
                context,
                sort_keys=True,
                separators=(",", ":"),
            ),
            temperature=0.0,
        )
