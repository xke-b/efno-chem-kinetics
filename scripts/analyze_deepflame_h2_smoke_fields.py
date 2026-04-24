#!/usr/bin/env python3
"""Analyze pre-failure DeepFlame H2 smoke-run fields across processors.

Focuses on the written processor fields at a given time and summarizes:
- temperature extremes
- pressure extremes
- species simplex consistency
- DNN-selected cell subsets via `selectDNN`
- largest changes from an earlier reference time
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
    parser.add_argument('--time', default='2e-06')
    parser.add_argument('--reference-time', default='1e-06')
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
            start = i + 3  # first value after opening (
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
    fields = {name: [] for name in ['T', 'p', 'selectDNN', *SPECIES]}
    for proc_dir in processor_dirs:
        time_dir = proc_dir / time_name
        t_values = read_internal_scalar_field(time_dir / 'T.gz')
        fields['T'].append(t_values)
        fallback_n = len(t_values)
        for field_name in ['p', 'selectDNN', *SPECIES]:
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



def summarize_case(case_dir: Path, time_name: str, reference_time: str) -> dict:
    fields = read_case_time_fields(case_dir, time_name)
    ref_fields = read_case_time_fields(case_dir, reference_time)

    species = np.column_stack([fields[name] for name in SPECIES])
    ref_species = np.column_stack([ref_fields[name] for name in SPECIES])
    species_sum = np.sum(species, axis=1)
    ref_species_sum = np.sum(ref_species, axis=1)
    select_mask = fields['selectDNN'] > 0.5
    selected_count = int(np.sum(select_mask))

    low_temp_thresholds = [400.0, 300.0, 200.0, 150.0]
    negative_threshold = -1e-12

    summary = {
        'case': str(case_dir.resolve()),
        'time': time_name,
        'reference_time': reference_time,
        'n_cells_total': int(len(fields['T'])),
        'n_cells_selectDNN': selected_count,
        'temperature': argextrema_info(fields['T']),
        'pressure': argextrema_info(fields['p']),
        'species_sum': {
            'min': float(np.min(species_sum)),
            'max': float(np.max(species_sum)),
            'mean': float(np.mean(species_sum)),
            'mean_abs_deviation_from_1': float(np.mean(np.abs(species_sum - 1.0))),
            'max_abs_deviation_from_1': float(np.max(np.abs(species_sum - 1.0))),
            'min_index': int(np.argmin(species_sum)),
            'max_index': int(np.argmax(species_sum)),
        },
        'selected_cells': {},
        'species': {},
        'deltas_from_reference': {},
    }

    for threshold in low_temp_thresholds:
        summary['selected_cells'][f'fraction_T_lt_{int(threshold)}'] = (
            float(np.mean(fields['T'][select_mask] < threshold)) if selected_count else 0.0
        )
    summary['selected_cells']['temperature'] = (
        argextrema_info(fields['T'][select_mask]) if selected_count else None
    )
    summary['selected_cells']['pressure'] = (
        argextrema_info(fields['p'][select_mask]) if selected_count else None
    )
    if selected_count:
        sel_sum = species_sum[select_mask]
        summary['selected_cells']['species_sum'] = {
            'min': float(np.min(sel_sum)),
            'max': float(np.max(sel_sum)),
            'mean': float(np.mean(sel_sum)),
            'mean_abs_deviation_from_1': float(np.mean(np.abs(sel_sum - 1.0))),
            'max_abs_deviation_from_1': float(np.max(np.abs(sel_sum - 1.0))),
        }

    for i, name in enumerate(SPECIES):
        vals = species[:, i]
        ref_vals = ref_species[:, i]
        delta = vals - ref_vals
        species_summary = {
            'min': float(np.min(vals)),
            'max': float(np.max(vals)),
            'mean': float(np.mean(vals)),
            'fraction_lt_0': float(np.mean(vals < 0.0)),
            'fraction_lt_neg1e12': float(np.mean(vals < negative_threshold)),
            'fraction_gt_1': float(np.mean(vals > 1.0)),
            'largest_abs_delta_from_reference': float(np.max(np.abs(delta))),
            'mean_abs_delta_from_reference': float(np.mean(np.abs(delta))),
        }
        if selected_count:
            sel = vals[select_mask]
            sel_delta = delta[select_mask]
            species_summary['selected_cells'] = {
                'min': float(np.min(sel)),
                'max': float(np.max(sel)),
                'mean': float(np.mean(sel)),
                'fraction_lt_0': float(np.mean(sel < 0.0)),
                'fraction_gt_1': float(np.mean(sel > 1.0)),
                'largest_abs_delta_from_reference': float(np.max(np.abs(sel_delta))),
                'mean_abs_delta_from_reference': float(np.mean(np.abs(sel_delta))),
            }
        summary['species'][name] = species_summary

    temp_delta = fields['T'] - ref_fields['T']
    pressure_delta = fields['p'] - ref_fields['p']
    summary['deltas_from_reference']['T'] = {
        'largest_abs_delta': float(np.max(np.abs(temp_delta))),
        'mean_abs_delta': float(np.mean(np.abs(temp_delta))),
        'min_delta': float(np.min(temp_delta)),
        'max_delta': float(np.max(temp_delta)),
    }
    summary['deltas_from_reference']['p'] = {
        'largest_abs_delta': float(np.max(np.abs(pressure_delta))),
        'mean_abs_delta': float(np.mean(np.abs(pressure_delta))),
        'min_delta': float(np.min(pressure_delta)),
        'max_delta': float(np.max(pressure_delta)),
    }
    sum_delta = species_sum - ref_species_sum
    summary['deltas_from_reference']['species_sum'] = {
        'largest_abs_delta': float(np.max(np.abs(sum_delta))),
        'mean_abs_delta': float(np.mean(np.abs(sum_delta))),
        'min_delta': float(np.min(sum_delta)),
        'max_delta': float(np.max(sum_delta)),
    }
    if selected_count:
        sel_temp_delta = temp_delta[select_mask]
        summary['selected_cells']['deltas_from_reference'] = {
            'T': {
                'largest_abs_delta': float(np.max(np.abs(sel_temp_delta))),
                'mean_abs_delta': float(np.mean(np.abs(sel_temp_delta))),
                'min_delta': float(np.min(sel_temp_delta)),
                'max_delta': float(np.max(sel_temp_delta)),
            }
        }

    return summary



def main() -> None:
    args = parse_args()
    case_dir = Path(args.case)
    summary = summarize_case(case_dir, args.time, args.reference_time)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
