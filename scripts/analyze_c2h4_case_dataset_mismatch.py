#!/usr/bin/env python3
"""Compare stock DeepFlame C2H4 case states against an offline training dataset.

The main question is whether the offline dataset covers the thermochemical region
actually seen by the C2H4 CFD case, especially in the DNN-active temperature
regime implied by `frozenTemperature`.
"""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

import numpy as np

SPECIES = [
    'H', 'H2', 'O', 'O2', 'OH', 'H2O', 'HO2', 'CO', 'CO2', 'HCO', 'CH3', 'CH4',
    'CH2O', 'T-CH2', 'S-CH2', 'C2H4', 'C2H5', 'C2H2', 'C2H3', 'CH2CHO',
    'HCCO', 'CH2CO', 'CH2OH', 'N2'
]



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--case', required=True)
    parser.add_argument('--times', nargs='+', required=True)
    parser.add_argument('--dataset', required=True)
    parser.add_argument('--metadata', required=True)
    parser.add_argument('--frozen-temperature', type=float, default=510.0)
    parser.add_argument('--max-samples-per-time', type=int, default=50000)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--out', required=True)
    return parser.parse_args()



def read_internal_scalar_field(path: Path, fallback_n_cells: int | None = None) -> np.ndarray:
    with gzip.open(path, 'rt', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('internalField') and 'List<scalar>' in stripped:
            count = int(lines[i + 1].strip())
            start = i + 3
            return np.array([float(lines[start + j].strip()) for j in range(count)], dtype=np.float64)
        if stripped.startswith('internalField') and 'uniform' in stripped:
            if fallback_n_cells is None:
                raise ValueError(f'Uniform field without fallback cell count in {path}')
            value = float(stripped.split('uniform', 1)[1].replace(';', '').strip())
            return np.full(fallback_n_cells, value, dtype=np.float64)

    raise ValueError(f'Could not parse internalField from {path}')



def read_case_time_states(case_dir: Path, time_name: str) -> np.ndarray:
    processor_dirs = sorted(p for p in case_dir.glob('processor*') if p.is_dir())
    chunks = []
    for proc_dir in processor_dirs:
        time_dir = proc_dir / time_name
        t_values = read_internal_scalar_field(time_dir / 'T.gz')
        p_values = read_internal_scalar_field(time_dir / 'p.gz', fallback_n_cells=len(t_values))
        species_values = [
            read_internal_scalar_field(time_dir / f'{name}.gz', fallback_n_cells=len(t_values))
            for name in SPECIES
        ]
        chunk = np.column_stack([t_values, p_values, *species_values])
        chunks.append(chunk)
    return np.concatenate(chunks, axis=0)



def summarize_matrix(matrix: np.ndarray, names: list[str]) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for idx, name in enumerate(names):
        values = matrix[:, idx]
        out[name] = {
            'min': float(np.min(values)),
            'p01': float(np.quantile(values, 0.01)),
            'p50': float(np.quantile(values, 0.50)),
            'p99': float(np.quantile(values, 0.99)),
            'max': float(np.max(values)),
            'mean': float(np.mean(values)),
        }
    return out



def main() -> None:
    args = parse_args()
    rng = np.random.default_rng(args.seed)

    dataset = np.load(args.dataset)
    metadata = json.loads(Path(args.metadata).read_text())
    dataset_state_width = len(metadata['species_names']) + 2
    dataset_current = dataset[:, :dataset_state_width]

    case_dir = Path(args.case)
    sampled_case_states = []
    per_time = {}
    for time_name in args.times:
        states = read_case_time_states(case_dir, time_name)
        active_mask = states[:, 0] > args.frozen_temperature
        active_states = states[active_mask]
        if len(active_states) == 0:
            raise ValueError(f'No active states found for time {time_name}')
        sample_n = min(args.max_samples_per_time, len(active_states))
        sample_idx = rng.choice(len(active_states), size=sample_n, replace=False)
        sampled = active_states[sample_idx]
        sampled_case_states.append(sampled)
        per_time[time_name] = {
            'n_cells_total': int(len(states)),
            'n_cells_active_by_T_threshold': int(np.sum(active_mask)),
            'active_fraction': float(np.mean(active_mask)),
            'sampled_active_cells': int(sample_n),
            'temperature': {
                'min': float(np.min(active_states[:, 0])),
                'p50': float(np.quantile(active_states[:, 0], 0.5)),
                'p99': float(np.quantile(active_states[:, 0], 0.99)),
                'max': float(np.max(active_states[:, 0])),
            },
            'pressure': {
                'min': float(np.min(active_states[:, 1])),
                'p50': float(np.quantile(active_states[:, 1], 0.5)),
                'p99': float(np.quantile(active_states[:, 1], 0.99)),
                'max': float(np.max(active_states[:, 1])),
            },
        }

    case_states = np.concatenate(sampled_case_states, axis=0)

    names = ['T', 'P', *SPECIES]
    dataset_summary = summarize_matrix(dataset_current, names)
    case_summary = summarize_matrix(case_states, names)

    dataset_t_min = float(np.min(dataset_current[:, 0]))
    dataset_t_max = float(np.max(dataset_current[:, 0]))
    dataset_p_min = float(np.min(dataset_current[:, 1]))
    dataset_p_max = float(np.max(dataset_current[:, 1]))

    summary = {
        'case': str(case_dir.resolve()),
        'times': args.times,
        'dataset': str(Path(args.dataset).resolve()),
        'metadata': str(Path(args.metadata).resolve()),
        'frozen_temperature': args.frozen_temperature,
        'max_samples_per_time': args.max_samples_per_time,
        'per_time': per_time,
        'dataset_summary': dataset_summary,
        'active_case_summary': case_summary,
        'coverage': {
            'temperature': {
                'dataset_min': dataset_t_min,
                'dataset_max': dataset_t_max,
                'case_fraction_below_dataset_min': float(np.mean(case_states[:, 0] < dataset_t_min)),
                'case_fraction_above_dataset_max': float(np.mean(case_states[:, 0] > dataset_t_max)),
            },
            'pressure': {
                'dataset_min': dataset_p_min,
                'dataset_max': dataset_p_max,
                'case_fraction_below_dataset_min': float(np.mean(case_states[:, 1] < dataset_p_min)),
                'case_fraction_above_dataset_max': float(np.mean(case_states[:, 1] > dataset_p_max)),
            },
        },
        'selected_species_means': {
            name: {
                'dataset': float(np.mean(dataset_current[:, names.index(name)])),
                'active_case': float(np.mean(case_states[:, names.index(name)])),
            }
            for name in ['O2', 'OH', 'H2O', 'CO', 'CO2', 'C2H4', 'C2H5', 'C2H3', 'N2']
        },
        'note': 'Active case states are approximated by T > frozenTemperature because selectDNN is not reliable in written fields for this setup.',
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
