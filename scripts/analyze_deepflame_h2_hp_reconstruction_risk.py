#!/usr/bin/env python3
"""Analyze HP reconstruction risk on written DeepFlame H2 smoke states.

For a given written case state and exported DeepFlame-compatible checkpoint:
1. read T, p, species fields across processors
2. identify cells that would enter the DNN path (T > frozenTemperature)
3. apply the exported DeepFlame species update contract
4. attempt Cantera HP reconstruction for each active cell
5. summarize failure rates and the most pathological cells
"""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

import numpy as np
import torch

SPECIES = ['H', 'H2', 'O', 'OH', 'H2O', 'O2', 'HO2', 'H2O2', 'N2']
BCT_LAMBDA = 0.1
BCT_INVERSE_FLOOR = -1.0 / BCT_LAMBDA + 1e-8



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--case', required=True)
    parser.add_argument('--time', default='2e-06')
    parser.add_argument('--checkpoint', required=True, help='Exported DeepFlame-compatible checkpoint')
    parser.add_argument('--mechanism', required=True)
    parser.add_argument('--frozen-temperature', type=float, default=510.0)
    parser.add_argument('--out', required=True)
    return parser.parse_args()



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



def main() -> None:
    args = parse_args()
    case_dir = Path(args.case)
    fields = read_case_time_fields(case_dir, args.time)
    species = np.column_stack([fields[name] for name in SPECIES])
    states = np.column_stack([fields['T'], fields['p'], species])

    active_mask = fields['T'] > args.frozen_temperature
    active_indices = np.flatnonzero(active_mask)
    active_states = states[active_mask]

    exported = torch.load(args.checkpoint, map_location='cpu')
    n_species = int(exported['export_metadata']['n_species'])
    models = build_models(exported, n_species)
    next_species = predict_next_species_batch(exported, models, active_states)

    import cantera as ct

    setter = ct.Solution(args.mechanism)
    getter = ct.Solution(args.mechanism)
    failures = []
    success_temperatures = []
    success_delta_t = []
    extreme_successes = []

    for local_idx, (global_idx, state, y_next) in enumerate(zip(active_indices, active_states, next_species)):
        try:
            setter.TPY = float(state[0]), float(state[1]), state[2:]
            h = setter.enthalpy_mass
            getter.Y = y_next
            getter.HP = h, float(state[1])
            next_t = getter.T
            success_temperatures.append(next_t)
            success_delta_t.append(next_t - float(state[0]))
            if next_t < 300.0 or next_t > 4000.0 or abs(next_t - float(state[0])) > 500.0:
                extreme_successes.append({
                    'global_index': int(global_idx),
                    'current_T': float(state[0]),
                    'current_p': float(state[1]),
                    'predicted_T': float(next_t),
                    'delta_T': float(next_t - float(state[0])),
                    'species_sum': float(np.sum(y_next)),
                    'top_species': sorted(
                        ({'name': SPECIES[i], 'value': float(y_next[i])} for i in range(n_species)),
                        key=lambda x: -x['value'],
                    )[:6],
                })
        except Exception as exc:  # CanteraError
            failures.append({
                'global_index': int(global_idx),
                'current_T': float(state[0]),
                'current_p': float(state[1]),
                'species_sum': float(np.sum(y_next)),
                'exception': str(exc),
                'top_species': sorted(
                    ({'name': SPECIES[i], 'value': float(y_next[i])} for i in range(n_species)),
                    key=lambda x: -x['value'],
                )[:6],
            })

    success_temperatures = np.asarray(success_temperatures, dtype=np.float64)
    success_delta_t = np.asarray(success_delta_t, dtype=np.float64)
    success_temperatures = np.asarray(success_temperatures, dtype=np.float64)
    success_delta_t = np.asarray(success_delta_t, dtype=np.float64)
    payload = {
        'case': str(case_dir.resolve()),
        'time': args.time,
        'checkpoint': str(Path(args.checkpoint).resolve()),
        'mechanism': args.mechanism,
        'frozen_temperature': args.frozen_temperature,
        'n_cells_total': int(len(states)),
        'n_cells_dnn_active': int(len(active_states)),
        'active_fraction': float(len(active_states) / len(states)),
        'hp_reconstruction': {
            'n_failures': int(len(failures)),
            'failure_fraction_of_active': float(len(failures) / len(active_states)) if len(active_states) else 0.0,
            'n_successes': int(len(success_temperatures)),
            'success_temperature': {
                'min': float(np.min(success_temperatures)) if len(success_temperatures) else None,
                'max': float(np.max(success_temperatures)) if len(success_temperatures) else None,
                'mean': float(np.mean(success_temperatures)) if len(success_temperatures) else None,
                'fraction_lt_300': float(np.mean(success_temperatures < 300.0)) if len(success_temperatures) else 0.0,
                'fraction_lt_150': float(np.mean(success_temperatures < 150.0)) if len(success_temperatures) else 0.0,
                'fraction_gt_4000': float(np.mean(success_temperatures > 4000.0)) if len(success_temperatures) else 0.0,
            },
            'success_delta_T': {
                'min': float(np.min(success_delta_t)) if len(success_delta_t) else None,
                'max': float(np.max(success_delta_t)) if len(success_delta_t) else None,
                'mean': float(np.mean(success_delta_t)) if len(success_delta_t) else None,
                'fraction_abs_gt_500': float(np.mean(np.abs(success_delta_t) > 500.0)) if len(success_delta_t) else 0.0,
                'fraction_abs_gt_1000': float(np.mean(np.abs(success_delta_t) > 1000.0)) if len(success_delta_t) else 0.0,
            },
            'sample_failures': failures[:20],
            'sample_extreme_successes': extreme_successes[:20],
        },
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    print(json.dumps(payload, indent=2))


if __name__ == '__main__':
    main()
