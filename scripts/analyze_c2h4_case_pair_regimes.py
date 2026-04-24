#!/usr/bin/env python3
"""Analyze regime structure of extracted C2H4 CFD state pairs.

This is a target-quality diagnostic for deciding whether a more chemistry-like
subset can be carved out of full CFD state pairs using simple transition-space
filters such as small pressure drift.
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
    parser.add_argument('--frozen-temperature', type=float, default=510.0)
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
        chunks.append(np.column_stack([t_values, p_values, *species_values]))
    return np.concatenate(chunks, axis=0)



def quantiles(x: np.ndarray) -> dict[str, float]:
    return {
        'min': float(np.min(x)),
        'p01': float(np.quantile(x, 0.01)),
        'p50': float(np.quantile(x, 0.50)),
        'p95': float(np.quantile(x, 0.95)),
        'p99': float(np.quantile(x, 0.99)),
        'max': float(np.max(x)),
        'mean': float(np.mean(x)),
    }



def main() -> None:
    args = parse_args()
    case_dir = Path(args.case)
    times = args.times

    state_blocks = {time_name: read_case_time_states(case_dir, time_name) for time_name in times}
    pair_summaries: dict[str, dict] = {}
    all_abs_dp = []
    all_rel_dp = []
    all_abs_dt = []
    all_species_l1 = []

    for current_time, next_time in zip(times[:-1], times[1:]):
        current = state_blocks[current_time]
        nxt = state_blocks[next_time]
        active = current[:, 0] > args.frozen_temperature
        cur = current[active]
        nxt = nxt[active]
        dt = nxt[:, 0] - cur[:, 0]
        dp = nxt[:, 1] - cur[:, 1]
        abs_dp = np.abs(dp)
        rel_dp = abs_dp / np.maximum(np.abs(cur[:, 1]), 1.0)
        species_l1 = np.sum(np.abs(nxt[:, 2:] - cur[:, 2:]), axis=1)

        pair_summaries[f'{current_time}->{next_time}'] = {
            'n_active': int(len(cur)),
            'delta_T': quantiles(dt),
            'abs_delta_P': quantiles(abs_dp),
            'rel_abs_delta_P': quantiles(rel_dp),
            'species_l1': quantiles(species_l1),
            'pressure_filter_fractions': {
                'abs_dp_le_25Pa': float(np.mean(abs_dp <= 25.0)),
                'abs_dp_le_50Pa': float(np.mean(abs_dp <= 50.0)),
                'abs_dp_le_100Pa': float(np.mean(abs_dp <= 100.0)),
                'abs_dp_le_250Pa': float(np.mean(abs_dp <= 250.0)),
                'abs_dp_le_500Pa': float(np.mean(abs_dp <= 500.0)),
                'rel_dp_le_1e-4': float(np.mean(rel_dp <= 1e-4)),
                'rel_dp_le_5e-4': float(np.mean(rel_dp <= 5e-4)),
                'rel_dp_le_1e-3': float(np.mean(rel_dp <= 1e-3)),
            },
        }
        all_abs_dp.append(abs_dp)
        all_rel_dp.append(rel_dp)
        all_abs_dt.append(np.abs(dt))
        all_species_l1.append(species_l1)

    all_abs_dp = np.concatenate(all_abs_dp)
    all_rel_dp = np.concatenate(all_rel_dp)
    all_abs_dt = np.concatenate(all_abs_dt)
    all_species_l1 = np.concatenate(all_species_l1)

    summary = {
        'case': str(case_dir.resolve()),
        'times': times,
        'frozen_temperature': args.frozen_temperature,
        'pair_summaries': pair_summaries,
        'aggregate': {
            'abs_delta_P': quantiles(all_abs_dp),
            'rel_abs_delta_P': quantiles(all_rel_dp),
            'abs_delta_T': quantiles(all_abs_dt),
            'species_l1': quantiles(all_species_l1),
            'pressure_filter_fractions': {
                'abs_dp_le_25Pa': float(np.mean(all_abs_dp <= 25.0)),
                'abs_dp_le_50Pa': float(np.mean(all_abs_dp <= 50.0)),
                'abs_dp_le_100Pa': float(np.mean(all_abs_dp <= 100.0)),
                'abs_dp_le_250Pa': float(np.mean(all_abs_dp <= 250.0)),
                'abs_dp_le_500Pa': float(np.mean(all_abs_dp <= 500.0)),
                'rel_dp_le_1e-4': float(np.mean(all_rel_dp <= 1e-4)),
                'rel_dp_le_5e-4': float(np.mean(all_rel_dp <= 5e-4)),
                'rel_dp_le_1e-3': float(np.mean(all_rel_dp <= 1e-3)),
            },
        },
        'note': 'These active-pair statistics help size a pressure-drift filter for a more chemistry-like subset of the full CFD pair labels.',
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
