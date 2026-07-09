from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean
from typing import Dict, List


@dataclass
class ExamItem:
    """Represents one multiple-choice PM competency exam item."""

    item_id: str
    competency: str
    level: str
    stem: str
    choices: List[str]
    answer_index: int
    rationale: str
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class ReviewIssue:
    item_id: str
    source: str
    severity: str
    message: str


@dataclass
class PersonaResult:
    item_id: str
    persona_name: str
    predicted_wrong_probability: float


@dataclass
class ForecastVsActual:
    item_id: str
    predicted_wrong_rate: float
    actual_wrong_rate: float

    @property
    def deviation(self) -> float:
        return self.actual_wrong_rate - self.predicted_wrong_rate


@dataclass
class PipelineResult:
    items: List[ExamItem]
    issues: List[ReviewIssue]
    persona_predictions: List[PersonaResult]
    error_report: List[ForecastVsActual]
    updated_persona_weights: Dict[str, float]

    @property
    def mean_abs_deviation(self) -> float:
        if not self.error_report:
            return 0.0
        return mean(abs(row.deviation) for row in self.error_report)
