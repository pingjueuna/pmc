from __future__ import annotations

from dataclasses import asdict
from typing import Dict, Iterable, List

from .agents import (
    ErrorRatePredictorAgent,
    ExternalLLMReviewAgent,
    InternalQAAgent,
    ItemGeneratorAgent,
    ItemRevisionAgent,
    PersonaSimulationAgent,
    PersonaUpdaterAgent,
    PostExamAnalyticsAgent,
)
from .models import PipelineResult


class MultiAgentWorkflow:
    """End-to-end workflow for PM competency item lifecycle."""

    def __init__(self) -> None:
        self.generator = ItemGeneratorAgent()
        self.internal_qa = InternalQAAgent()
        self.external_review = ExternalLLMReviewAgent()
        self.revision = ItemRevisionAgent()
        self.persona_simulator = PersonaSimulationAgent()
        self.predictor = ErrorRatePredictorAgent()
        self.analytics = PostExamAnalyticsAgent()
        self.persona_updater = PersonaUpdaterAgent()

    def run(self, blueprint: Iterable[Dict[str, str]], actual_wrong_rate: Dict[str, float]) -> PipelineResult:
        items = self.generator.generate(blueprint)
        internal_issues = self.internal_qa.review(items)
        external_issues = self.external_review.review(items)
        merged_issues = internal_issues + external_issues

        revised_items = self.revision.revise(items, merged_issues)
        persona_predictions = self.persona_simulator.predict(revised_items)

        predicted_item_rates = self.predictor.predict_item_wrong_rate(persona_predictions)
        error_report = self.analytics.compare(predicted_item_rates, actual_wrong_rate)

        updated_weights = self.persona_updater.update(self.persona_simulator.persona_weights, error_report)

        return PipelineResult(
            items=revised_items,
            issues=merged_issues,
            persona_predictions=persona_predictions,
            error_report=error_report,
            updated_persona_weights=updated_weights,
        )


def default_blueprint() -> List[Dict[str, str]]:
    return [
        {"competency": "이해관계자 관리", "level": "Core"},
        {"competency": "우선순위 설정", "level": "Core"},
        {"competency": "리스크 관리", "level": "Advanced"},
    ]
