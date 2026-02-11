from pmc_multi_agent.workflow import MultiAgentWorkflow, default_blueprint


def test_workflow_runs_and_produces_deviation():
    workflow = MultiAgentWorkflow()
    actual = {"PM-001": 0.5, "PM-002": 0.4, "PM-003": 0.7}

    result = workflow.run(default_blueprint(), actual)

    assert len(result.items) == 3
    assert len(result.error_report) == 3
    assert result.mean_abs_deviation >= 0
    assert set(result.updated_persona_weights.keys()) == {"junior_pm", "mid_pm", "career_switcher"}


def test_advanced_item_has_higher_predicted_wrong_probability():
    workflow = MultiAgentWorkflow()
    actual = {"PM-001": 0.5, "PM-002": 0.4, "PM-003": 0.7}

    result = workflow.run(default_blueprint(), actual)

    by_item = {}
    for row in result.persona_predictions:
        by_item.setdefault(row.item_id, []).append(row.predicted_wrong_probability)

    avg_basic = sum(by_item["PM-001"]) / len(by_item["PM-001"])
    avg_advanced = sum(by_item["PM-003"]) / len(by_item["PM-003"])

    assert avg_advanced > avg_basic
