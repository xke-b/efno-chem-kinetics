#!/usr/bin/env python3
"""Fit a simple logistic HP-failure risk model for DeepFlame H2 active states."""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

import cantera as ct
import numpy as np
import torch

SPECIES = ['H', 'H2', 'O', 'OH', 'H2O', 'O2', 'HO2', 'H2O2', 'N2']
BCT_LAMBDA = 0.1
BCT_INVERSE_FLOOR = -1.0 / BCT_LAMBDA + 1e-8


class DeepFlameScalarMLP(torch.nn.Module):
    def __init__(self, layer_info: list[int]):
        super().__init__()
        self.net = torch.nn.Sequential()
        n = len(layer_info) - 1
        for i in range(n - 1):
            self.net.add_module(f'linear_layer_{i}', torch.nn.Linear(layer_info[i], layer_info[i + 1]))
            self.net.add_module(f'gelu_layer_{i}', torch.nn.GELU())
        self.net.add_module(f'linear_layer_{n - 1}', torch.nn.Linear(layer_info[n - 1], layer_info[n]))

    def forward(self, x):
        return self.net(x)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument('--case', required=True)
    p.add_argument('--times', nargs='+', required=True)
    p.add_argument('--checkpoint', required=True)
    p.add_argument('--mechanism', required=True)
    p.add_argument('--frozen-temperature', type=float, default=650.0)
    p.add_argument('--out', required=True)
    return p.parse_args()


def read_internal_scalar_field(path: Path, fallback_n_cells: int | None = None) -> np.ndarray:
    with gzip.open(path, 'rt', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    n_cells = None
    for line in lines:
        stripped = line.strip()
        if stripped.isdigit():
            n_cells = int(stripped)
            break

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('internalField') and 'List<scalar>' in stripped:
            count = int(lines[i + 1].strip())
            start = i + 3
            return np.array([float(lines[start + j].strip()) for j in range(count)], dtype=np.float64)
        if stripped.startswith('internalField') and 'uniform' in stripped:
            if n_cells is None:
                n_cells = fallback_n_cells
            if n_cells is None:
                raise ValueError(f'Uniform field without resolvable cell count in {path}')
            value = float(stripped.split('uniform', 1)[1].replace(';', '').strip())
            return np.full(n_cells, value, dtype=np.float64)

    raise ValueError(f'Could not parse internalField from {path}')


def read_case_time_fields(case_dir: Path, time_name: str) -> dict[str, np.ndarray]:
    processor_dirs = sorted(p for p in case_dir.glob('processor*') if p.is_dir())
    fields = {name: [] for name in ['T', 'p', *SPECIES]}
    for proc_dir in processor_dirs:
        time_dir = proc_dir / time_name
        t_values = read_internal_scalar_field(time_dir / 'T.gz')
        fields['T'].append(t_values)
        fallback_n = len(t_values)
        fields['p'].append(read_internal_scalar_field(time_dir / 'p.gz', fallback_n_cells=fallback_n))
        for field_name in SPECIES:
            fields[field_name].append(read_internal_scalar_field(time_dir / f'{field_name}.gz', fallback_n_cells=fallback_n))
    return {name: np.concatenate(chunks) for name, chunks in fields.items()}


def BCT(x: np.ndarray, lam: float = BCT_LAMBDA) -> np.ndarray:
    x = np.clip(x, 1e-16, None)
    return (np.power(x, lam) - 1.0) / lam


def inverse_BCT(x: np.ndarray, lam: float = BCT_LAMBDA) -> np.ndarray:
    return np.power(np.maximum(lam * x + 1.0, 1e-16), 1.0 / lam)


def build_models(exported: dict, n_species: int):
    hidden_layers = list(exported['export_metadata']['hidden_layers'])
    models = []
    for i in range(n_species - 1):
        m = DeepFlameScalarMLP([2 + n_species, *hidden_layers, 1])
        m.load_state_dict(exported[f'net{i}'])
        m.eval()
        models.append(m)
    return models


def predict_next_species_batch(exported: dict, models, states: np.ndarray) -> np.ndarray:
    current = states.copy().astype(np.float64)
    current[:, 2:] = np.clip(current[:, 2:], 0.0, 1.0)
    input_y = current[:, 2:].copy()
    input_bct = current.copy()
    input_bct[:, 2:] = BCT(input_bct[:, 2:], lam=BCT_LAMBDA)

    x_mean = np.asarray(exported['data_in_mean'], dtype=np.float64)
    x_std = np.asarray(exported['data_in_std'], dtype=np.float64)
    inorm = ((input_bct - x_mean) / x_std).astype(np.float32)
    xt = torch.tensor(inorm, dtype=torch.float32)

    outs = []
    for m in models:
        with torch.no_grad():
            outs.append(m(xt).numpy())
    outs = np.concatenate(outs, axis=1)

    y_mean = np.asarray(exported['data_target_mean'], dtype=np.float32)
    y_std = np.asarray(exported['data_target_std'], dtype=np.float32)
    out_bct = outs * y_std + y_mean + input_bct[:, 2:-1]
    out_bct = np.maximum(out_bct, BCT_INVERSE_FLOOR)
    next_y = input_y.copy()
    next_y[:, :-1] = inverse_BCT(out_bct, lam=BCT_LAMBDA)
    denom = np.sum(next_y[:, :-1], axis=1, keepdims=True)
    valid = denom[:, 0] > 0.0
    next_y[valid, :-1] = next_y[valid, :-1] / denom[valid] * (1.0 - next_y[valid, -1:])
    return next_y


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -50.0, 50.0)))


