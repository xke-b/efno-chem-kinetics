#!/usr/bin/env python3
"""Small loss-weight sweep for temperature+species EFNO-style holdout training."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path("/root/workspace")
MECH = "/opt/src/deepflame-dev/mechanisms/H2/ES80_H2-7-16.yaml"
TRAIN_DATA = ROOT / "data" / "h2_autoignition_longprobe_train.npy"
TEST_DATA = ROOT / "data" / "h2_autoignition_longprobe_test.npy"
TEST_META = ROOT / "data" / "h2_autoignition_longprobe_test.json"
EXP_DIR = ROOT / "artifacts" / "experiments" / "h2_temp_species_efno_weight_sweep"
EXP_DIR.mkdir(parents=True, exist_ok=True)

CASES = [
    {"name": "tempw_1p0_speciesw_1p0", "temperature_loss_weight": 1.0, "species_loss_weight": 1.0},
    {"name": "tempw_0p1_speciesw_1p0", "temperature_loss_weight": 0.1, "species_loss_weight": 1.0},
    {"name": "tempw_0p01_speciesw_1p0", "temperature_loss_weight": 0.01, "species_loss_weight": 1.0},
    {"name": "tempw_0p1_speciesw_2p0", "temperature_loss_weight": 0.1, "species_loss_weight": 2.0},
]


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def train_and_eval(case: dict) -> dict:
    ckpt = ROOT / "data" / f"h2_holdout_mlp_efno_style_{case['name']}.pt"
    params = {
        "target_mode": "temperature_species",
        "lambda_data": 1.0,
        "lambda_elements": 1.0,
        "lambda_mass": 1.0,
        "temperature_loss_weight": case["temperature_loss_weight"],
        "species_loss_weight": case["species_loss_weight"],
    }
    train_py = f'''
from dfode_kit.training.train import train
from dfode_kit.training.config import TrainingConfig, ModelConfig, OptimizerConfig, TrainerConfig
cfg = TrainingConfig(
    model=ModelConfig(name="mlp", params={{"hidden_layers":[64,64]}}),
    optimizer=OptimizerConfig(name="adam", lr=1e-3),
    trainer=TrainerConfig(
        name="efno_style",
        max_epochs=10,
        lr_decay_epoch=5,
        lr_decay_factor=0.5,
        batch_size=512,
        params={json.dumps(params)},
    ),
    time_step=1e-7,
)
train("{MECH}", "{TRAIN_DATA}", "{ckpt}", 1e-7, cfg)
'''
    run(["python", "-c", train_py])

    out = EXP_DIR / f"{case['name']}_eval.json"
    run([
        "python",
        str(ROOT / "scripts" / "evaluate_species_delta_checkpoint.py"),
        "--checkpoint", str(ckpt),
        "--dataset", str(TEST_DATA),
        "--metadata", str(TEST_META),
        "--out", str(out),
    ])
    metrics = json.loads(out.read_text())
    metrics["sweep_case"] = case
    return metrics


def main() -> None:
    results = [train_and_eval(case) for case in CASES]
    summary = {
        "cases": results,
        "ranking_by_one_step_species_mae": [
            {
                "name": item["sweep_case"]["name"],
                "one_step_species_mae": item["one_step_species_mae"],
                "one_step_temperature_mae": item["one_step_temperature_mae"],
                "rollout_species_mae_h1000": item["rollout_species_mae_by_horizon"][-1],
                "rollout_temperature_mae_h1000": item["rollout_temperature_mae_by_horizon"][-1],
            }
            for item in sorted(results, key=lambda x: x["one_step_species_mae"])
        ],
    }
    (EXP_DIR / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
