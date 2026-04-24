#!/usr/bin/env python3
"""Analyze which normalized second-step feature components dominate self-vs-teacher gap."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch

from dfode_kit.models.mlp import build_mlp
from dfode_kit.training.config import ModelConfig, OptimizerConfig, TrainerConfig
from dfode_kit.training.efno_style import EFNOStyleTrainer
from dfode_kit.training.train import _prepare_training_tensors


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--dataset", required=True)
    p.add_argument("--out", required=True)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    ckpt = torch.load(args.checkpoint, map_location="cpu")
    training_cfg = ckpt["training_config"]
    model = build_mlp(
        model_config=ModelConfig(
            name=training_cfg["model"]["name"],
            params=training_cfg["model"]["params"],
        ),
        n_species=training_cfg["model"]["params"].get("output_dim", 7),
        device=torch.device("cpu"),
    )
    # n_species above is only used for output dims in builder path; correct from checkpoint output_dim path.
    model.load_state_dict(ckpt["net"])
    model.eval()

    trainer = EFNOStyleTrainer(
        TrainerConfig(name="efno_style", max_epochs=1, batch_size=512, params=training_cfg["trainer"]["params"]),
        OptimizerConfig(name=training_cfg["optimizer"]["name"], lr=training_cfg["optimizer"]["lr"]),
    )

    data = np.load(args.dataset)
    # infer n_species from feature mean length = 2+n_species
    n_species = len(ckpt["data_in_mean"]) - 2
    tensors = _prepare_training_tensors(
        data,
        n_species=n_species,
        device=torch.device("cpu"),
        target_mode=training_cfg["trainer"]["params"].get("target_mode", "species_only"),
    )

    with torch.no_grad():
        preds = model(tensors["features"])
        y_pred, *_ = trainer._decode_species_updates(
            batch_features=tensors["features"],
            batch_labels=tensors["labels"],
            preds=preds,
            features_mean=tensors["features_mean"],
            features_std=tensors["features_std"],
            labels_mean=tensors["labels_mean"],
            labels_std=tensors["labels_std"],
        )
        self_nf = trainer._build_next_features_norm(
            batch_features=tensors["features"],
            preds=preds,
            y_pred=y_pred,
            features_mean=tensors["features_mean"],
            features_std=tensors["features_std"],
            labels_mean=tensors["labels_mean"],
            labels_std=tensors["labels_std"],
            species_offset=1,
        )
        valid = tensors["rollout_mask"] > 0.5
        teacher_nf = tensors["rollout_next_features"][valid]
        self_nf = self_nf[valid]
        abs_diff = torch.abs(self_nf - teacher_nf)
        mean_abs_by_component = abs_diff.mean(dim=0)
        median_abs_by_component = abs_diff.median(dim=0).values
        max_abs_by_component = abs_diff.max(dim=0).values

    component_names = ["temperature", "pressure"] + [f"bct_Y_{i}" for i in range(n_species)]
    report = {
        "checkpoint": args.checkpoint,
        "dataset": args.dataset,
        "valid_rollout_pairs": int(valid.sum().item()),
        "component_mean_abs_gap": {k: float(v) for k, v in zip(component_names, mean_abs_by_component.tolist())},
        "component_median_abs_gap": {k: float(v) for k, v in zip(component_names, median_abs_by_component.tolist())},
        "component_max_abs_gap": {k: float(v) for k, v in zip(component_names, max_abs_by_component.tolist())},
        "group_means": {
            "temperature": float(mean_abs_by_component[0].item()),
            "pressure": float(mean_abs_by_component[1].item()),
            "species_bct_mean": float(mean_abs_by_component[2:].mean().item()),
            "overall_feature_mean_abs_gap": float(mean_abs_by_component.mean().item()),
        },
    }
    Path(args.out).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
