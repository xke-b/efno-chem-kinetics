#!/usr/bin/env python3
"""Extract paired CFD states from a DeepFlame C2H4 case.

This is a first case-aligned data path for C2H4 replacement work. It does not
isolate chemistry-only evolution; it snapshots full CFD state changes between
written times at fixed cell ordering within each processor. Use it as a
case-aligned surrogate-data prototype, not as a final chemistry-only labeler.
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
    parser.add_argument('--times', nargs='+', required=True, help='Ordered written times to pair consecutively')
    parser.add_argument('--out', required=True)
    parser.add_argument('--metadata-out', default=None)
    parser.add_argument('--frozen-temperature', type=float, default=None)
    parser.add_argument('--max-samples-per-pair', type=int, default=None)
    parser.add_argument('--max-abs-delta-p', type=float, default=None)
    parser.add_argument('--max-rel-delta-p', type=float, default=None)
    parser.add_argument('--seed', type=int, default=0)
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



def main() -> None:
    args = parse_args()
    rng = np.random.default_rng(args.seed)
    case_dir = Path(args.case)
    times = args.times

    state_blocks = {time_name: read_case_time_states(case_dir, time_name) for time_name in times}
    rows = []
    pair_counts = {}
    for current_time, next_time in zip(times[:-1], times[1:]):
        current = state_blocks[current_time]
        nxt = state_blocks[next_time]
        if current.shape != nxt.shape:
            raise ValueError(f'Shape mismatch for pair {current_time}->{next_time}: {current.shape} vs {nxt.shape}')
        mask = np.ones(len(current), dtype=bool)
        if args.frozen_temperature is not None:
            mask &= current[:, 0] > args.frozen_temperature
        abs_delta_p = np.abs(nxt[:, 1] - current[:, 1])
        rel_delta_p = abs_delta_p / np.maximum(np.abs(current[:, 1]), 1.0)
        if args.max_abs_delta_p is not None:
            mask &= abs_delta_p <= args.max_abs_delta_p
        if args.max_rel_delta_p is not None:
            mask &= rel_delta_p <= args.max_rel_delta_p
        indices = np.flatnonzero(mask)
        if args.max_samples_per_pair is not None and len(indices) > args.max_samples_per_pair:
            indices = rng.choice(indices, size=args.max_samples_per_pair, replace=False)
        pair_rows = np.hstack([current[indices], nxt[indices]])
        rows.append(pair_rows)
        pair_counts[f'{current_time}->{next_time}'] = int(len(indices))

    dataset = np.concatenate(rows, axis=0) if rows else np.empty((0, 2 * (2 + len(SPECIES))), dtype=np.float64)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(out_path, dataset)

    metadata = {
        'case': str(case_dir.resolve()),
        'times': times,
        'pair_counts': pair_counts,
        'dataset_shape': list(dataset.shape),
        'n_species': len(SPECIES),
        'species_names': SPECIES,
        'frozen_temperature_filter': args.frozen_temperature,
        'max_samples_per_pair': args.max_samples_per_pair,
        'max_abs_delta_p_filter': args.max_abs_delta_p,
        'max_rel_delta_p_filter': args.max_rel_delta_p,
        'seed': args.seed,
        'state_layout': ['T', 'P', *SPECIES, 'T_next', 'P_next', *[f'{s}_next' for s in SPECIES]],
        'note': 'Case-aligned CFD state-pair extractor. These pairs include full CFD evolution between written times, not isolated chemistry-only labels.',
    }

    metadata_out = Path(args.metadata_out) if args.metadata_out else out_path.with_suffix('.json')
    metadata_out.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print(json.dumps(metadata, indent=2))


if __name__ == '__main__':
    main()
