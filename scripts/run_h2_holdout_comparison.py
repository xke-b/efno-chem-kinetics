#!/usr/bin/env python3
"""Train/evaluate H2 models with a holdout split by initial-condition trajectory.

This addresses a key weakness of same-dataset evaluation by holding out entire
initial-condition trajectories, then evaluating rollout behavior only on unseen
trajectories.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np

ROOT = Path("/root/workspace")
MECH = "/opt/src/deepflame-dev/mechanisms/H2/ES80_H2-7-16.yaml"
DATA = ROOT / "data" / "h2_autoignition_longprobe.npy"
META = ROOT / "data" / "h2_autoignition_longprobe.json"
EXP_DIR = ROOT / "artifacts" / "experiments" / "h2_holdout_comparison"
EXP_DIR.mkdir(parents=True, exist_ok=True)

TRAIN_DATA = ROOT / "data" / "h2_autoignition_longprobe_train.npy"
TRAIN_META = ROOT / "data" / "h2_autoignition_longprobe_train.json"
TEST_DATA = ROOT / "data" / "h2_autoignition_longprobe_test.npy"
TEST_META = ROOT / "data" / "h2_autoignition_longprobe_test.json"


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def ensure_longprobe_dataset() -> None:
    if DATA.exists() and META.exists():
        return
    run(
        [
            "python",
            str(ROOT / "scripts" / "generate_h2_autoignition_pairs.py"),
            "--mech",
            MECH,
            "--out",
            str(DATA),
            "--metadata-out",
            str(META),
            "--n-init",
            "16",
            "--steps",
            "1000",
            "--dt",
            "1e-7",
            "--reactor",
            "const_pressure",
            "--seed",
            "13",
        ]
    )


def make_split() -> dict:
    meta = json.loads(META.read_text())
    data = np.load(DATA)
    n_init = meta["n_init"]
    steps = meta["steps"]
    state_width = 2 + meta["n_species"]
    traj = data.reshape(n_init, steps, 2 * state_width)

    holdout_ids = list(range(max(0, n_init - 4), n_init))
    train_ids = [i for i in range(n_init) if i not in holdout_ids]

    train = traj[train_ids].reshape(-1, 2 * state_width)
    test = traj[holdout_ids].reshape(-1, 2 * state_width)
    np.save(TRAIN_DATA, train)
    np.save(TEST_DATA, test)

    train_meta = dict(meta)
    train_meta["n_init"] = len(train_ids)
    train_meta["dataset_shape"] = list(train.shape)
    train_meta["trajectory_ids"] = train_ids
    TRAIN_META.write_text(json.dumps(train_meta, indent=2), encoding="utf-8")

    test_meta = dict(meta)
    test_meta["n_init"] = len(holdout_ids)
    test_meta["dataset_shape"] = list(test.shape)
    test_meta["trajectory_ids"] = holdout_ids
    TEST_META.write_text(json.dumps(test_meta, indent=2), encoding="utf-8")

    return {
        "train_ids": train_ids,
        "holdout_ids": holdout_ids,
        "train_shape": list(train.shape),
        "test_shape": list(test.shape),
    }


def train_model(name: str, trainer_name: str, trainer_params: dict | None = None) -> Path:
    ckpt = ROOT / "data" / f"{name}.pt"
    py = f'''
from dfode_kit.training.train import train
from dfode_kit.training.config import TrainingConfig, ModelConfig, OptimizerConfig, TrainerConfig
cfg = TrainingConfig(
    model=ModelConfig(name='mlp', params={{'hidden_layers':[64,64]}}),
    optimizer=OptimizerConfig(name='adam', lr=1e-3),
    trainer=TrainerConfig(name='{trainer_name}', max_epochs=10, lr_decay_epoch=5, lr_decay_factor=0.5, batch_size=512, params={trainer_params or {}}),
    time_step=1e-7,
)
train('{MECH}','{TRAIN_DATA}','{ckpt}',1e-7,cfg)
'''
    run(["python", "-c", py])
    return ckpt


def evaluate_model(ckpt: Path, out_json: Path) -> dict:
    run(
        [
            "python",
            str(ROOT / "scripts" / "evaluate_species_delta_checkpoint.py"),
            "--checkpoint",
            str(ckpt),
            "--dataset",
            str(TEST_DATA),
            "--metadata",
            str(TEST_META),
            "--out",
            str(out_json),
        ]
    )
    return json.loads(out_json.read_text())


def main() -> None:
    ensure_longprobe_dataset()
    split = make_split()

    baseline_ckpt = train_model(
        "h2_holdout_mlp_supervised_physics",
        "supervised_physics",
        {},
    )
    efno_ckpt = train_model(
        "h2_holdout_mlp_efno_style",
        "efno_style",
        {"lambda_data": 1.0, "lambda_elements": 1.0, "lambda_mass": 1.0},
    )

    baseline_eval = evaluate_model(baseline_ckpt, EXP_DIR / "baseline_holdout_eval.json")
    efno_eval = evaluate_model(efno_ckpt, EXP_DIR / "efno_holdout_eval.json")

    summary = {
        "split": split,
        "baseline": baseline_eval,
        "efno_style": efno_eval,
    }
    (EXP_DIR / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
