#!/usr/bin/env python3
"""Compare temperature+species holdout trainers on H2 autoignition."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path("/root/workspace")
MECH = "/opt/src/deepflame-dev/mechanisms/H2/ES80_H2-7-16.yaml"
TRAIN_DATA = ROOT / "data" / "h2_autoignition_longprobe_train.npy"
TEST_DATA = ROOT / "data" / "h2_autoignition_longprobe_test.npy"
TEST_META = ROOT / "data" / "h2_autoignition_longprobe_test.json"
EXP_DIR = ROOT / "artifacts" / "experiments" / "h2_temp_species_holdout_comparison"
EXP_DIR.mkdir(parents=True, exist_ok=True)


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def train_model(name: str, trainer_name: str, trainer_params: dict, max_epochs: int = 10) -> Path:
    ckpt = ROOT / "data" / f"{name}.pt"
    train_py = f'''
from dfode_kit.training.train import train
from dfode_kit.training.config import TrainingConfig, ModelConfig, OptimizerConfig, TrainerConfig
cfg = TrainingConfig(
    model=ModelConfig(name="mlp", params={{"hidden_layers":[64,64]}}),
    optimizer=OptimizerConfig(name="adam", lr=1e-3),
    trainer=TrainerConfig(
        name="{trainer_name}",
        max_epochs={max_epochs},
        lr_decay_epoch=5,
        lr_decay_factor=0.5,
        batch_size=512,
        params={json.dumps(trainer_params)},
    ),
    time_step=1e-7,
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
    supervised_ckpt = train_model(
        "h2_holdout_mlp_supervised_physics_temp_species_10ep",
        "supervised_physics",
        {"target_mode": "temperature_species"},
        max_epochs=10,
    )
    efno_ckpt = train_model(
        "h2_holdout_mlp_efno_style_temp_species_10ep",
        "efno_style",
        {
            "target_mode": "temperature_species",
            "lambda_data": 1.0,
            "lambda_elements": 1.0,
            "lambda_mass": 1.0,
        },
        max_epochs=10,
    )

    supervised_eval = evaluate_model(supervised_ckpt, EXP_DIR / "supervised_temp_species_eval.json")
    efno_eval = evaluate_model(efno_ckpt, EXP_DIR / "efno_temp_species_eval.json")

    summary = {
        "supervised_physics_temp_species": supervised_eval,
        "efno_style_temp_species": efno_eval,
    }
    (EXP_DIR / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
