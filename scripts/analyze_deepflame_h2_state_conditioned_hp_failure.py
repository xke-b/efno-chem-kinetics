#!/usr/bin/env python3
"""Analyze state-conditioned HP failure structure for DeepFlame H2 hybrid cases."""

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
    n_species = exported['export_metadata']['n_species']
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


def summarize_bins(values: np.ndarray, failure_mask: np.ndarray, edges: list[float]) -> list[dict]:
    bins = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        if np.isinf(hi):
            mask = values >= lo
            label = f'[{lo}, inf)'
        else:
            mask = (values >= lo) & (values < hi)
            label = f'[{lo}, {hi})'
        count = int(np.sum(mask))
        failures = int(np.sum(failure_mask[mask])) if count else 0
        bins.append({
            'label': label,
            'count': count,
            'failures': failures,
            'failure_fraction': failures / count if count else None,
        })
    return bins


def main() -> None:
    args = parse_args()
    case_dir = Path(args.case)
    exported = torch.load(args.checkpoint, map_location='cpu')
    n_species = int(exported['export_metadata']['n_species'])
    models = build_models(exported, n_species)
    gas = ct.Solution(args.mechanism)

    t_edges = [650.0, 800.0, 1000.0, 1200.0, 1600.0, 2000.0, np.inf]
    o2_edges = [0.0, 0.02, 0.05, 0.10, 0.15, 0.20, np.inf]
    h2o_edges = [0.0, 0.02, 0.05, 0.10, 0.15, 0.20, np.inf]

    payload = {
        'case': str(case_dir.resolve()),
        'checkpoint': str(Path(args.checkpoint).resolve()),
        'mechanism': str(Path(args.mechanism).resolve()),
        'frozen_temperature': args.frozen_temperature,
        'times': {},
    }

    for time_name in args.times:
        fields = read_case_time_fields(case_dir, time_name)
        species = np.column_stack([fields[name] for name in SPECIES])
        states = np.column_stack([fields['T'], fields['p'], species])
        active_mask = fields['T'] > args.frozen_temperature
        active_states = states[active_mask]

        next_species = predict_next_species_batch(exported, models, active_states)
        failures = np.zeros(len(active_states), dtype=bool)
        next_t_success = []
        delta_t_success = []

        for i, (state, y_next) in enumerate(zip(active_states, next_species)):
            try:
                gas.TPY = float(state[0]), float(state[1]), state[2:]
                h = gas.enthalpy_mass
                gas.Y = y_next
                gas.HP = h, float(state[1])
                next_t = float(gas.T)
                next_t_success.append(next_t)
                delta_t_success.append(next_t - float(state[0]))
            except Exception:
                failures[i] = True

        active_t = active_states[:, 0]
        active_o2 = active_states[:, 2 + SPECIES.index('O2')]
        active_h2o = active_states[:, 2 + SPECIES.index('H2O')]

        payload['times'][time_name] = {
            'n_active_cells': int(len(active_states)),
            'hp_failure_fraction_active': float(np.mean(failures)) if len(failures) else 0.0,
            'temperature_bins': summarize_bins(active_t, failures, t_edges),
            'o2_bins': summarize_bins(active_o2, failures, o2_edges),
            'h2o_bins': summarize_bins(active_h2o, failures, h2o_edges),
            'active_state_means': {
                'T': float(np.mean(active_t)) if len(active_t) else None,
                'O2': float(np.mean(active_o2)) if len(active_o2) else None,
                'H2O': float(np.mean(active_h2o)) if len(active_h2o) else None,
            },
            'success_temperature': {
                'mean': float(np.mean(next_t_success)) if next_t_success else None,
                'fraction_lt_300': float(np.mean(np.asarray(next_t_success) < 300.0)) if next_t_success else None,
            },
            'success_delta_t': {
                'mean': float(np.mean(delta_t_success)) if delta_t_success else None,
                'fraction_abs_gt_500': float(np.mean(np.abs(np.asarray(delta_t_success)) > 500.0)) if delta_t_success else None,
            },
        }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    print(json.dumps(payload, indent=2))


if __name__ == '__main__':
    main()
