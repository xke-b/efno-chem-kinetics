#!/usr/bin/env python3
"""Train/evaluate a minimal temperature+species holdout baseline on H2 autoignition."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path("/root/workspace")
MECH = "/opt/src/deepflame-dev/mechanisms/H2/ES80_H2-7-16.yaml"
TRAIN_DATA = ROOT / "data" / "h2_autoignition_longprobe_train.npy"
TEST_DATA = ROOT / "data" / "h2_autoignition_longprobe_test.npy"
TEST_META = ROOT / "data" / "h2_autoignition_longprobe_test.json"
CKPT = ROOT / "data" / "h2_holdout_mlp_supervised_physics_temp_species.pt"
OUT = ROOT / "artifacts" / "h2_holdout_mlp_supervised_physics_temp_species_eval.json"


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def main() -> None:
    train_py = f'''
from dfode_kit.training.train import train
from dfode_kit.training.config import TrainingConfig, ModelConfig, OptimizerConfig, TrainerConfig
cfg = TrainingConfig(
    model=ModelConfig(name="mlp", params={{"hidden_layers":[64,64]}}),
    optimizer=OptimizerConfig(name="adam", lr=1e-3),
    trainer=TrainerConfig(
        name="supervised_physics",
        max_epochs=5,
        lr_decay_epoch=5,
        lr_decay_factor=0.5,
        batch_size=512,
        params={{"target_mode":"temperature_species"}},
    ),
    time_step=1e-7,
)
train("{MECH}", "{TRAIN_DATA}", "{CKPT}", 1e-7, cfg)
'''
    run(["python", "-c", train_py])
    run([
        "python",
        str(ROOT / "scripts" / "evaluate_species_delta_checkpoint.py"),
        "--checkpoint", str(CKPT),
        "--dataset", str(TEST_DATA),
        "--metadata", str(TEST_META),
        "--out", str(OUT),
    ])
    print(json.dumps(json.loads(OUT.read_text()), indent=2))


if __name__ == "__main__":
    main()
