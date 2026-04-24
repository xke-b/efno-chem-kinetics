#!/usr/bin/env python3
"""Extract current thermochemical states from a DeepFlame C2H4 case/time.

Useful for building targeted chemistry-label datasets from real CFD states,
especially narrow regime slices such as the cool-onset active band.
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
    p = argparse.ArgumentParser()
    p.add_argument('--case-dir', required=True)
    p.add_argument('--time', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--metadata-out', default=None)
    p.add_argument('--min-temperature', type=float, default=None)
    p.add_argument('--max-temperature', type=float, default=None)
    p.add_argument('--max-samples', type=int, default=None)
    p.add_argument('--seed', type=int, default=0)
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



def read_case_time_states(case_dir: Path, time_name: str) -> np.ndarray:
    chunks = []
    for proc_dir in sorted(p for p in case_dir.glob('processor*') if p.is_dir()):
        time_dir = proc_dir / time_name
        t = read_internal_scalar_field(time_dir / 'T.gz')
        p = read_internal_scalar_field(time_dir / 'p.gz', fallback_n_cells=len(t))
        species = [read_internal_scalar_field(time_dir / f'{name}.gz', fallback_n_cells=len(t)) for name in SPECIES]
        chunks.append(np.column_stack([t, p, *species]))
    return np.concatenate(chunks, axis=0)



def main() -> None:
    args = parse_args()
    rng = np.random.default_rng(args.seed)
    states = read_case_time_states(Path(args.case_dir), args.time)
    mask = np.ones(len(states), dtype=bool)
    if args.min_temperature is not None:
        mask &= states[:, 0] >= args.min_temperature
    if args.max_temperature is not None:
        mask &= states[:, 0] < args.max_temperature
    filtered = states[mask]
    if args.max_samples is not None and len(filtered) > args.max_samples:
        idx = rng.choice(len(filtered), size=args.max_samples, replace=False)
        filtered = filtered[idx]

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(out_path, filtered)

    metadata = {
        'case_dir': str(Path(args.case_dir).resolve()),
        'time': args.time,
        'output': str(out_path.resolve()),
        'shape': list(filtered.shape),
        'species_names': SPECIES,
        'min_temperature': args.min_temperature,
        'max_temperature': args.max_temperature,
        'max_samples': args.max_samples,
        'seed': args.seed,
        'temperature_summary': {
            'min': float(filtered[:, 0].min()) if len(filtered) else None,
            'p50': float(np.quantile(filtered[:, 0], 0.5)) if len(filtered) else None,
            'p99': float(np.quantile(filtered[:, 0], 0.99)) if len(filtered) else None,
            'max': float(filtered[:, 0].max()) if len(filtered) else None,
            'mean': float(filtered[:, 0].mean()) if len(filtered) else None,
        },
        'pressure_summary': {
            'min': float(filtered[:, 1].min()) if len(filtered) else None,
            'p50': float(np.quantile(filtered[:, 1], 0.5)) if len(filtered) else None,
            'p99': float(np.quantile(filtered[:, 1], 0.99)) if len(filtered) else None,
            'max': float(filtered[:, 1].max()) if len(filtered) else None,
            'mean': float(filtered[:, 1].mean()) if len(filtered) else None,
        },
        'note': 'Current-state extraction from a real DeepFlame C2H4 case/time, intended for targeted chemistry labeling or regime-specific support analysis.',
    }
    metadata_out = Path(args.metadata_out) if args.metadata_out else out_path.with_suffix('.json')
    metadata_out.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print(json.dumps(metadata, indent=2))


if __name__ == '__main__':
    main()
