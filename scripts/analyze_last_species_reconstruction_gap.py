#!/usr/bin/env python3
"""Quantify the gap between two last-species reconstruction contracts.

Contracts compared:
1. evaluator_closure: main species are inverse-BCT decoded and the last species
   is reconstructed as 1 - sum(main species).
2. deepflame_preserve_last: main species are inverse-BCT decoded, then
   renormalized to preserve the input last-species mass fraction, matching the
   current DeepFlame PyTorch inference path.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch

from dfode_kit.models.mlp import MLP
from dfode_kit.training.config import ModelConfig
from dfode_kit.utils import BCT, inverse_BCT

BCT_LAMBDA = 0.1
BCT_INVERSE_FLOOR = -1.0 / BCT_LAMBDA + 1e-8


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--checkpoint', required=True)
    parser.add_argument('--dataset', required=True)
    parser.add_argument('--metadata', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--max-samples', type=int, default=None)
    return parser.parse_args()


def build_model(checkpoint: dict, n_species: int):
    cfg = checkpoint.get('training_config', {})
    model_cfg = cfg.get('model', {})
    params = model_cfg.get('params', {})
    hidden_layers = list(params.get('hidden_layers', [400, 400, 400, 400]))
    output_dim = int(params.get('output_dim', checkpoint['net'][f"net.linear_layer_{len(hidden_layers)}.weight"].shape[0]))
    model = MLP([2 + n_species, *hidden_layers, output_dim])
    model.load_state_dict(checkpoint['net'])
    model.eval()
    return model


def decode_species(raw_pred: np.ndarray, current: np.ndarray, *, preserve_last: bool, n_species: int) -> np.ndarray:
    y = np.clip(current[2:], 0.0, 1.0)
    species_raw = raw_pred[1:] if raw_pred.shape[0] == n_species else raw_pred
    pred_bct = np.maximum(BCT(y[:-1], lam=BCT_LAMBDA) + species_raw, BCT_INVERSE_FLOOR)
    main_species = np.clip(inverse_BCT(pred_bct, lam=BCT_LAMBDA), 0.0, 1.0)
    if preserve_last:
        out = y.copy()
        out[:-1] = main_species
        denom = np.sum(out[:-1], keepdims=True)
        if float(denom) > 0:
            out[:-1] = out[:-1] / denom * (1.0 - out[-1])
        return out
    last_species = max(0.0, 1.0 - float(main_species.sum()))
    return np.concatenate((main_species, [last_species]))


def main() -> None:
    args = parse_args()
    checkpoint = torch.load(args.checkpoint, map_location='cpu')
    metadata = json.loads(Path(args.metadata).read_text())
    dataset = np.load(args.dataset)

    n_species = int(metadata['n_species'])
    state_width = 2 + n_species
    model = build_model(checkpoint, n_species)

    current = dataset[:, :state_width]
    target = dataset[:, state_width:]
    if args.max_samples is not None:
        current = current[: args.max_samples]
        target = target[: args.max_samples]

    x_mean = np.asarray(checkpoint['data_in_mean'], dtype=np.float32)
    x_std = np.asarray(checkpoint['data_in_std'], dtype=np.float32)
    y_mean = np.asarray(checkpoint['data_target_mean'], dtype=np.float32)
    y_std = np.asarray(checkpoint['data_target_std'], dtype=np.float32)

    closure_preds = []
    preserve_preds = []
    per_sample_contract_gap = []
    for row in current:
        features = np.hstack((row[:2], BCT(np.clip(row[2:], 0.0, 1.0), lam=BCT_LAMBDA))).astype(np.float32)
        x_norm = torch.tensor(((features - x_mean) / x_std)[None, :], dtype=torch.float32)
        with torch.no_grad():
            pred_norm = model(x_norm).numpy()[0]
        raw_pred = pred_norm * y_std + y_mean
        closure_y = decode_species(raw_pred, row, preserve_last=False, n_species=n_species)
        preserve_y = decode_species(raw_pred, row, preserve_last=True, n_species=n_species)
        closure_preds.append(closure_y)
        preserve_preds.append(preserve_y)
        per_sample_contract_gap.append(np.max(np.abs(closure_y - preserve_y)))

    closure_preds = np.asarray(closure_preds)
    preserve_preds = np.asarray(preserve_preds)
    true_y = target[:, 2:]

    payload = {
        'checkpoint': str(Path(args.checkpoint).resolve()),
        'dataset': str(Path(args.dataset).resolve()),
        'n_species': n_species,
        'samples': int(len(current)),
        'contracts': {
            'evaluator_closure': {
                'one_step_species_mae': float(np.mean(np.abs(closure_preds - true_y))),
                'one_step_mass_sum_mae': float(np.mean(np.abs(np.sum(closure_preds, axis=1) - 1.0))),
            },
            'deepflame_preserve_last': {
                'one_step_species_mae': float(np.mean(np.abs(preserve_preds - true_y))),
                'one_step_mass_sum_mae': float(np.mean(np.abs(np.sum(preserve_preds, axis=1) - 1.0))),
            },
        },
        'contract_gap': {
            'max_abs_species_diff': float(np.max(np.abs(closure_preds - preserve_preds))),
            'mean_abs_species_diff': float(np.mean(np.abs(closure_preds - preserve_preds))),
            'mean_max_abs_species_diff_per_sample': float(np.mean(per_sample_contract_gap)),
            'max_max_abs_species_diff_per_sample': float(np.max(per_sample_contract_gap)),
        },
        'note': 'If this gap is non-negligible, offline evaluator summaries and deployable DeepFlame species behavior are using different last-species reconstruction contracts.',
    }

    Path(args.out).write_text(json.dumps(payload, indent=2), encoding='utf-8')
    print(json.dumps(payload, indent=2))


if __name__ == '__main__':
    main()
