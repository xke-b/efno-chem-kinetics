#!/usr/bin/env python3
"""Compare real-CFD regime states against training datasets via local nearest-neighbor label support.

This diagnoses whether the current paired datasets provide locally similar chemistry
labels for the exact cool-onset and hot-active states observed in the CFD case.
"""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

import cantera as ct
import numpy as np

SPECIES = [
    'H', 'H2', 'O', 'O2', 'OH', 'H2O', 'HO2', 'CO', 'CO2', 'HCO', 'CH3', 'CH4',
    'CH2O', 'T-CH2', 'S-CH2', 'C2H4', 'C2H5', 'C2H2', 'C2H3', 'CH2CHO',
    'HCCO', 'CH2CO', 'CH2OH', 'N2'
]
KEY_SPECIES = ['C2H5', 'C2H3', 'CH2CHO', 'CH2CO', 'CH2OH', 'HCCO', 'HO2', 'OH', 'CO', 'CO2']
BCT_LAMBDA = 0.1


def BCT(x: np.ndarray, lam: float = BCT_LAMBDA) -> np.ndarray:
    x = np.clip(x, 0.0, None)
    if abs(lam) < 1e-12:
        return np.log(np.clip(x, 1e-30, None))
    return (np.power(np.clip(x, 1e-30, None), lam) - 1.0) / lam



def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument('--case-dir', required=True)
    p.add_argument('--time', required=True)
    p.add_argument('--mech', required=True)
    p.add_argument('--dt', type=float, default=1e-7)
    p.add_argument('--datasets', nargs='+', required=True)
    p.add_argument('--dataset-metadata-files', nargs='*', default=None)
    p.add_argument('--dataset-labels', nargs='+', required=True)
    p.add_argument('--frozen-temperature', type=float, default=510.0)
    p.add_argument('--cool-max-temperature', type=float, default=700.0)
    p.add_argument('--hot-min-temperature', type=float, default=1600.0)
    p.add_argument('--hot-max-temperature', type=float, default=2600.0)
    p.add_argument('--max-hot-samples', type=int, default=580)
    p.add_argument('--seed', type=int, default=0)
    p.add_argument('--out-json', required=True)
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



def read_case_states(case_dir: Path, time_name: str) -> np.ndarray:
    chunks = []
    for proc_dir in sorted(p for p in case_dir.glob('processor*') if p.is_dir()):
        time_dir = proc_dir / time_name
        t = read_internal_scalar_field(time_dir / 'T.gz')
        p = read_internal_scalar_field(time_dir / 'p.gz', fallback_n_cells=len(t))
        species = [read_internal_scalar_field(time_dir / f'{name}.gz', fallback_n_cells=len(t)) for name in SPECIES]
        chunks.append(np.column_stack([t, p, *species]))
    return np.concatenate(chunks, axis=0)



def permutation(source: list[str], target: list[str]) -> np.ndarray:
    if source == target:
        return np.arange(len(source), dtype=np.int64)
    if set(source) != set(target):
        raise ValueError('Source and target species sets differ; cannot build permutation')
    src_index = {name: i for i, name in enumerate(source)}
    return np.array([src_index[name] for name in target], dtype=np.int64)



def cvode_next(states: np.ndarray, mech: str, dt: float) -> np.ndarray:
    gas = ct.Solution(mech)
    mech_species = list(gas.species_names)
    to_mech = permutation(SPECIES, mech_species)
    from_mech = permutation(mech_species, SPECIES)
    out = np.empty((states.shape[0], len(SPECIES)), dtype=np.float64)
    for i, row in enumerate(states):
        gas.TPY = float(row[0]), float(row[1]), np.clip(row[2:][to_mech], 0.0, 1.0)
        reactor = ct.IdealGasConstPressureReactor(gas, energy='on')
        net = ct.ReactorNet([reactor])
        net.rtol = 1e-9
        net.atol = 1e-15
        net.advance(dt)
        out[i] = gas.Y.copy()[from_mech]
    return out



