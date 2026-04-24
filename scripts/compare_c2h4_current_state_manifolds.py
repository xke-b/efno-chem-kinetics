#!/usr/bin/env python3
"""Compare current-state C2H4 manifolds against stock active states."""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

import h5py
import matplotlib.pyplot as plt
import numpy as np

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
SPECIES_CASE_ORDER = [
    'H', 'H2', 'O', 'O2', 'OH', 'H2O', 'HO2', 'CO', 'CO2', 'HCO', 'CH3', 'CH4',
    'CH2O', 'T-CH2', 'S-CH2', 'C2H4', 'C2H5', 'C2H2', 'C2H3', 'CH2CHO', 'HCCO', 'CH2CO', 'CH2OH', 'N2'
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument('--raw-oned-h5', required=True)
    p.add_argument('--canonical-current-dataset', required=True)
    p.add_argument('--canonical-current-metadata', required=True)
    p.add_argument('--augmented-current-dataset', required=True)
    p.add_argument('--augmented-current-metadata', required=True)
    p.add_argument('--case', required=True)
    p.add_argument('--case-time', required=True)
    p.add_argument('--out-json', required=True)
    p.add_argument('--out-fig', required=True)
    p.add_argument('--frozen-temperature', type=float, default=510.0)
    return p.parse_args()


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
                raise ValueError(f'Uniform field without fallback in {path}')
            value = float(stripped.split('uniform', 1)[1].replace(';', '').strip())
            return np.full(fallback_n_cells, value, dtype=np.float64)
    raise ValueError(f'Could not parse internalField from {path}')


def summarize_named_matrix(matrix: np.ndarray, names: list[str]) -> dict:
    out = {
        'rows': int(len(matrix)),
        'temperature': {
            'min': float(matrix[:, 0].min()),
            'p50': float(np.quantile(matrix[:, 0], 0.5)),
            'p99': float(np.quantile(matrix[:, 0], 0.99)),
            'max': float(matrix[:, 0].max()),
            'mean': float(matrix[:, 0].mean()),
        },
        'pressure': {
            'min': float(matrix[:, 1].min()),
            'p50': float(np.quantile(matrix[:, 1], 0.5)),
            'p99': float(np.quantile(matrix[:, 1], 0.99)),
            'max': float(matrix[:, 1].max()),
            'mean': float(matrix[:, 1].mean()),
        },
        'species': {},
    }
    for name in KEY_SPECIES:
        idx = names.index(name)
        vals = matrix[:, idx]
        thr = DEFAULT_THRESHOLDS[name]
        out['species'][name] = {
            'mean': float(vals.mean()),
            'frac_ge_threshold': float(np.mean(vals >= thr)),
            'p99': float(np.quantile(vals, 0.99)),
        }
    return out


def raw_oned_summary(h5_path: Path) -> dict:
    with h5py.File(h5_path, 'r') as h5:
        names = [str(x) for x in h5.attrs['species_names']]
        arrays = [h5['scalar_fields'][key][...] for key in sorted(h5['scalar_fields'].keys(), key=float)]
    return summarize_named_matrix(np.concatenate(arrays, axis=0), names)


def npy_current_summary(dataset_path: Path, metadata_path: Path) -> dict:
    arr = np.load(dataset_path)
    meta = json.loads(metadata_path.read_text())
    species_names = meta['species_names']
    return summarize_named_matrix(arr, ['T', 'P', *species_names])


def case_summary(case: Path, time_name: str, frozen_temperature: float) -> dict:
    chunks = []
    for proc_dir in sorted(p for p in case.glob('processor*') if p.is_dir()):
        time_dir = proc_dir / time_name
        t = read_internal_scalar_field(time_dir / 'T.gz')
        p = read_internal_scalar_field(time_dir / 'p.gz', fallback_n_cells=len(t))
        species = [read_internal_scalar_field(time_dir / f'{name}.gz', fallback_n_cells=len(t)) for name in SPECIES_CASE_ORDER]
        chunks.append(np.column_stack([t, p, *species]))
    arr = np.concatenate(chunks, axis=0)
    arr = arr[arr[:, 0] > frozen_temperature]
    return summarize_named_matrix(arr, ['T', 'P', *SPECIES_CASE_ORDER])


def plot(payload: dict, out_fig: Path) -> None:
    labels = ['raw_oneD', 'canonical_cantera', 'augmented_oneD', 'stock_active_5e6']
    species_groups = [KEY_SPECIES[:2], KEY_SPECIES[2:4], KEY_SPECIES[4:6], KEY_SPECIES[6:]]
    fig, axes = plt.subplots(2, 2, figsize=(12, 7), constrained_layout=True)
    for ax, group in zip(axes.flatten(), species_groups):
        x = np.arange(len(labels))
        width = 0.8 / len(group)
        for i, sp in enumerate(group):
            vals = [
                payload['raw_oned']['species'][sp]['frac_ge_threshold'],
                payload['canonical_cantera']['species'][sp]['frac_ge_threshold'],
                payload['augmented_oned']['species'][sp]['frac_ge_threshold'],
                payload['stock_active_5e6']['species'][sp]['frac_ge_threshold'],
            ]
            ax.bar(x + (i - (len(group)-1)/2) * width, vals, width=width, label=sp)
        ax.set_xticks(x, labels, rotation=20, ha='right')
        ax.set_ylim(0, 1.0)
        ax.set_ylabel('fraction above threshold')
        ax.legend(frameon=False)
    fig.suptitle('C2H4 current-state manifold comparison')
    out_fig.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_fig, dpi=180, bbox_inches='tight')


def main() -> None:
    args = parse_args()
    payload = {
        'raw_oned': raw_oned_summary(Path(args.raw_oned_h5)),
        'canonical_cantera': npy_current_summary(Path(args.canonical_current_dataset), Path(args.canonical_current_metadata)),
        'augmented_oned': npy_current_summary(Path(args.augmented_current_dataset), Path(args.augmented_current_metadata)),
        'stock_active_5e6': case_summary(Path(args.case), args.case_time, args.frozen_temperature),
        'note': 'All but stock_active_5e6 are current-state manifolds; stock_active_5e6 uses active CFD cells from the stock case.',
    }
    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    plot(payload, Path(args.out_fig))
    print(json.dumps({'out_json': str(out_json.resolve()), 'out_fig': str(Path(args.out_fig).resolve())}, indent=2))


if __name__ == '__main__':
    main()
