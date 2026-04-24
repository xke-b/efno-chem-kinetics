#!/usr/bin/env python3
"""Analyze time-resolved divergence between a learned C2H4 DeepFlame case and stock."""

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
KEY_SPECIES = ['C2H5', 'C2H3', 'CH2CHO', 'CH2CO', 'CH2OH', 'HCCO', 'HO2', 'OH', 'CO', 'CO2']
TEMP_BINS = [510.0, 700.0, 900.0, 1200.0, 1600.0, 2600.0]
QDOT_SIGN_EPS = 1e6


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument('--stock-case', required=True)
    p.add_argument('--model-case', required=True)
    p.add_argument('--out-json', required=True)
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



def read_case_time_fields(case_dir: Path, time_name: str) -> dict[str, np.ndarray]:
    processor_dirs = sorted(p for p in case_dir.glob('processor*') if p.is_dir())
    fields = {name: [] for name in ['T', 'p', 'Qdot', *SPECIES]}
    for proc_dir in processor_dirs:
        time_dir = proc_dir / time_name
        t = read_internal_scalar_field(time_dir / 'T.gz')
        fields['T'].append(t)
        n = len(t)
        for name in ['p', 'Qdot', *SPECIES]:
            fields[name].append(read_internal_scalar_field(time_dir / f'{name}.gz', fallback_n_cells=n))
    return {k: np.concatenate(v) for k, v in fields.items()}



def available_numeric_times(case_dir: Path) -> list[str]:
    proc0 = case_dir / 'processor0'
    times = []
    for p in proc0.iterdir():
        if not p.is_dir():
            continue
        try:
            value = float(p.name)
        except ValueError:
            continue
        if value <= 0.0:
            continue
        times.append(p.name)
    return sorted(times, key=float)



def summarize_bin(mask: np.ndarray, stock: dict[str, np.ndarray], model: dict[str, np.ndarray]) -> dict:
    if int(mask.sum()) == 0:
        return {'count': 0}
    stock_q = stock['Qdot'][mask]
    model_q = model['Qdot'][mask]
    strong = (np.abs(stock_q) >= QDOT_SIGN_EPS) | (np.abs(model_q) >= QDOT_SIGN_EPS)
    mismatch = float(np.mean(np.sign(stock_q[strong]) != np.sign(model_q[strong]))) if strong.any() else 0.0
    return {
        'count': int(mask.sum()),
        'stock_qdot_mean': float(np.mean(stock_q)),
        'model_qdot_mean': float(np.mean(model_q)),
        'mean_abs_qdot_diff': float(np.mean(np.abs(model_q - stock_q))),
        'sign_mismatch_fraction_strong_qdot': mismatch,
        'stock_T_mean': float(np.mean(stock['T'][mask])),
        'model_T_mean': float(np.mean(model['T'][mask])),
    }



def per_time_summary(stock: dict[str, np.ndarray], model: dict[str, np.ndarray], frozen_temperature: float) -> dict:
    stock_active = stock['T'] > frozen_temperature
    model_active = model['T'] > frozen_temperature
    union = stock_active | model_active
    stock_q = stock['Qdot'][union]
    model_q = model['Qdot'][union]
    strong = (np.abs(stock_q) >= QDOT_SIGN_EPS) | (np.abs(model_q) >= QDOT_SIGN_EPS)
    mismatch = float(np.mean(np.sign(stock_q[strong]) != np.sign(model_q[strong]))) if strong.any() else 0.0
    species_metrics = {}
    ranked = []
    for name in KEY_SPECIES:
        s = stock[name][union]
        m = model[name][union]
        denom = max(float(np.mean(s)), 1e-20)
        ratio = float(np.mean(m) / denom)
        species_metrics[name] = {
            'stock_mean': float(np.mean(s)),
            'model_mean': float(np.mean(m)),
            'model_to_stock_mean_ratio': ratio,
            'mean_abs_diff': float(np.mean(np.abs(m - s))),
        }
        ranked.append({'species': name, 'abs_log10_ratio': abs(float(np.log10(max(ratio, 1e-20)))) if ratio > 0 else 99.0, 'ratio': ratio})
    bins = {}
    for lo, hi in zip(TEMP_BINS[:-1], TEMP_BINS[1:]):
        mask = union & (stock['T'] >= lo) & (stock['T'] < hi)
        bins[f'{lo:.0f}-{hi:.0f}K'] = summarize_bin(mask, stock, model)
    return {
        'n_active_stock': int(stock_active.sum()),
        'n_active_model': int(model_active.sum()),
        'n_active_union': int(union.sum()),
        'qdot_ratio_model_to_stock_mean': float(np.mean(model_q) / np.mean(stock_q)) if abs(np.mean(stock_q)) > 0 else None,
        'mean_abs_qdot_diff': float(np.mean(np.abs(model_q - stock_q))),
        'sign_mismatch_fraction_strong_qdot': mismatch,
        'mean_abs_T_diff': float(np.mean(np.abs(model['T'][union] - stock['T'][union]))),
        'mean_abs_p_diff': float(np.mean(np.abs(model['p'][union] - stock['p'][union]))),
        'key_species': species_metrics,
        'ranked_species_distortions': sorted(ranked, key=lambda x: x['abs_log10_ratio'], reverse=True),
        'temperature_bin_metrics': bins,
    }



def first_threshold_crossing(times: list[str], per_time: dict[str, dict], predicate) -> str | None:
    for t in times:
        if predicate(per_time[t]):
            return t
    return None



def main() -> None:
    args = parse_args()
    stock_case = Path(args.stock_case)
    model_case = Path(args.model_case)
    stock_times = available_numeric_times(stock_case)
    model_times = available_numeric_times(model_case)
    common_times = [t for t in stock_times if t in set(model_times)]
    per_time = {}
    for t in common_times:
        stock = read_case_time_fields(stock_case, t)
        model = read_case_time_fields(model_case, t)
        per_time[t] = per_time_summary(stock, model, args.frozen_temperature)

    thresholds = {
        'first_qdot_ratio_below_0p5': first_threshold_crossing(common_times, per_time, lambda rec: rec['qdot_ratio_model_to_stock_mean'] is not None and rec['qdot_ratio_model_to_stock_mean'] < 0.5),
        'first_qdot_sign_mismatch_above_0p5': first_threshold_crossing(common_times, per_time, lambda rec: rec['sign_mismatch_fraction_strong_qdot'] > 0.5),
        'first_c2h3_ratio_below_1e-2': first_threshold_crossing(common_times, per_time, lambda rec: rec['key_species']['C2H3']['model_to_stock_mean_ratio'] < 1e-2),
        'first_ch2co_ratio_below_1e-2': first_threshold_crossing(common_times, per_time, lambda rec: rec['key_species']['CH2CO']['model_to_stock_mean_ratio'] < 1e-2),
        'first_ho2_ratio_below_0p5': first_threshold_crossing(common_times, per_time, lambda rec: rec['key_species']['HO2']['model_to_stock_mean_ratio'] < 0.5),
    }

    out = {
        'stock_case': str(stock_case.resolve()),
        'model_case': str(model_case.resolve()),
        'common_times': common_times,
        'frozen_temperature': args.frozen_temperature,
        'per_time': per_time,
        'threshold_crossings': thresholds,
        'note': 'Time-resolved matched-mesh stock-vs-model divergence analysis for C2H4 DeepFlame runs.',
    }
    out_path = Path(args.out_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding='utf-8')
    print(json.dumps({'out_json': str(out_path.resolve())}, indent=2))


if __name__ == '__main__':
    main()