def state_features(states: np.ndarray) -> np.ndarray:
    return np.column_stack([states[:, 0], states[:, 1], BCT(states[:, 2:])])



def nearest_neighbor_indices(query: np.ndarray, ref: np.ndarray, query_chunk: int = 128, ref_chunk: int = 4096) -> tuple[np.ndarray, np.ndarray]:
    ref_sq = np.sum(ref * ref, axis=1)
    out_idx = np.empty(query.shape[0], dtype=np.int64)
    out_dist = np.empty(query.shape[0], dtype=np.float64)
    for qs in range(0, query.shape[0], query_chunk):
        qe = min(qs + query_chunk, query.shape[0])
        q = query[qs:qe]
        q_sq = np.sum(q * q, axis=1, keepdims=True)
        best_dist = np.full(q.shape[0], np.inf, dtype=np.float64)
        best_idx = np.full(q.shape[0], -1, dtype=np.int64)
        for rs in range(0, ref.shape[0], ref_chunk):
            re = min(rs + ref_chunk, ref.shape[0])
            dots = q @ ref[rs:re].T
            d2 = np.maximum(q_sq + ref_sq[None, rs:re] - 2.0 * dots, 0.0)
            local_idx = np.argmin(d2, axis=1)
            local_best = d2[np.arange(q.shape[0]), local_idx]
            update = local_best < best_dist
            best_dist[update] = local_best[update]
            best_idx[update] = rs + local_idx[update]
        out_idx[qs:qe] = best_idx
        out_dist[qs:qe] = np.sqrt(best_dist)
    return out_idx, out_dist



def summarize(values: np.ndarray) -> dict[str, float]:
    return {
        'mean': float(np.mean(values)),
        'p50': float(np.quantile(values, 0.5)),
        'p90': float(np.quantile(values, 0.9)),
        'p99': float(np.quantile(values, 0.99)),
        'max': float(np.max(values)),
    }



def delta_metrics(pred: np.ndarray, true: np.ndarray) -> dict:
    err = pred - true
    return {
        'mae': float(np.mean(np.abs(err))),
        'rmse': float(np.sqrt(np.mean(err ** 2))),
        'activity_l1_ratio_mean': float(np.mean(np.sum(np.abs(pred), axis=1) / np.clip(np.sum(np.abs(true), axis=1), 1e-30, None))),
        'pred_l1_mean': float(np.mean(np.sum(np.abs(pred), axis=1))),
        'true_l1_mean': float(np.mean(np.sum(np.abs(true), axis=1))),
    }



def per_species_metrics(pred: np.ndarray, true: np.ndarray) -> dict:
    out = {}
    for name in KEY_SPECIES:
        idx = SPECIES.index(name)
        err = pred[:, idx] - true[:, idx]
        out[name] = {
            'mae': float(np.mean(np.abs(err))),
            'pred_mean': float(np.mean(pred[:, idx])),
            'true_mean': float(np.mean(true[:, idx])),
        }
    return out



def dataset_pairs(path: Path, metadata_path: Path | None) -> tuple[np.ndarray, np.ndarray]:
    arr = np.load(path)
    width = 2 + len(SPECIES)
    current = arr[:, :width]
    nxt = arr[:, width:]
    if metadata_path is not None:
        meta = json.loads(metadata_path.read_text())
        species_names = list(meta.get('species_names', SPECIES))
        if species_names != SPECIES:
            order = permutation(species_names, SPECIES)
            current = np.column_stack([current[:, :2], current[:, 2:][:, order]])
            nxt = np.column_stack([nxt[:, :2], nxt[:, 2:][:, order]])
    return current, nxt



