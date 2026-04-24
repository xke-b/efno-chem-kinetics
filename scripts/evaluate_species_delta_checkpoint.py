#!/usr/bin/env python3
"""Evaluate DFODE-kit paired-state checkpoints on paired trajectory data.

This evaluator supports both the earlier species-only target contract and the
new minimal thermochemical extension that predicts temperature + species.
It is still a project-side reproduction scaffold, not the final paper-faithful
EFNO evaluation stack.
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
from dfode_kit.utils import BCT, inverse_BCT, inverse_power_transform


BCT_LAMBDA = 0.1
BCT_INVERSE_FLOOR = -1.0 / BCT_LAMBDA + 1e-8


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--out", default=None, help="Optional JSON output path")
    parser.add_argument(
        "--species-postprocess-mode",
        choices=["closure", "preserve_last"],
        default="closure",
        help=(
            "How to reconstruct the final species mass fraction after inverse-BCT decoding. "
            "'closure' uses Y_last = 1 - sum(Y_main); 'preserve_last' matches the current "
            "DeepFlame PyTorch inference path by preserving the input last-species value and "
            "renormalizing the predicted main species to sum to 1 - Y_last,input."
        ),
    )
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


def build_element_mass_matrix(mech_path: str) -> np.ndarray:
    import cantera as ct

    gas = ct.Solution(mech_path)
    matrix = np.zeros((gas.n_species, gas.n_elements), dtype=np.float64)
    for s_idx, species in enumerate(gas.species()):
        molecular_weight = gas.molecular_weights[s_idx]
        for e_idx, element_name in enumerate(gas.element_names):
            n_atoms = species.composition.get(element_name, 0.0)
            if n_atoms == 0:
                continue
            matrix[s_idx, e_idx] = n_atoms * gas.atomic_weights[e_idx] / molecular_weight
    return matrix



def _decode_full_species(
    current_species: np.ndarray,
    decoded_main_species: np.ndarray,
    *,
    species_postprocess_mode: str,
) -> np.ndarray:
    pred_species = np.clip(decoded_main_species, 0.0, 1.0)

    if species_postprocess_mode == "closure":
        last_species = max(0.0, 1.0 - float(pred_species.sum()))
        return np.concatenate((pred_species, [last_species]))

    if species_postprocess_mode == "preserve_last":
        full_y = current_species.copy()
        full_y[:-1] = pred_species
        denom = float(np.sum(full_y[:-1]))
        if denom > 0.0:
            full_y[:-1] = full_y[:-1] / denom * (1.0 - full_y[-1])
        return full_y

    raise ValueError(f"Unsupported species_postprocess_mode '{species_postprocess_mode}'")



def predict_next_state(
    model,
    checkpoint: dict,
    current: np.ndarray,
    device: torch.device,
    *,
    species_postprocess_mode: str,
) -> tuple[np.ndarray, bool]:
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

    raw_pred = pred_norm.cpu().numpy()[0] * y_std.cpu().numpy()[0] + y_mean.cpu().numpy()[0]
    predicts_temperature = raw_pred.shape[0] == n_species
    target_mode = (
        checkpoint.get("training_config", {})
        .get("trainer", {})
        .get("params", {})
        .get("target_mode", "species_only")
    )

    if predicts_temperature and target_mode == "temperature_next_species":
        temp_next = float(raw_pred[0])
    elif predicts_temperature:
        temp_next = float(current[0] + raw_pred[0])
    else:
        temp_next = float(current[0])
    species_delta = raw_pred[1:] if predicts_temperature else raw_pred

    power_lambda = float(
        checkpoint.get("training_config", {})
        .get("trainer", {})
        .get("params", {})
        .get("power_lambda", 0.1)
    )
    if target_mode == "species_power_delta":
        decoded_main = np.clip(y[:-1] + inverse_power_transform(species_delta, lam=power_lambda), 0.0, 1.0)
        invalid_inverse = False
    else:
        base_bct = BCT(y[:-1], lam=BCT_LAMBDA).astype(np.float32)
        pred_bct = species_delta + base_bct
        invalid_inverse = bool(np.any(pred_bct <= BCT_INVERSE_FLOOR))
        pred_bct = np.maximum(pred_bct, BCT_INVERSE_FLOOR)
        decoded_main = inverse_BCT(pred_bct, lam=BCT_LAMBDA)
    full_y = _decode_full_species(y, decoded_main, species_postprocess_mode=species_postprocess_mode)
    full_state = np.concatenate(([temp_next, current[1]], full_y))
    return full_state, invalid_inverse


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

    one_step_outputs = [
        predict_next_state(
            model,
            checkpoint,
            row,
            device,
            species_postprocess_mode=args.species_postprocess_mode,
        )
        for row in current_states
    ]
    pred_states = np.vstack([item[0] for item in one_step_outputs])
    preds = pred_states[:, 2:]
    one_step_invalid_inverse_count = int(sum(1 for _, invalid in one_step_outputs if invalid))
    target_species = target_states[:, 2:]
    element_mass_matrix = build_element_mass_matrix(metadata["mech"])

    one_step_mae = float(np.mean(np.abs(preds - target_species)))
    one_step_rmse = float(np.sqrt(np.mean((preds - target_species) ** 2)))
    one_step_temperature_mae = float(np.mean(np.abs(pred_states[:, 0] - target_states[:, 0])))
    one_step_temperature_rmse = float(np.sqrt(np.mean((pred_states[:, 0] - target_states[:, 0]) ** 2)))
    sum_error = float(np.mean(np.abs(preds.sum(axis=1) - 1.0)))
    one_step_element_mae = float(
        np.mean(np.abs(preds @ element_mass_matrix - target_species @ element_mass_matrix))
    )

    rollout_maes = []
    rollout_temperature_maes = []
    rollout_mass_maes = []
    rollout_element_maes = []
    trajectories = dataset.reshape(n_init, steps, 2 * state_width)
    for i in range(n_init):
        state = trajectories[i, 0, :state_width].copy()
        per_step_errors = []
        per_step_temperature_errors = []
        per_step_mass_errors = []
        per_step_element_errors = []
        for j in range(steps):
            pred_state, invalid_inverse = predict_next_state(
                model,
                checkpoint,
                state,
                device,
                species_postprocess_mode=args.species_postprocess_mode,
            )
            true_next = trajectories[i, j, state_width:]
            pred_y = pred_state[2:]
            true_y = true_next[2:]
            per_step_errors.append(float(np.mean(np.abs(pred_y - true_y))))
            per_step_temperature_errors.append(float(abs(pred_state[0] - true_next[0])))
            per_step_mass_errors.append(float(abs(pred_y.sum() - 1.0)))
            per_step_element_errors.append(
                float(np.mean(np.abs(pred_y @ element_mass_matrix - true_y @ element_mass_matrix)))
            )
            state = pred_state.copy()
        rollout_maes.append(per_step_errors)
        rollout_temperature_maes.append(per_step_temperature_errors)
        rollout_mass_maes.append(per_step_mass_errors)
        rollout_element_maes.append(per_step_element_errors)

    rollout_maes = np.asarray(rollout_maes)
    rollout_temperature_maes = np.asarray(rollout_temperature_maes)
    rollout_mass_maes = np.asarray(rollout_mass_maes)
    rollout_element_maes = np.asarray(rollout_element_maes)
    metrics = {
        "checkpoint": str(Path(args.checkpoint).resolve()),
        "dataset": str(Path(args.dataset).resolve()),
        "model_name": model_name,
        "model_params": model_params,
        "n_species": n_species,
        "species_postprocess_mode": args.species_postprocess_mode,
        "one_step_species_mae": one_step_mae,
        "one_step_species_rmse": one_step_rmse,
        "one_step_temperature_mae": one_step_temperature_mae,
        "one_step_temperature_rmse": one_step_temperature_rmse,
        "one_step_mass_sum_mae": sum_error,
        "one_step_invalid_inverse_count": one_step_invalid_inverse_count,
        "one_step_element_mass_mae": one_step_element_mae,
        "rollout_species_mae_by_horizon": rollout_maes.mean(axis=0).tolist(),
        "rollout_temperature_mae_by_horizon": rollout_temperature_maes.mean(axis=0).tolist(),
        "rollout_mass_sum_mae_by_horizon": rollout_mass_maes.mean(axis=0).tolist(),
        "rollout_element_mass_mae_by_horizon": rollout_element_maes.mean(axis=0).tolist(),
        "notes": [
            "This evaluator supports both species-only and minimal temperature-plus-species project checkpoints.",
            f"Species postprocess mode: {args.species_postprocess_mode}.",
            "Use this as baseline evidence and mismatch documentation, not as paper-faithful EFNO evaluation.",
        ],
    }

    text = json.dumps(metrics, indent=2)
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
