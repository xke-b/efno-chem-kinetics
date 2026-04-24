#!/usr/bin/env python3
"""Compare the best teacher-forced EFNO branch against the seeded supervised reference."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path("/root/workspace")
OUT = ROOT / "artifacts" / "experiments" / "h2_teacherforced_vs_supervised_comparison"
OUT.mkdir(parents=True, exist_ok=True)

SUPERVISED_SUMMARY = ROOT / "artifacts" / "experiments" / "h2_temp_species_seeded_replicates" / "summary.json"
TEACHER_SUMMARY = ROOT / "artifacts" / "experiments" / "h2_efno_teacher_forced_rollout_ablation" / "summary.json"

SUP_CASE = "supervised_deltaT_25ep"
BASE_EFNO_CASE = "baseline_tempw_0p1_speciesw_4p0"
BEST_TEACHER_CASE = "teacherforced_rollout0p1_tempw_0p1_speciesw_4p0"

METRICS = [
    "one_step_species_mae",
    "one_step_temperature_mae",
    "one_step_element_mass_mae",
    "rollout_species_mae_h1000",
    "rollout_temperature_mae_h1000",
    "rollout_element_mass_mae_h1000",
]


def load_case(path: Path, case_name: str) -> dict:
    data = json.loads(path.read_text())
    return data["cases"][case_name]



def mean_metric(case: dict, metric: str) -> float:
    return float(case["aggregate"][metric]["mean"])



def pct_change(candidate: float, baseline: float) -> float:
    return 100.0 * (candidate - baseline) / baseline



def main() -> None:
    supervised = load_case(SUPERVISED_SUMMARY, SUP_CASE)
    base_efno = load_case(TEACHER_SUMMARY, BASE_EFNO_CASE)
    teacher = load_case(TEACHER_SUMMARY, BEST_TEACHER_CASE)

    report = {
        "supervised_case": SUP_CASE,
        "base_efno_case": BASE_EFNO_CASE,
        "best_teacherforced_case": BEST_TEACHER_CASE,
        "metrics": {},
    }

    for metric in METRICS:
        s = mean_metric(supervised, metric)
        b = mean_metric(base_efno, metric)
        t = mean_metric(teacher, metric)
        report["metrics"][metric] = {
            "supervised_mean": s,
            "base_efno_mean": b,
            "teacherforced_mean": t,
            "teacherforced_vs_supervised_pct": pct_change(t, s),
            "teacherforced_vs_base_efno_pct": pct_change(t, b),
            "lower_is_better_winner": min(
                [
                    ("supervised", s),
                    ("base_efno", b),
                    ("teacherforced", t),
                ],
                key=lambda x: x[1],
            )[0],
        }

    out_path = OUT / "summary.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
