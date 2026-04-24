#!/usr/bin/env python3
"""Seeded noise-ablation for teacher-forced two-step EFNO on H2 holdout."""

from __future__ import annotations

import json
import statistics
import subprocess
from pathlib import Path

ROOT = Path("/root/workspace")
MECH = "/opt/src/deepflame-dev/mechanisms/H2/ES80_H2-7-16.yaml"
TRAIN_DATA = ROOT / "data" / "h2_autoignition_longprobe_train.npy"
TEST_DATA = ROOT / "data" / "h2_autoignition_longprobe_test.npy"
TEST_META = ROOT / "data" / "h2_autoignition_longprobe_test.json"
EXP_DIR = ROOT / "artifacts" / "experiments" / "h2_efno_teacher_forced_noise_ablation"
EXP_DIR.mkdir(parents=True, exist_ok=True)
EPOCHS = 25
SEEDS = [0, 1, 2]

BASE = {
    "target_mode": "temperature_species",
    "species_data_space": "bct_delta",
    "lambda_data": 1.0,
    "lambda_elements": 0.0,
    "lambda_mass": 0.0,
    "temperature_loss_weight": 0.1,
    "species_loss_weight": 4.0,
    "rollout_consistency_weight": 0.1,
    "rollout_consistency_mode": "teacher_forced",
}

CASES = {
    "teacherforced_rollout0p1_noise0p0": {
        **BASE,
        "rollout_feature_noise_std": 0.0,
    },
    "teacherforced_rollout0p1_noise0p05": {
        **BASE,
        "rollout_feature_noise_std": 0.05,
    },
    "teacherforced_rollout0p1_noise0p1": {
        **BASE,
        "rollout_feature_noise_std": 0.1,
    },
}

METRIC_KEYS = [
    "one_step_species_mae",
    "one_step_temperature_mae",
    "one_step_element_mass_mae",
]
ROLLOUT_KEYS = [
    ("rollout_species_mae_by_horizon", "rollout_species_mae_h1000"),
    ("rollout_temperature_mae_by_horizon", "rollout_temperature_mae_h1000"),
    ("rollout_element_mass_mae_by_horizon", "rollout_element_mass_mae_h1000"),
]


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)



def train_model(name: str, trainer_params: dict, seed: int) -> Path:
    ckpt = ROOT / "data" / f"h2_holdout_mlp_{name}_seed{seed}.pt"
    train_py = f'''
from dfode_kit.training.train import train
from dfode_kit.training.config import TrainingConfig, ModelConfig, OptimizerConfig, TrainerConfig
cfg = TrainingConfig(
    model=ModelConfig(name="mlp", params={{"hidden_layers":[64,64]}}),
    optimizer=OptimizerConfig(name="adam", lr=1e-3),
    trainer=TrainerConfig(
        name="efno_style",
        max_epochs={EPOCHS},
        lr_decay_epoch=10,
        lr_decay_factor=0.5,
        batch_size=512,
        params={json.dumps(trainer_params)},
    ),
    time_step=1e-7,
    seed={seed},
)
train("{MECH}", "{TRAIN_DATA}", "{ckpt}", 1e-7, cfg)
'''
    run(["python", "-c", train_py])
    return ckpt



def evaluate_model(ckpt: Path, out_json: Path) -> dict:
    run([
        "python",
        str(ROOT / "scripts" / "evaluate_species_delta_checkpoint.py"),
        "--checkpoint", str(ckpt),
        "--dataset", str(TEST_DATA),
        "--metadata", str(TEST_META),
        "--out", str(out_json),
    ])
    return json.loads(out_json.read_text())



def summarize_case(results: list[dict]) -> dict:
    summary = {"replicates": results, "aggregate": {}}
    for key in METRIC_KEYS:
        vals = [r[key] for r in results]
        summary["aggregate"][key] = {
            "mean": statistics.fmean(vals),
            "min": min(vals),
            "max": max(vals),
            "stdev": statistics.pstdev(vals),
        }
    for source_key, out_key in ROLLOUT_KEYS:
        vals = [r[source_key][-1] for r in results]
        summary["aggregate"][out_key] = {
            "mean": statistics.fmean(vals),
            "min": min(vals),
            "max": max(vals),
            "stdev": statistics.pstdev(vals),
        }
    return summary



def main() -> None:
    summary = {"epochs": EPOCHS, "seeds": SEEDS, "cases": {}}
    for case_name, trainer_params in CASES.items():
        case_results = []
        for seed in SEEDS:
            ckpt = train_model(case_name, trainer_params, seed)
            metrics = evaluate_model(ckpt, EXP_DIR / f"{case_name}_seed{seed}_eval.json")
            metrics["seed"] = seed
            case_results.append(metrics)
        summary["cases"][case_name] = summarize_case(case_results)

    ranking = []
    for case_name, payload in summary["cases"].items():
        agg = payload["aggregate"]
        ranking.append({
            "name": case_name,
            "one_step_species_mae_mean": agg["one_step_species_mae"]["mean"],
            "one_step_temperature_mae_mean": agg["one_step_temperature_mae"]["mean"],
            "one_step_element_mass_mae_mean": agg["one_step_element_mass_mae"]["mean"],
            "rollout_species_mae_h1000_mean": agg["rollout_species_mae_h1000"]["mean"],
            "rollout_temperature_mae_h1000_mean": agg["rollout_temperature_mae_h1000"]["mean"],
        })
    summary["ranking_by_rollout_species_mae_mean"] = sorted(ranking, key=lambda x: x["rollout_species_mae_h1000_mean"])
    (EXP_DIR / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
