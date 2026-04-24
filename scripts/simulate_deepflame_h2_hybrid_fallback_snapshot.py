#!/usr/bin/env python3
"""Simulate a one-step hybrid fallback policy on a written DeepFlame H2 snapshot.

Policy:
- use exported DeepFlame-style species update for DNN-active cells
- attempt HP reconstruction
- if HP fails, or if a temperature guard is violated, fallback to a one-step
  Cantera reactor advance from the current state

This is an offline snapshot study, not a solver-integrated patch.
"""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

import numpy as np
import torch
import cantera as ct

SPECIES = ['H', 'H2', 'O', 'OH', 'H2O', 'O2', 'HO2', 'H2O2', 'N2']
BCT_LAMBDA = 0.1
BCT_INVERSE_FLOOR = -1.0 / BCT_LAMBDA + 1e-8


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument('--case', required=True)
    p.add_argument('--time', default='2e-06')
    p.add_argument('--checkpoint', required=True)
    p.add_argument('--mechanism', required=True)
    p.add_argument('--dt', type=float, default=1e-6)
    p.add_argument('--frozen-temperature', type=float, default=510.0)
    p.add_argument('--deltaT-guard', type=float, default=500.0)
    p.add_argument('--min-temperature-guard', type=float, default=300.0)
    p.add_argument('--out', required=True)
    return p.parse_args()


