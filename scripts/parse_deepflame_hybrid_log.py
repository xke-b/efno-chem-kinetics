#!/usr/bin/env python3
"""Parse DeepFlame hybrid-fallback smoke-run logs into per-time summaries."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

TIME_RE = re.compile(r"^Time = ([0-9eE+\-.]+)$")
ACTIVE_RE = re.compile(r"real inference points number: (\d+)")
FALLBACK_RE = re.compile(
    r"hybrid fallback cells: (\d+) \(hp_failures=(\d+), guard_only=(\d+)(?:, state_guard=(\d+))?\)"
)
TEMP_RE = re.compile(r"min/max\(T\) = ([0-9eE+\-.]+), ([0-9eE+\-.]+)")


def parse_log(path: Path) -> dict:
    lines = path.read_text().splitlines()
    summary: dict[str, dict] = {}
    current_time: str | None = None

    for line in lines:
        stripped = line.strip()
        m = TIME_RE.match(stripped)
        if m:
            current_time = m.group(1)
            summary.setdefault(
                current_time,
                {
                    "active_cells": 0,
                    "fallback_cells": 0,
                    "hp_failures": 0,
                    "guard_only": 0,
                    "state_guard": 0,
                },
            )
            continue

        if current_time is None:
            continue

        m = ACTIVE_RE.search(stripped)
        if m:
            summary[current_time]["active_cells"] += int(m.group(1))
            continue

        m = FALLBACK_RE.search(stripped)
        if m:
            summary[current_time]["fallback_cells"] += int(m.group(1))
            summary[current_time]["hp_failures"] += int(m.group(2))
            summary[current_time]["guard_only"] += int(m.group(3))
            if m.group(4) is not None:
                summary[current_time]["state_guard"] += int(m.group(4))
            continue

        m = TEMP_RE.search(stripped)
        if m:
            summary[current_time]["T_min"] = float(m.group(1))
            summary[current_time]["T_max"] = float(m.group(2))
            continue

    ordered_times = sorted(summary.keys(), key=lambda x: float(x))
    cumulative_fallback = 0
    cumulative_active = 0
    for t in ordered_times:
        item = summary[t]
        active = item["active_cells"]
        fallback = item["fallback_cells"]
        hp_failures = item["hp_failures"]
        guard_only = item["guard_only"]
        state_guard = item["state_guard"]
        learned = max(active - fallback, 0)
        cumulative_fallback += fallback
        cumulative_active += active
        item["learned_cells"] = learned
        item["fallback_fraction_active"] = (fallback / active) if active else 0.0
        item["hp_failure_fraction_active"] = (hp_failures / active) if active else 0.0
        item["guard_only_fraction_active"] = (guard_only / active) if active else 0.0
        item["state_guard_fraction_active"] = (state_guard / active) if active else 0.0
        item["learned_fraction_active"] = (learned / active) if active else 0.0
        item["cumulative_fallback_fraction_active"] = (
            cumulative_fallback / cumulative_active if cumulative_active else 0.0
        )

    return {
        "log_path": str(path),
        "completed": any("Finalising parallel run" in line for line in lines),
        "times": ordered_times,
        "by_time": summary,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("log_path")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    payload = parse_log(Path(args.log_path))
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
