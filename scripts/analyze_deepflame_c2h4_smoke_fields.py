#!/usr/bin/env python3
"""Analyze DeepFlame C2H4 smoke-run fields across processors."""

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
    parser.add_argument('--time', required=True)
    parser.add_argument('--reference-time', default=None)
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
    base_fields = ['T', 'p', 'Qdot', 'mixfrac', 'rho', 'selectDNN']
    fields = {name: [] for name in [*base_fields, *SPECIES]}
    for proc_dir in processor_dirs:
        time_dir = proc_dir / time_name
        t_values = read_internal_scalar_field(time_dir / 'T.gz')
        fields['T'].append(t_values)
        fallback_n = len(t_values)
        for field_name in ['p', 'Qdot', 'mixfrac', 'rho', 'selectDNN', *SPECIES]:
            values = read_internal_scalar_field(time_dir / f'{field_name}.gz', fallback_n_cells=fallback_n)
            fields[field_name].append(values)
    return {name: np.concatenate(chunks) for name, chunks in fields.items()}


def argextrema_info(values: np.ndarray) -> dict[str, float | int]:
    imin = int(np.argmin(values))
    imax = int(np.argmax(values))
    return {
        'min': float(values[imin]),
        'min_index': imin,
        'max': float(values[imax]),
        'max_index': imax,
        'mean': float(np.mean(values)),
    }


def summarize_case(case_dir: Path, time_name: str, reference_time: str | None) -> dict:
    fields = read_case_time_fields(case_dir, time_name)
    ref_fields = read_case_time_fields(case_dir, reference_time) if reference_time else None

    species = np.column_stack([fields[name] for name in SPECIES])
    species_sum = np.sum(species, axis=1)
    select_mask = fields['selectDNN'] > 0.5
    selected_count = int(np.sum(select_mask))

    summary = {
        'case': str(case_dir.resolve()),
        'time': time_name,
        'reference_time': reference_time,
        'n_cells_total': int(len(fields['T'])),
        'n_cells_selectDNN': selected_count,
        'selectDNN_unique_values': [float(x) for x in np.unique(fields['selectDNN'])[:20]],
        'temperature': argextrema_info(fields['T']),
        'pressure': argextrema_info(fields['p']),
        'qdot': argextrema_info(fields['Qdot']),
        'mixfrac': argextrema_info(fields['mixfrac']),
        'rho': argextrema_info(fields['rho']),
        'species_sum': {
            'min': float(np.min(species_sum)),
            'max': float(np.max(species_sum)),
            'mean': float(np.mean(species_sum)),
            'mean_abs_deviation_from_1': float(np.mean(np.abs(species_sum - 1.0))),
            'max_abs_deviation_from_1': float(np.max(np.abs(species_sum - 1.0))),
        },
        'species': {},
    }

    for name in SPECIES:
        vals = fields[name]
        summary['species'][name] = {
            'min': float(np.min(vals)),
            'max': float(np.max(vals)),
            'mean': float(np.mean(vals)),
            'fraction_lt_0': float(np.mean(vals < 0.0)),
            'fraction_gt_1': float(np.mean(vals > 1.0)),
        }

    if ref_fields is not None:
        ref_species = np.column_stack([ref_fields[name] for name in SPECIES])
        ref_species_sum = np.sum(ref_species, axis=1)
        temp_delta = fields['T'] - ref_fields['T']
        qdot_delta = fields['Qdot'] - ref_fields['Qdot']
        species_sum_delta = species_sum - ref_species_sum
        summary['deltas_from_reference'] = {
            'T': {
                'largest_abs_delta': float(np.max(np.abs(temp_delta))),
                'mean_abs_delta': float(np.mean(np.abs(temp_delta))),
                'min_delta': float(np.min(temp_delta)),
                'max_delta': float(np.max(temp_delta)),
            },
            'Qdot': {
                'largest_abs_delta': float(np.max(np.abs(qdot_delta))),
                'mean_abs_delta': float(np.mean(np.abs(qdot_delta))),
                'min_delta': float(np.min(qdot_delta)),
                'max_delta': float(np.max(qdot_delta)),
            },
            'species_sum': {
                'largest_abs_delta': float(np.max(np.abs(species_sum_delta))),
                'mean_abs_delta': float(np.mean(np.abs(species_sum_delta))),
                'min_delta': float(np.min(species_sum_delta)),
                'max_delta': float(np.max(species_sum_delta)),
            },
        }

    return summary


def main() -> None:
    args = parse_args()
    summary = summarize_case(Path(args.case), args.time, args.reference_time)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