def read_internal_scalar_field(path: Path, fallback_n_cells: int | None = None) -> np.ndarray:
    with gzip.open(path, 'rt', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    n_cells = None
    for line in lines:
        s = line.strip()
        if s.isdigit():
            n_cells = int(s)
            break
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith('internalField') and 'List<scalar>' in s:
            count = int(lines[i + 1].strip())
            start = i + 3
            return np.array([float(lines[start + j].strip()) for j in range(count)], dtype=np.float64)
        if s.startswith('internalField') and 'uniform' in s:
            if n_cells is None:
                n_cells = fallback_n_cells
            if n_cells is None:
                raise ValueError(f'Uniform field without cell count: {path}')
            value = float(s.split('uniform', 1)[1].replace(';', '').strip())
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
    return {k: np.concatenate(v) for k, v in fields.items()}


def BCT(x: np.ndarray, lam: float = BCT_LAMBDA) -> np.ndarray:
    x = np.clip(x, 1e-16, None)
    return (np.power(x, lam) - 1.0) / lam


def inverse_BCT(x: np.ndarray, lam: float = BCT_LAMBDA) -> np.ndarray:
    return np.power(np.maximum(lam * x + 1.0, 1e-16), 1.0 / lam)


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


def hp_reconstruct(states: np.ndarray, next_species: np.ndarray, mechanism: str):
    setter = ct.Solution(mechanism)
    getter = ct.Solution(mechanism)
    ok = np.zeros(len(states), dtype=bool)
    next_T = np.full(len(states), np.nan, dtype=np.float64)
    messages = [''] * len(states)
    for i, (state, y_next) in enumerate(zip(states, next_species)):
        try:
            setter.TPY = float(state[0]), float(state[1]), state[2:]
            h = setter.enthalpy_mass
            getter.Y = y_next
            getter.HP = h, float(state[1])
            next_T[i] = getter.T
            ok[i] = True
        except Exception as exc:
            messages[i] = str(exc)
    return ok, next_T, messages


def cvode_fallback_step(states: np.ndarray, mechanism: str, dt: float) -> tuple[np.ndarray, np.ndarray]:
    gas = ct.Solution(mechanism)
    next_species = np.zeros((len(states), gas.n_species), dtype=np.float64)
    next_T = np.zeros(len(states), dtype=np.float64)
    for i, state in enumerate(states):
        gas.TPY = float(state[0]), float(state[1]), state[2:]
        reactor = ct.IdealGasConstPressureReactor(gas, energy='on')
        net = ct.ReactorNet([reactor])
        net.rtol = 1e-9
        net.atol = 1e-15
        net.advance(dt)
        next_species[i] = gas.Y
        next_T[i] = gas.T
    return next_species, next_T



def main() -> None:
    args = parse_args()
    case_dir = Path(args.case)
    fields = read_case_time_fields(case_dir, args.time)
    species = np.column_stack([fields[s] for s in SPECIES])
    states = np.column_stack([fields['T'], fields['p'], species])

    active_mask = fields['T'] > args.frozen_temperature
    active_indices = np.flatnonzero(active_mask)
    active_states = states[active_mask]

    exported = torch.load(args.checkpoint, map_location='cpu')
    models = build_models(exported, int(exported['export_metadata']['n_species']))
    dnn_next_species = predict_next_species_batch(exported, models, active_states)
    hp_ok, hp_next_T, hp_messages = hp_reconstruct(active_states, dnn_next_species, args.mechanism)
    dT = hp_next_T - active_states[:, 0]

    guard_mask = (~hp_ok) | (np.abs(dT) > args.deltaT_guard) | (hp_next_T < args.min_temperature_guard)
    fallback_states = active_states[guard_mask]
    fallback_next_species, fallback_next_T = cvode_fallback_step(fallback_states, args.mechanism, args.dt)

    hybrid_next_species = dnn_next_species.copy()
    hybrid_next_T = hp_next_T.copy()
    hybrid_next_species[guard_mask] = fallback_next_species
    hybrid_next_T[guard_mask] = fallback_next_T

    hybrid_ok, hybrid_recheck_T, hybrid_messages = hp_reconstruct(active_states, hybrid_next_species, args.mechanism)

    payload = {
        'case': str(case_dir.resolve()),
        'time': args.time,
        'checkpoint': str(Path(args.checkpoint).resolve()),
        'mechanism': args.mechanism,
        'dt': args.dt,
        'frozen_temperature': args.frozen_temperature,
        'deltaT_guard': args.deltaT_guard,
        'min_temperature_guard': args.min_temperature_guard,
        'n_cells_total': int(len(states)),
        'n_cells_dnn_active': int(len(active_states)),
        'baseline': {
            'hp_failures': int(np.sum(~hp_ok)),
            'hp_failure_fraction_of_active': float(np.mean(~hp_ok)) if len(active_states) else 0.0,
            'fraction_success_with_abs_dT_gt_guard': float(np.mean(np.abs(dT[hp_ok]) > args.deltaT_guard)) if np.any(hp_ok) else 0.0,
            'fraction_success_with_T_lt_guard': float(np.mean(hp_next_T[hp_ok] < args.min_temperature_guard)) if np.any(hp_ok) else 0.0,
        },
        'hybrid_policy': {
            'n_fallback_cells': int(np.sum(guard_mask)),
            'fallback_fraction_of_active': float(np.mean(guard_mask)) if len(active_states) else 0.0,
            'fallback_breakdown': {
                'hp_failures': int(np.sum(~hp_ok)),
                'abs_dT_gt_guard': int(np.sum(hp_ok & (np.abs(dT) > args.deltaT_guard))),
                'T_lt_guard': int(np.sum(hp_ok & (hp_next_T < args.min_temperature_guard))),
            },
            'rechecked_hp_failures_after_hybrid': int(np.sum(~hybrid_ok)),
            'rechecked_hp_failure_fraction_after_hybrid': float(np.mean(~hybrid_ok)) if len(active_states) else 0.0,
            'hybrid_next_T': {
                'min': float(np.min(hybrid_next_T)) if len(hybrid_next_T) else None,
                'max': float(np.max(hybrid_next_T)) if len(hybrid_next_T) else None,
                'mean': float(np.mean(hybrid_next_T)) if len(hybrid_next_T) else None,
            },
            'hybrid_delta_T': {
                'min': float(np.min(hybrid_next_T - active_states[:, 0])) if len(active_states) else None,
                'max': float(np.max(hybrid_next_T - active_states[:, 0])) if len(active_states) else None,
                'mean': float(np.mean(hybrid_next_T - active_states[:, 0])) if len(active_states) else None,
            },
        },
        'sample_remaining_failures': [
            {
                'global_index': int(active_indices[i]),
                'current_T': float(active_states[i, 0]),
                'current_p': float(active_states[i, 1]),
                'message': hybrid_messages[i],
            }
            for i in np.flatnonzero(~hybrid_ok)[:20]
        ],
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    print(json.dumps(payload, indent=2))


if __name__ == '__main__':
    main()
