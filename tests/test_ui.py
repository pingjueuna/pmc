from pmc_multi_agent.ui import run_payload


def test_run_payload_includes_stages():
    payload = run_payload({"PM-001": 0.51, "PM-002": 0.44, "PM-003": 0.63})

    assert "stages" in payload
    assert len(payload["stages"]) == 8
    assert payload["stages"][0]["name"] == "generate_items"
