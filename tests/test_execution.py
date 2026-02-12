from pmc_multi_agent.execution import ExecutionRunner
from pmc_multi_agent.workflow import default_blueprint


def test_execution_runner_returns_stage_data():
    runner = ExecutionRunner()
    payload, stages = runner.run_with_stages(
        default_blueprint(),
        {"PM-001": 0.5, "PM-002": 0.4, "PM-003": 0.7},
    )

    assert "items" in payload
    assert "error_report" in payload
    assert len(stages) == 8
    assert stages[0]["name"] == "generate_items"
    assert stages[-1]["name"] == "update_personas"
    assert all(stage["duration_ms"] >= 0 for stage in stages)
