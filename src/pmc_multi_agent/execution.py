from __future__ import annotations

from dataclasses import asdict
from time import perf_counter
from typing import Dict, Iterable, List, Tuple

from .workflow import MultiAgentWorkflow


class ExecutionRunner:
    """Stage-by-stage executor for visibility into pipeline runtime flow."""

    def __init__(self, workflow: MultiAgentWorkflow | None = None) -> None:
        self.workflow = workflow or MultiAgentWorkflow()

    def run_with_stages(
        self, blueprint: Iterable[Dict[str, str]], actual_wrong_rate: Dict[str, float]
    ) -> Tuple[Dict[str, object], List[Dict[str, object]]]:
        stages: List[Dict[str, object]] = []

        t0 = perf_counter()
        items = self.workflow.generator.generate(blueprint)
        stages.append(_stage("generate_items", t0, perf_counter(), {"item_count": len(items)}))

        t1 = perf_counter()
        internal_issues = self.workflow.internal_qa.review(items)
        stages.append(_stage("internal_review", t1, perf_counter(), {"issue_count": len(internal_issues)}))

        t2 = perf_counter()
        external_issues = self.workflow.external_review.review(items)
        stages.append(_stage("external_review", t2, perf_counter(), {"issue_count": len(external_issues)}))

        merged_issues = internal_issues + external_issues

        t3 = perf_counter()
        revised_items = self.workflow.revision.revise(items, merged_issues)
        stages.append(_stage("revise_items", t3, perf_counter(), {"revised_count": len(revised_items)}))

        t4 = perf_counter()
        persona_predictions = self.workflow.persona_simulator.predict(revised_items)
        stages.append(
            _stage(
                "persona_simulation",
                t4,
                perf_counter(),
                {"prediction_count": len(persona_predictions)},
            )
        )

        t5 = perf_counter()
        predicted_item_rates = self.workflow.predictor.predict_item_wrong_rate(persona_predictions)
        stages.append(
            _stage(
                "predict_wrong_rate",
                t5,
                perf_counter(),
                {"item_count": len(predicted_item_rates)},
            )
        )

        t6 = perf_counter()
        error_report = self.workflow.analytics.compare(predicted_item_rates, actual_wrong_rate)
        stages.append(_stage("compare_actuals", t6, perf_counter(), {"rows": len(error_report)}))

        t7 = perf_counter()
        updated_weights = self.workflow.persona_updater.update(
            self.workflow.persona_simulator.persona_weights, error_report
        )
        stages.append(_stage("update_personas", t7, perf_counter(), {"persona_count": len(updated_weights)}))

        mean_abs_deviation = 0.0
        if error_report:
            mean_abs_deviation = sum(abs(row.deviation) for row in error_report) / len(error_report)

        payload: Dict[str, object] = {
            "items": [asdict(item) for item in revised_items],
            "issues": [asdict(issue) for issue in merged_issues],
            "error_report": [
                {
                    **asdict(row),
                    "deviation": round(row.deviation, 3),
                }
                for row in error_report
            ],
            "updated_persona_weights": updated_weights,
            "mean_abs_deviation": round(mean_abs_deviation, 3),
        }
        return payload, stages


def _stage(name: str, start: float, end: float, metrics: Dict[str, object]) -> Dict[str, object]:
    return {
        "name": name,
        "duration_ms": round((end - start) * 1000, 3),
        "metrics": metrics,
    }
