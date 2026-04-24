#!/usr/bin/env python3
"""Longer-training comparison for promising temperature+species holdout settings."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path("/root/workspace")
MECH = "/opt/src/deepflame-dev/mechanisms/H2/ES80_H2-7-16.yaml"
TRAIN_DATA = ROOT / "data" / "h2_autoignition_longprobe_train.npy"
TEST_DATA = ROOT / "data" / "h2_autoignition_longprobe_test.npy"
TEST_META = ROOT / "data" / "h2_autoignition_longprobe_test.json"
EXP_DIR = ROOT / "artifacts" / "experiments" / "h2_temp_species_longer_training_comparison"
EXP_DIR.mkdir(parents=True, exist_ok=True)
EPOCHS = 25
SEED = 0


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def train_model(name: str, trainer_name: str, trainer_params: dict) -> Path:
    ckpt = ROOT / "data" / f"{name}.pt"
    train_py = f'''
from dfode_kit.training.train import train
from dfode_kit.training.config import TrainingConfig, ModelConfig, OptimizerConfig, TrainerConfig
cfg = TrainingConfig(
    model=ModelConfig(name="mlp", params={{"hidden_layers":[64,64]}}),
    optimizer=OptimizerConfig(name="adam", lr=1e-3),
    trainer=TrainerConfig(
        name="{trainer_name}",
        max_epochs={EPOCHS},
        lr_decay_epoch=10,
        lr_decay_factor=0.5,
        batch_size=512,
        params={json.dumps(trainer_params)},
    ),
    time_step=1e-7,
    seed={SEED},
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


def main() -> None:
    configs = {
        "supervised_physics_25ep": {
            "trainer_name": "supervised_physics",
            "params": {"target_mode": "temperature_species"},
        },
        "efno_best_weighted_25ep": {
            "trainer_name": "efno_style",
            "params": {
                "target_mode": "temperature_species",
                "temperature_loss_weight": 0.1,
                "species_loss_weight": 2.0,
                "lambda_data": 1.0,
                "lambda_elements": 1.0,
                "lambda_mass": 1.0,
            },
        },
        "efno_best_weighted_lowmass_25ep": {
            "trainer_name": "efno_style",
            "params": {
                "target_mode": "temperature_species",
                "temperature_loss_weight": 0.1,
                "species_loss_weight": 2.0,
                "lambda_data": 1.0,
                "lambda_elements": 2.0,
                "lambda_mass": 0.1,
            },
        },
    }

    summary = {"epochs": EPOCHS, "seed": SEED, "results": {}}
    for name, cfg in configs.items():
        ckpt = train_model(f"h2_holdout_mlp_{name}", cfg["trainer_name"], cfg["params"])
        metrics = evaluate_model(ckpt, EXP_DIR / f"{name}_eval.json")
        summary["results"][name] = metrics

    ranking = []
    for name, metrics in summary["results"].items():
        ranking.append({
            "name": name,
            "one_step_species_mae": metrics["one_step_species_mae"],
            "one_step_temperature_mae": metrics["one_step_temperature_mae"],
            "one_step_element_mass_mae": metrics["one_step_element_mass_mae"],
            "rollout_species_mae_h1000": metrics["rollout_species_mae_by_horizon"][-1],
            "rollout_temperature_mae_h1000": metrics["rollout_temperature_mae_by_horizon"][-1],
        })
    summary["ranking_by_one_step_species_mae"] = sorted(ranking, key=lambda x: x["one_step_species_mae"])
    (EXP_DIR / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
