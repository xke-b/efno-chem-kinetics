#!/usr/bin/env python3
"""Compare key-species coverage across C2H4 datasets using each dataset's metadata order."""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

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
    p.add_argument('--datasets', nargs='+', required=True)
    p.add_argument('--metadata-files', nargs='+', required=True)
    p.add_argument('--labels', nargs='+', required=True)
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



def dataset_summary(dataset_path: Path, meta_path: Path) -> dict:
    arr = np.load(dataset_path)
    meta = json.loads(meta_path.read_text())
    species_names = meta['species_names']
    n_species = len(species_names)
    next_block = arr[:, 2 + n_species:]
    next_species = next_block[:, 2:]
    out = {'rows': int(len(arr)), 'species': {}}
    for name in KEY_SPECIES:
        idx = species_names.index(name)
        vals = next_species[:, idx]
        thr = DEFAULT_THRESHOLDS[name]
        out['species'][name] = {
            'mean_next': float(vals.mean()),
            'frac_next_ge_threshold': float(np.mean(vals >= thr)),
            'p99_next': float(np.quantile(vals, 0.99)),
        }
    return out



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
    out = {'rows': int(len(arr)), 'species': {}}
    for name in KEY_SPECIES:
        idx = 2 + SPECIES_CASE_ORDER.index(name)
        vals = arr[:, idx]
        thr = DEFAULT_THRESHOLDS[name]
        out['species'][name] = {
            'mean': float(vals.mean()),
            'frac_ge_threshold': float(np.mean(vals >= thr)),
            'p99': float(np.quantile(vals, 0.99)),
        }
    return out



def plot(payload: dict, out_fig: Path) -> None:
    labels = list(payload['datasets'].keys()) + ['stock_5e-6']
    n = len(KEY_SPECIES)
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), constrained_layout=True)
    species_sets = [KEY_SPECIES[:2], KEY_SPECIES[2:4], KEY_SPECIES[4:6], KEY_SPECIES[6:]]
    for ax, group in zip(axes.flatten(), species_sets):
        x = np.arange(len(labels))
        width = 0.8 / len(group)
        for i, sp in enumerate(group):
            values = []
            for label in labels:
                if label == 'stock_5e-6':
                    values.append(payload['stock']['species'][sp]['frac_ge_threshold'])
                else:
                    values.append(payload['datasets'][label]['species'][sp]['frac_next_ge_threshold'])
            ax.bar(x + (i - (len(group)-1)/2)*width, values, width=width, label=sp)
        ax.set_xticks(x, labels, rotation=25, ha='right')
        ax.set_ylim(0, 1.0)
        ax.set_ylabel('fraction above threshold')
        ax.legend(frameon=False)
    fig.suptitle('C2H4 key-species coverage comparison')
    out_fig.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_fig, dpi=180, bbox_inches='tight')



def main() -> None:
    args = parse_args()
    if not (len(args.datasets) == len(args.metadata_files) == len(args.labels)):
        raise ValueError('datasets, metadata-files, and labels must match')
    payload = {'datasets': {}, 'stock': case_summary(Path(args.case), args.case_time, args.frozen_temperature)}
    for label, ds, meta in zip(args.labels, args.datasets, args.metadata_files):
        payload['datasets'][label] = dataset_summary(Path(ds), Path(meta))
    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    plot(payload, Path(args.out_fig))
    print(json.dumps({'out_json': str(out_json.resolve()), 'out_fig': str(Path(args.out_fig).resolve())}, indent=2))


if __name__ == '__main__':
    main()
