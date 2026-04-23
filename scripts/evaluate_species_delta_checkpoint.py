#!/usr/bin/env python3
"""Evaluate DFODE-kit species-delta checkpoints on paired trajectory data.

This evaluator is intentionally aligned with the *current* DFODE-kit training
contract, not the final EFNO paper contract. It is therefore useful for:
- smoke validation
- exposing mismatches between the current baseline and the paper
- quick one-step / rollout checks for MLP and provisional FNO scaffolds
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch

from dfode_kit.models.fno1d import build_fno1d
from dfode_kit.models.mlp import build_mlp
from dfode_kit.training.config import ModelConfig
from dfode_kit.utils import BCT, inverse_BCT


BCT_LAMBDA = 0.1
BCT_INVERSE_FLOOR = -1.0 / BCT_LAMBDA + 1e-8


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--out", default=None, help="Optional JSON output path")
    return parser.parse_args()


def build_model_from_checkpoint(checkpoint: dict, n_species: int, device: torch.device):
    cfg = checkpoint.get("training_config", {})
    model_cfg = cfg.get("model", {})
    name = model_cfg.get("name", "mlp")
    params = model_cfg.get("params", {})
    model_config = ModelConfig(name=name, params=params)

    if name == "mlp":
        model = build_mlp(model_config=model_config, n_species=n_species, device=device)
    elif name == "fno1d":
        model = build_fno1d(model_config=model_config, n_species=n_species, device=device)
    else:
        raise ValueError(f"Unsupported checkpoint model '{name}'")

    state = checkpoint["net"]
    model.load_state_dict(state)
    model.eval()
    return model, name, params


def predict_next_species(model, checkpoint: dict, current: np.ndarray, device: torch.device) -> tuple[np.ndarray, bool]:
    n_species = (current.shape[0] - 2)
    y = np.clip(current[2:], 0.0, 1.0)
    features = np.hstack((current[:2], BCT(y, lam=BCT_LAMBDA))).astype(np.float32)

    x = torch.tensor(features, dtype=torch.float32, device=device).unsqueeze(0)
    x_mean = torch.tensor(checkpoint["data_in_mean"], dtype=torch.float32, device=device).unsqueeze(0)
    x_std = torch.tensor(checkpoint["data_in_std"], dtype=torch.float32, device=device).unsqueeze(0)
    y_mean = torch.tensor(checkpoint["data_target_mean"], dtype=torch.float32, device=device).unsqueeze(0)
    y_std = torch.tensor(checkpoint["data_target_std"], dtype=torch.float32, device=device).unsqueeze(0)

    x_norm = (x - x_mean) / x_std
    with torch.no_grad():
        pred_norm = model(x_norm)

    base_bct = BCT(y[:-1], lam=BCT_LAMBDA).astype(np.float32)
    pred_bct = pred_norm.cpu().numpy()[0] * y_std.cpu().numpy()[0] + y_mean.cpu().numpy()[0] + base_bct
    invalid_inverse = bool(np.any(pred_bct <= BCT_INVERSE_FLOOR))
    pred_bct = np.maximum(pred_bct, BCT_INVERSE_FLOOR)
    pred_species = inverse_BCT(pred_bct, lam=BCT_LAMBDA)
    pred_species = np.clip(pred_species, 0.0, 1.0)
    last_species = max(0.0, 1.0 - float(pred_species.sum()))
    full_y = np.concatenate((pred_species, [last_species]))
    return full_y, invalid_inverse


def main() -> None:
    args = parse_args()
    dataset = np.load(args.dataset)
    metadata = json.loads(Path(args.metadata).read_text())
    checkpoint = torch.load(args.checkpoint, map_location="cpu")

    n_species = metadata["n_species"]
    state_width = 2 + n_species
    n_init = metadata["n_init"]
    steps = metadata["steps"]

    device = torch.device("cpu")
    model, model_name, model_params = build_model_from_checkpoint(checkpoint, n_species=n_species, device=device)

    current_states = dataset[:, :state_width]
    target_states = dataset[:, state_width:]

    one_step_outputs = [predict_next_species(model, checkpoint, row, device) for row in current_states]
    preds = np.vstack([item[0] for item in one_step_outputs])
    one_step_invalid_inverse_count = int(sum(1 for _, invalid in one_step_outputs if invalid))
    target_species = target_states[:, 2:]

    one_step_mae = float(np.mean(np.abs(preds - target_species)))
    one_step_rmse = float(np.sqrt(np.mean((preds - target_species) ** 2)))
    sum_error = float(np.mean(np.abs(preds.sum(axis=1) - 1.0)))

    rollout_maes = []
    trajectories = dataset.reshape(n_init, steps, 2 * state_width)
    for i in range(n_init):
        state = trajectories[i, 0, :state_width].copy()
        per_step_errors = []
        for j in range(steps):
            pred_y, invalid_inverse = predict_next_species(model, checkpoint, state, device)
            true_next = trajectories[i, j, state_width:]
            per_step_errors.append(float(np.mean(np.abs(pred_y - true_next[2:]))))
            state = state.copy()
            state[2:] = pred_y
        rollout_maes.append(per_step_errors)

    rollout_maes = np.asarray(rollout_maes)
    metrics = {
        "checkpoint": str(Path(args.checkpoint).resolve()),
        "dataset": str(Path(args.dataset).resolve()),
        "model_name": model_name,
        "model_params": model_params,
        "n_species": n_species,
        "one_step_species_mae": one_step_mae,
        "one_step_species_rmse": one_step_rmse,
        "one_step_mass_sum_mae": sum_error,
        "one_step_invalid_inverse_count": one_step_invalid_inverse_count,
        "rollout_species_mae_by_horizon": rollout_maes.mean(axis=0).tolist(),
        "notes": [
            "This evaluator only checks species prediction because the current DFODE-kit baseline does not predict temperature.",
            "Use this as baseline evidence and mismatch documentation, not as paper-faithful EFNO evaluation.",
        ],
    }

    text = json.dumps(metrics, indent=2)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
