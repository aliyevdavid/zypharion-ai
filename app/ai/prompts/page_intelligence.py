import json

from app.ai.models import AIRequest
from app.intelligence.analysis_models import PageAnalysisResult


class PageIntelligencePromptBuilder:
    """
    Build provider-neutral requests for page intelligence.
    """

    def build(
        self,
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
