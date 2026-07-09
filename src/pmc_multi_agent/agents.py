from __future__ import annotations

from dataclasses import replace
from statistics import mean
from typing import Dict, Iterable, List

from .models import ExamItem, ForecastVsActual, PersonaResult, ReviewIssue


class ItemGeneratorAgent:
    """Creates candidate PM competency exam items from a competency map."""

    def generate(self, blueprint: Iterable[Dict[str, str]]) -> List[ExamItem]:
        items: List[ExamItem] = []
        for idx, row in enumerate(blueprint, start=1):
            competency = row["competency"]
            level = row["level"]
            stem = f"[{competency}] 상황에서 가장 적절한 PM 의사결정은 무엇인가?"
            choices = [
                "문제 정의 없이 즉시 실행한다.",
                "이해관계자 목표를 정렬한 뒤 우선순위를 재설정한다.",
                "팀 의견 대신 개인 경험만으로 결정한다.",
                "리스크를 무시하고 일정만 단축한다.",
            ]
            item = ExamItem(
                item_id=f"PM-{idx:03}",
                competency=competency,
                level=level,
                stem=stem,
                choices=choices,
                answer_index=1,
                rationale="목표 정렬과 우선순위 재설정은 PM 핵심 역량이다.",
                metadata={"source": "generator-v1"},
            )
            items.append(item)
        return items


class InternalQAAgent:
    """Rule-based internal quality checks."""

    def review(self, items: List[ExamItem]) -> List[ReviewIssue]:
        issues: List[ReviewIssue] = []
        for item in items:
            if len(item.choices) < 4:
                issues.append(ReviewIssue(item.item_id, "internal-qa", "high", "선택지는 4개 이상이어야 합니다."))
            if not (0 <= item.answer_index < len(item.choices)):
                issues.append(ReviewIssue(item.item_id, "internal-qa", "high", "정답 인덱스가 유효하지 않습니다."))
            if len(item.stem) < 20:
                issues.append(ReviewIssue(item.item_id, "internal-qa", "medium", "문항 길이가 너무 짧습니다."))
        return issues


class ExternalLLMReviewAgent:
    """Simulated second-model review for ambiguity and rationale quality."""

    def review(self, items: List[ExamItem]) -> List[ReviewIssue]:
        issues: List[ReviewIssue] = []
        for item in items:
            if "가장" not in item.stem:
                issues.append(ReviewIssue(item.item_id, "external-llm", "medium", "판단 기준이 약해 모호할 수 있습니다."))
            if "핵심 역량" not in item.rationale:
                issues.append(ReviewIssue(item.item_id, "external-llm", "low", "해설에 역량 연결성이 약합니다."))
        return issues


class PersonaSimulationAgent:
    """Estimates wrong-answer probability by persona."""

    def __init__(self, persona_weights: Dict[str, float] | None = None) -> None:
        self.persona_weights = persona_weights or {
            "junior_pm": 0.62,
            "mid_pm": 0.38,
            "career_switcher": 0.55,
        }

    def predict(self, items: List[ExamItem]) -> List[PersonaResult]:
        results: List[PersonaResult] = []
        for item in items:
            difficulty_factor = 0.06 if item.level.lower().startswith("advanced") else 0.0
            for persona, weight in self.persona_weights.items():
                wrong_prob = min(max(weight + difficulty_factor, 0.05), 0.95)
                results.append(
                    PersonaResult(
                        item_id=item.item_id,
                        persona_name=persona,
                        predicted_wrong_probability=round(wrong_prob, 3),
                    )
                )
        return results


class ErrorRatePredictorAgent:
    """Aggregates persona predictions into per-item expected wrong rate."""

    def predict_item_wrong_rate(self, persona_results: List[PersonaResult]) -> Dict[str, float]:
        bucket: Dict[str, List[float]] = {}
        for result in persona_results:
            bucket.setdefault(result.item_id, []).append(result.predicted_wrong_probability)
        return {item_id: round(mean(scores), 3) for item_id, scores in bucket.items()}


class PostExamAnalyticsAgent:
    """Compares expected vs observed wrong rate."""

    def compare(self, predicted_wrong_rate: Dict[str, float], actual_wrong_rate: Dict[str, float]) -> List[ForecastVsActual]:
        report: List[ForecastVsActual] = []
        for item_id, predicted in predicted_wrong_rate.items():
            if item_id not in actual_wrong_rate:
                continue
            report.append(
                ForecastVsActual(
                    item_id=item_id,
                    predicted_wrong_rate=predicted,
                    actual_wrong_rate=actual_wrong_rate[item_id],
                )
            )
        return report


class PersonaUpdaterAgent:
    """Updates persona baseline weights from prediction error trend."""

    def update(self, current_weights: Dict[str, float], error_report: List[ForecastVsActual]) -> Dict[str, float]:
        if not error_report:
            return current_weights

        avg_deviation = mean(row.deviation for row in error_report)
        adjusted: Dict[str, float] = {}
        for persona, weight in current_weights.items():
            nudged = weight + (avg_deviation * 0.2)
            adjusted[persona] = round(min(max(nudged, 0.05), 0.95), 3)
        return adjusted


class ItemRevisionAgent:
    """Applies issue-informed revisions to items."""

    def revise(self, items: List[ExamItem], issues: List[ReviewIssue]) -> List[ExamItem]:
        issue_by_item: Dict[str, List[ReviewIssue]] = {}
        for issue in issues:
            issue_by_item.setdefault(issue.item_id, []).append(issue)

        revised: List[ExamItem] = []
        for item in items:
            new_item = item
            for issue in issue_by_item.get(item.item_id, []):
                if "모호" in issue.message and "판단 기준" not in new_item.stem:
                    new_item = replace(new_item, stem=f"{new_item.stem} (판단 기준: 비즈니스 임팩트)")
            revised.append(new_item)
        return revised