def fit_logistic(X: np.ndarray, y: np.ndarray, lr: float = 0.1, epochs: int = 3000, reg: float = 1e-4):
    mu = X.mean(axis=0)
    sigma = X.std(axis=0)
    sigma[sigma == 0.0] = 1.0
    Xn = (X - mu) / sigma
    Xb = np.concatenate([Xn, np.ones((Xn.shape[0], 1))], axis=1)
    w = np.zeros(Xb.shape[1], dtype=np.float64)

    for _ in range(epochs):
        p = sigmoid(Xb @ w)
        grad = (Xb.T @ (p - y)) / len(y)
        grad[:-1] += reg * w[:-1]
        w -= lr * grad

    return {'weights': w, 'mean': mu, 'std': sigma}


def predict_logistic(model: dict, X: np.ndarray) -> np.ndarray:
    Xn = (X - model['mean']) / model['std']
    Xb = np.concatenate([Xn, np.ones((Xn.shape[0], 1))], axis=1)
    return sigmoid(Xb @ model['weights'])


def threshold_metrics(scores: np.ndarray, y: np.ndarray, threshold: float) -> dict:
    pred = scores >= threshold
    tp = int(np.sum(pred & (y == 1)))
    fp = int(np.sum(pred & (y == 0)))
    fn = int(np.sum((~pred) & (y == 1)))
    tn = int(np.sum((~pred) & (y == 0)))
    flagged = int(np.sum(pred))
    return {
        'threshold': float(threshold),
        'flagged_fraction': float(flagged / len(y)) if len(y) else 0.0,
        'recall': float(tp / (tp + fn)) if (tp + fn) else 0.0,
        'precision': float(tp / (tp + fp)) if (tp + fp) else 0.0,
        'specificity': float(tn / (tn + fp)) if (tn + fp) else 0.0,
        'tp': tp,
        'fp': fp,
        'fn': fn,
        'tn': tn,
    }


def rank_correlation_like(scores: np.ndarray, y: np.ndarray) -> float:
    order = np.argsort(scores)
    ranks = np.empty_like(order, dtype=np.float64)
    ranks[order] = np.arange(len(scores), dtype=np.float64)
    ys = y.astype(np.float64)
    if np.std(ranks) == 0.0 or np.std(ys) == 0.0:
        return 0.0
    return float(np.corrcoef(ranks, ys)[0, 1])


def main() -> None:
    args = parse_args()
    case_dir = Path(args.case)
    exported = torch.load(args.checkpoint, map_location='cpu')
    n_species = int(exported['export_metadata']['n_species'])
    models = build_models(exported, n_species)
    gas = ct.Solution(args.mechanism)

    feature_names = ['T', 'p', 'O2', 'H2O', 'OH']
    all_X = []
    all_y = []
    per_time = {}

    for time_name in args.times:
        fields = read_case_time_fields(case_dir, time_name)
        species = np.column_stack([fields[name] for name in SPECIES])
        states = np.column_stack([fields['T'], fields['p'], species])
        active_mask = fields['T'] > args.frozen_temperature
        active_states = states[active_mask]
        next_species = predict_next_species_batch(exported, models, active_states)
        failures = np.zeros(len(active_states), dtype=np.int64)
        for i, (state, y_next) in enumerate(zip(active_states, next_species)):
            try:
                gas.TPY = float(state[0]), float(state[1]), state[2:]
                h = gas.enthalpy_mass
                gas.Y = y_next
                gas.HP = h, float(state[1])
            except Exception:
                failures[i] = 1
        X = np.column_stack([
            active_states[:, 0],
            active_states[:, 1],
            active_states[:, 2 + SPECIES.index('O2')],
            active_states[:, 2 + SPECIES.index('H2O')],
            active_states[:, 2 + SPECIES.index('OH')],
        ])
        all_X.append(X)
        all_y.append(failures)
        per_time[time_name] = {'n_active': int(len(failures)), 'failure_fraction': float(np.mean(failures))}

    X = np.concatenate(all_X, axis=0)
    y = np.concatenate(all_y, axis=0)
    model = fit_logistic(X, y)
    scores = predict_logistic(model, X)

    thresholds = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
    metrics = [threshold_metrics(scores, y, thr) for thr in thresholds]

    per_time_eval = {}
    offset = 0
    for time_name in args.times:
        n = per_time[time_name]['n_active']
        Xt = X[offset:offset+n]
        yt = y[offset:offset+n]
        st = predict_logistic(model, Xt)
        per_time_eval[time_name] = {
            'n_active': int(n),
            'failure_fraction': float(np.mean(yt)) if n else 0.0,
            'mean_score': float(np.mean(st)) if n else 0.0,
            'score_quantiles': {
                'q50': float(np.quantile(st, 0.5)) if n else 0.0,
                'q90': float(np.quantile(st, 0.9)) if n else 0.0,
                'q99': float(np.quantile(st, 0.99)) if n else 0.0,
            },
            'threshold_metrics': [threshold_metrics(st, yt, thr) for thr in thresholds],
        }
        offset += n

    payload = {
        'case': str(case_dir.resolve()),
        'checkpoint': str(Path(args.checkpoint).resolve()),
        'mechanism': str(Path(args.mechanism).resolve()),
        'frozen_temperature': args.frozen_temperature,
        'feature_names': feature_names,
        'fit_times': args.times,
        'n_samples': int(len(y)),
        'failure_fraction': float(np.mean(y)),
        'rank_correlation_like': rank_correlation_like(scores, y),
        'model': {
            'weights': {name: float(w) for name, w in zip(feature_names + ['bias'], model['weights'])},
            'feature_mean': {name: float(v) for name, v in zip(feature_names, model['mean'])},
            'feature_std': {name: float(v) for name, v in zip(feature_names, model['std'])},
        },
        'global_threshold_metrics': metrics,
        'per_time': per_time_eval,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    print(json.dumps(payload, indent=2))


if __name__ == '__main__':
    main()
