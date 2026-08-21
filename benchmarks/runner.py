"""Agent-X Evaluation Benchmark Runner."""

import argparse
import json
import os
from typing import Any


def load_benchmark_scenarios(scenario_dir: str) -> list[dict[str, Any]]:
    scenarios: list[dict[str, Any]] = []
    if not os.path.exists(scenario_dir):
        return scenarios
    for filename in sorted(os.listdir(scenario_dir)):
        if filename.endswith(".json"):
            filepath = os.path.join(scenario_dir, filename)
            with open(filepath, encoding="utf-8") as f:
                scenarios.append(json.load(f))
    return scenarios


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent-X Evaluation Benchmark Runner")
    parser.add_argument("--suite", type=str, default="all", help="Suite name to execute")
    parser.add_argument("--concurrency", type=int, default=1, help="Concurrent test runs")
    args = parser.parse_args()

    print(f"Executing Agent-X Benchmark Suite: {args.suite} (concurrency: {args.concurrency})")
    scenarios = load_benchmark_scenarios("benchmarks/scenarios")
    print(f"Loaded {len(scenarios)} benchmark scenarios.")


if __name__ == "__main__":
    main()
