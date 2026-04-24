#!/usr/bin/env python3
"""Run a small reproducible H2 trainer comparison experiment.

This script compares the current DFODE-kit baseline trainer against the new
EFNO-style trainer on a modest autoignition dataset, then evaluates the saved
checkpoints with rollout/physical-consistency metrics.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from dfode_kit.training.config import ModelConfig, OptimizerConfig, TrainerConfig, TrainingConfig
from dfode_kit.training.train import train


ROOT = Path("/root/workspace")
MECH = "/opt/src/deepflame-dev/mechanisms/H2/ES80_H2-7-16.yaml"
DATA_DIR = ROOT / "data"
ART_DIR = ROOT / "artifacts" / "experiments" / "h2_trainer_comparison_small"
ART_DIR.mkdir(parents=True, exist_ok=True)

DATASET = DATA_DIR / "h2_autoignition_smallcmp.npy"
METADATA = DATA_DIR / "h2_autoignition_smallcmp.json"


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def ensure_dataset() -> None:
    if DATASET.exists() and METADATA.exists():
        return
    run(
        [
            "python",
            str(ROOT / "scripts" / "generate_h2_autoignition_pairs.py"),
            "--mech",
            MECH,
            "--out",
            str(DATASET),
            "--metadata-out",
            str(METADATA),
            "--n-init",
            "64",
            "--steps",
            "50",
            "--dt",
            "1e-7",
            "--reactor",
            "const_pressure",
            "--seed",
            "11",
        ]
    )


def train_checkpoint(name: str, trainer_cfg: TrainerConfig) -> Path:
    ckpt = DATA_DIR / f"{name}.pt"
    cfg = TrainingConfig(
        model=ModelConfig(name="mlp", params={"hidden_layers": [64, 64]}),
        optimizer=OptimizerConfig(name="adam", lr=1e-3),
        trainer=trainer_cfg,
        time_step=1e-7,
    )
    train(
        mech_path=MECH,
        source_file=str(DATASET),
        output_path=str(ckpt),
        time_step=1e-7,
        config=cfg,
    )
    return ckpt


def evaluate_checkpoint(ckpt: Path, out_json: Path) -> dict:
    run(
        [
            "python",
            str(ROOT / "scripts" / "evaluate_species_delta_checkpoint.py"),
            "--checkpoint",
            str(ckpt),
            "--dataset",
            str(DATASET),
            "--metadata",
            str(METADATA),
            "--out",
            str(out_json),
        ]
    )
    return json.loads(out_json.read_text())


def main() -> None:
    ensure_dataset()

    baseline_ckpt = train_checkpoint(
        "h2_autoignition_smallcmp_mlp_supervised_physics",
        TrainerConfig(
            name="supervised_physics",
            max_epochs=20,
            lr_decay_epoch=10,
            lr_decay_factor=0.5,
            batch_size=128,
        ),
    )
    efno_style_ckpt = train_checkpoint(
        "h2_autoignition_smallcmp_mlp_efno_style",
        TrainerConfig(
            name="efno_style",
            max_epochs=20,
            lr_decay_epoch=10,
            lr_decay_factor=0.5,
            batch_size=128,
            params={"lambda_data": 1.0, "lambda_elements": 1.0, "lambda_mass": 1.0},
        ),
    )

    baseline_eval = evaluate_checkpoint(
        baseline_ckpt,
        ART_DIR / "baseline_eval.json",
    )
    efno_style_eval = evaluate_checkpoint(
        efno_style_ckpt,
        ART_DIR / "efno_style_eval.json",
    )

    summary = {
        "dataset": str(DATASET),
        "metadata": str(METADATA),
        "baseline": baseline_eval,
        "efno_style": efno_style_eval,
    }
    (ART_DIR / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