def main() -> None:
    args = parse_args()
    if len(args.datasets) != len(args.dataset_labels):
        raise ValueError('datasets and dataset-labels length mismatch')
    if args.dataset_metadata_files is None or len(args.dataset_metadata_files) == 0:
        dataset_metadata_files = [str(Path(p).with_suffix('.json')) for p in args.datasets]
    else:
        dataset_metadata_files = args.dataset_metadata_files
    if len(dataset_metadata_files) != len(args.datasets):
        raise ValueError('dataset-metadata-files and datasets length mismatch')
    rng = np.random.default_rng(args.seed)

    case_states = read_case_states(Path(args.case_dir), args.time)
    active = case_states[case_states[:, 0] > args.frozen_temperature]
    cool = active[(active[:, 0] >= args.frozen_temperature) & (active[:, 0] < args.cool_max_temperature)]
    hot_pool = active[(active[:, 0] >= args.hot_min_temperature) & (active[:, 0] < args.hot_max_temperature)]
    if len(cool) == 0 or len(hot_pool) == 0:
        raise ValueError('Missing cool or hot regime states')
    hot_n = min(args.max_hot_samples, len(hot_pool))
    hot = hot_pool[rng.choice(len(hot_pool), size=hot_n, replace=False)]

    benchmark = {
        'cool_onset_510_700K': cool,
        f'hot_active_{int(args.hot_min_temperature)}_{int(args.hot_max_temperature)}K': hot,
    }

    benchmark_all = np.concatenate(list(benchmark.values()), axis=0)
    feat_all = state_features(benchmark_all)
    feat_mean = feat_all.mean(axis=0)
    feat_std = feat_all.std(axis=0)
    feat_std = np.where(feat_std < 1e-12, 1.0, feat_std)

    results = {
        'case_dir': str(Path(args.case_dir).resolve()),
        'time': args.time,
        'mech': str(Path(args.mech).resolve()),
        'dt': args.dt,
        'benchmark_sizes': {name: int(len(states)) for name, states in benchmark.items()},
        'regimes': {},
        'datasets': {},
        'note': 'Nearest-neighbor current-state support and local label mismatch between real CFD regimes and offline paired datasets. Query truth is one-step Cantera/CVODE chemistry from the CFD state itself.',
    }

    truth = {}
    for regime_name, states in benchmark.items():
        next_y = cvode_next(states, args.mech, args.dt)
        true_delta = next_y - states[:, 2:]
        truth[regime_name] = true_delta
        results['regimes'][regime_name] = {
            'count': int(len(states)),
            'temperature': summarize(states[:, 0]),
            'pressure': summarize(states[:, 1]),
            'true_delta': delta_metrics(true_delta, true_delta),
            'true_delta_key_species': per_species_metrics(true_delta, true_delta),
        }

    for label, path_str, meta_str in zip(args.dataset_labels, args.datasets, dataset_metadata_files):
        meta_path = Path(meta_str) if meta_str else None
        current, nxt = dataset_pairs(Path(path_str), meta_path if meta_path and meta_path.exists() else None)
        ref_feat = (state_features(current) - feat_mean) / feat_std
        ref_delta = nxt[:, 2:] - current[:, 2:]
        ds_result = {
            'dataset': str(Path(path_str).resolve()),
            'metadata': str(meta_path.resolve()) if meta_path and meta_path.exists() else None,
            'rows': int(len(current)),
            'regimes': {},
        }
        for regime_name, states in benchmark.items():
            query_feat = (state_features(states) - feat_mean) / feat_std
            nn_idx, nn_dist = nearest_neighbor_indices(query_feat, ref_feat)
            neighbor_delta = ref_delta[nn_idx]
            true_delta = truth[regime_name]
            ds_result['regimes'][regime_name] = {
                'nn_distance': summarize(nn_dist),
                'neighbor_label_delta': delta_metrics(neighbor_delta, true_delta),
                'neighbor_label_key_species': per_species_metrics(neighbor_delta, true_delta),
                'neighbor_temperature': summarize(current[nn_idx, 0]),
                'neighbor_pressure': summarize(current[nn_idx, 1]),
            }
        results['datasets'][label] = ds_result

    out_path = Path(args.out_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(json.dumps({'out_json': str(out_path.resolve())}, indent=2))


if __name__ == '__main__':
    main()
