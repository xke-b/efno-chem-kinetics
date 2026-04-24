#!/usr/bin/env python3
"""Summarize DeepFlame H2 case states across a transition window.

Focuses on the DNN-active subset (T > frozen_temperature) and reports
state-distribution changes across specified written times.
"""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

import numpy as np

SPECIES = ['H', 'H2', 'O', 'OH', 'H2O', 'O2', 'HO2', 'H2O2', 'N2']


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


def summarize_subset(fields: dict[str, np.ndarray], mask: np.ndarray) -> dict:
    subset = {k: v[mask] for k, v in fields.items()}
    n = int(np.sum(mask))
    result = {'n_cells': n}
    if n == 0:
        return result

    T = subset['T']
    p = subset['p']
    Y = np.column_stack([subset[s] for s in SPECIES])
    result.update(
        {
            'temperature': {
                'min': float(np.min(T)),
                'max': float(np.max(T)),
                'mean': float(np.mean(T)),
                'fraction_lt_600': float(np.mean(T < 600.0)),
                'fraction_lt_700': float(np.mean(T < 700.0)),
                'fraction_gt_1200': float(np.mean(T > 1200.0)),
            },
            'pressure': {
                'min': float(np.min(p)),
                'max': float(np.max(p)),
                'mean': float(np.mean(p)),
            },
            'species_sum': {
                'mean_abs_deviation_from_1': float(np.mean(np.abs(np.sum(Y, axis=1) - 1.0))),
            },
            'species_means': {s: float(np.mean(subset[s])) for s in SPECIES},
            'species_p95': {s: float(np.quantile(subset[s], 0.95)) for s in SPECIES},
            'species_p99': {s: float(np.quantile(subset[s], 0.99)) for s in SPECIES},
        }
    )
    return result


def main() -> None:
    args = parse_args()
    case_dir = Path(args.case)
    payload = {
        'case': str(case_dir.resolve()),
        'frozen_temperature': args.frozen_temperature,
        'times': {},
    }

    for time_name in args.times:
        fields = read_case_time_fields(case_dir, time_name)
        active_mask = fields['T'] > args.frozen_temperature
        payload['times'][time_name] = {
            'all_cells': summarize_subset(fields, np.ones_like(fields['T'], dtype=bool)),
            'active_cells': summarize_subset(fields, active_mask),
        }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    print(json.dumps(payload, indent=2))


if __name__ == '__main__':
    main()
