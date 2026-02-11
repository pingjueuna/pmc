from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from .workflow import MultiAgentWorkflow, default_blueprint


def main() -> None:
    parser = argparse.ArgumentParser(description="Run PM competency multi-agent pipeline")
    parser.add_argument(
        "--actual",
        default='{"PM-001":0.51,"PM-002":0.44,"PM-003":0.63}',
        help="JSON dictionary of item_id to actual wrong rate",
    )
    args = parser.parse_args()

    actual_wrong_rate = json.loads(args.actual)
    workflow = MultiAgentWorkflow()
    result = workflow.run(default_blueprint(), actual_wrong_rate)

    payload = {
        "items": [asdict(item) for item in result.items],
        "issues": [asdict(issue) for issue in result.issues],
        "error_report": [
            {
                **asdict(row),
                "deviation": round(row.deviation, 3),
            }
            for row in result.error_report
        ],
        "updated_persona_weights": result.updated_persona_weights,
        "mean_abs_deviation": round(result.mean_abs_deviation, 3),
    }

    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
