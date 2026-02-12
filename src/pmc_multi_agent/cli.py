from __future__ import annotations

import argparse
import json

from .execution import ExecutionRunner
from .workflow import default_blueprint


def main() -> None:
    parser = argparse.ArgumentParser(description="Run PM competency multi-agent pipeline")
    parser.add_argument(
        "--actual",
        default='{"PM-001":0.51,"PM-002":0.44,"PM-003":0.63}',
        help="JSON dictionary of item_id to actual wrong rate",
    )
    parser.add_argument(
        "--show-stages",
        action="store_true",
        help="Include stage-by-stage execution information",
    )
    args = parser.parse_args()

    actual_wrong_rate = json.loads(args.actual)
    runner = ExecutionRunner()
    payload, stages = runner.run_with_stages(default_blueprint(), actual_wrong_rate)

    if args.show_stages:
        payload["stages"] = stages

    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
