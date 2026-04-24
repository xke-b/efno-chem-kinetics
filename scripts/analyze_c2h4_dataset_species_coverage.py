#!/usr/bin/env python3
"""Compare key-species coverage across C2H4 paired-state datasets and case states."""

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


KEY_SPECIES = ['C2H5', 'C2H3', 'CH2CHO', 'CH2CO', 'OH', 'CO', 'CO2']
DEFAULT_THRESHOLDS = {
    'C2H5': 1e-8,
    'C2H3': 1e-8,
    'CH2CHO': 1e-8,
    'CH2CO': 1e-8,
    'OH': 1e-5,
    'CO': 1e-4,
    'CO2': 1e-4,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--datasets', nargs='*', default=[])
    parser.add_argument('--dataset-labels', nargs='*', default=[])
    parser.add_argument('--cases', nargs='*', default=[])
    parser.add_argument('--case-labels', nargs='*', default=[])
    parser.add_argument('--case-times', nargs='*', default=[])
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



def dataset_summary(path: Path) -> dict:
    arr = np.load(path)
    n_species = len(SPECIES)
    current = arr[:, : 2 + n_species]
    nxt = arr[:, 2 + n_species :]
    summary = {
        'rows': int(len(arr)),
        'temperature': {
            'current_mean': float(current[:, 0].mean()),
            'next_mean': float(nxt[:, 0].mean()),
        },
        'pressure': {
            'current_mean': float(current[:, 1].mean()),
            'next_mean': float(nxt[:, 1].mean()),
        },
        'species': {},
    }
    next_species = nxt[:, 2:]
    for name in KEY_SPECIES:
        idx = SPECIES.index(name)
        values = next_species[:, idx]
        thr = DEFAULT_THRESHOLDS[name]
        summary['species'][name] = {
            'threshold': thr,
            'mean_next': float(values.mean()),
            'frac_next_ge_threshold': float(np.mean(values >= thr)),
            'p99_next': float(np.quantile(values, 0.99)),
        }
    return summary



def case_summary(case_dir: Path, time_name: str, frozen_temperature: float) -> dict:
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
    arr = np.concatenate(chunks, axis=0)
    arr = arr[arr[:, 0] > frozen_temperature]
    summary = {
        'rows': int(len(arr)),
        'temperature': {'mean': float(arr[:, 0].mean())},
        'pressure': {'mean': float(arr[:, 1].mean())},
        'species': {},
    }
    for name in KEY_SPECIES:
        idx = 2 + SPECIES.index(name)
        values = arr[:, idx]
        thr = DEFAULT_THRESHOLDS[name]
        summary['species'][name] = {
            'threshold': thr,
            'mean': float(values.mean()),
            'frac_ge_threshold': float(np.mean(values >= thr)),
            'p99': float(np.quantile(values, 0.99)),
        }
    return summary



def main() -> None:
    args = parse_args()
    if len(args.datasets) != len(args.dataset_labels):
        raise ValueError('datasets and dataset-labels must have the same length')
    if not (len(args.cases) == len(args.case_labels) == len(args.case_times)):
        raise ValueError('cases, case-labels, and case-times must have the same length')

    result = {
        'frozen_temperature': args.frozen_temperature,
        'dataset_summaries': {},
        'case_summaries': {},
        'note': 'Coverage summary for key late-chemistry species across C2H4 datasets and/or case states.',
    }
    for label, path in zip(args.dataset_labels, args.datasets):
        result['dataset_summaries'][label] = dataset_summary(Path(path))
    for label, case, time_name in zip(args.case_labels, args.cases, args.case_times):
        result['case_summaries'][label] = {
            'case': str(Path(case).resolve()),
            'time': time_name,
            'summary': case_summary(Path(case), time_name, args.frozen_temperature),
        }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
