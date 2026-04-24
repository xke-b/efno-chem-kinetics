#!/usr/bin/env python3
"""Relabel C2H4 case-pair states with one-step Cantera chemistry integration.

This creates a chemistry-only proxy label path from the current-state side of an
existing paired dataset. It is meant to expose label-semantics mismatch between
full-CFD transitions and one-step chemistry evolution under a controlled reactor
assumption, not to claim final target fidelity.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cantera as ct
import numpy as np

KEY_SPECIES = ['C2H5', 'C2H3', 'CH2CHO', 'CH2CO', 'CH2OH', 'HCCO', 'HO2', 'OH', 'CO', 'CO2']


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument('--dataset', required=True)
    p.add_argument('--metadata', required=True)
    p.add_argument('--mech', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--metadata-out', default=None)
    p.add_argument('--summary-out', required=True)
    p.add_argument('--dt', type=float, default=1e-7)
    p.add_argument('--reactor', choices=['const_pressure', 'const_volume'], default='const_pressure')
    p.add_argument('--max-samples', type=int, default=5000)
    p.add_argument('--seed', type=int, default=0)
    p.add_argument('--index-file', default=None, help='Optional JSON file with explicit dataset indices to relabel.')
    return p.parse_args()



def build_reactor(gas: ct.Solution, reactor_kind: str):
    if reactor_kind == 'const_pressure':
        reactor = ct.IdealGasConstPressureReactor(gas, energy='on')
    elif reactor_kind == 'const_volume':
        reactor = ct.IdealGasReactor(gas, energy='on')
    else:
        raise ValueError(f'Unsupported reactor type: {reactor_kind}')
    net = ct.ReactorNet([reactor])
    net.rtol = 1e-9
    net.atol = 1e-15
    return reactor, net



def relabel_row(gas: ct.Solution, row: np.ndarray, n_species: int, dt: float, reactor_kind: str) -> np.ndarray:
    before = row[: 2 + n_species].copy()
    T = float(before[0])
    P = float(before[1])
    Y = before[2:].copy()
    gas.TPY = T, P, Y
    _reactor, net = build_reactor(gas, reactor_kind)
    net.advance(dt)
    after = np.concatenate(([gas.T, gas.P], gas.Y.copy()))
    return np.concatenate([before, after])



def summarize(original: np.ndarray, relabeled: np.ndarray, species_names: list[str]) -> dict:
    n_species = len(species_names)
    orig_next = original[:, 2 + n_species :]
    chem_next = relabeled[:, 2 + n_species :]

    orig_T_next = orig_next[:, 0]
    chem_T_next = chem_next[:, 0]
    orig_P_next = orig_next[:, 1]
    chem_P_next = chem_next[:, 1]
    orig_Y_next = orig_next[:, 2:]
    chem_Y_next = chem_next[:, 2:]

    summary = {
        'rows': int(original.shape[0]),
        'temperature': {
            'orig_mean_next': float(orig_T_next.mean()),
            'chem_mean_next': float(chem_T_next.mean()),
            'mean_abs_next_diff': float(np.mean(np.abs(chem_T_next - orig_T_next))),
        },
        'pressure': {
            'orig_mean_next': float(orig_P_next.mean()),
            'chem_mean_next': float(chem_P_next.mean()),
            'mean_abs_next_diff': float(np.mean(np.abs(chem_P_next - orig_P_next))),
            'orig_mean_abs_delta_p_from_current': float(np.mean(np.abs(orig_P_next - original[:, 1]))),
            'chem_mean_abs_delta_p_from_current': float(np.mean(np.abs(chem_P_next - original[:, 1]))),
        },
        'species_sum': {
            'orig_mean_abs_dev_from_1': float(np.mean(np.abs(orig_Y_next.sum(axis=1) - 1.0))),
            'chem_mean_abs_dev_from_1': float(np.mean(np.abs(chem_Y_next.sum(axis=1) - 1.0))),
        },
        'key_species': {},
    }

    ranked = []
    for name in KEY_SPECIES:
        idx = species_names.index(name)
        o = orig_Y_next[:, idx]
        c = chem_Y_next[:, idx]
        ratio = float(c.mean() / max(o.mean(), 1e-30))
        rec = {
            'orig_mean_next': float(o.mean()),
            'chem_mean_next': float(c.mean()),
            'chem_to_orig_mean_ratio': ratio,
            'mean_abs_next_diff': float(np.mean(np.abs(c - o))),
            'orig_p99_next': float(np.quantile(o, 0.99)),
            'chem_p99_next': float(np.quantile(c, 0.99)),
        }
        summary['key_species'][name] = rec
        ranked.append({
            'species': name,
            'chem_to_orig_mean_ratio': ratio,
            'abs_log10_ratio': abs(float(np.log10(max(ratio, 1e-30)))),
            'orig_mean_next': rec['orig_mean_next'],
            'chem_mean_next': rec['chem_mean_next'],
        })
    summary['ranked_key_species_shift'] = sorted(ranked, key=lambda x: x['abs_log10_ratio'], reverse=True)
    return summary



def main() -> None:
    args = parse_args()
    dataset = np.load(args.dataset)
    meta = json.loads(Path(args.metadata).read_text())
    species_names = meta['species_names']
    n_species = len(species_names)

    if args.index_file:
        selection = json.loads(Path(args.index_file).read_text())
        indices = np.asarray(selection['indices'], dtype=int)
        if indices.ndim != 1:
            raise ValueError('Selection indices must be a 1D list')
        if len(indices) == 0:
            raise ValueError('Selection indices are empty')
        if indices.min() < 0 or indices.max() >= len(dataset):
            raise ValueError('Selection indices out of bounds for dataset')
        subset = dataset[indices]
    else:
        rng = np.random.default_rng(args.seed)
        if args.max_samples is not None and len(dataset) > args.max_samples:
            indices = np.sort(rng.choice(len(dataset), size=args.max_samples, replace=False))
            subset = dataset[indices]
        else:
            indices = np.arange(len(dataset))
            subset = dataset

    gas = ct.Solution(args.mech)
    relabeled_rows = [relabel_row(gas, row, n_species, args.dt, args.reactor) for row in subset]
    relabeled = np.asarray(relabeled_rows, dtype=np.float64)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(out_path, relabeled)

    metadata = {
        'source_dataset': str(Path(args.dataset).resolve()),
        'source_metadata': str(Path(args.metadata).resolve()),
        'output': str(out_path.resolve()),
        'dataset_shape': list(relabeled.shape),
        'selected_indices': {
            'count': int(len(indices)),
            'seed': args.seed,
            'max_samples': args.max_samples,
            'index_file': str(Path(args.index_file).resolve()) if args.index_file else None,
        },
        'mech': str(Path(args.mech).resolve()),
        'reactor': args.reactor,
        'dt': args.dt,
        'species_names': species_names,
        'note': 'Chemistry-only proxy relabeling of case-pair current states with one-step Cantera integration.',
    }
    metadata_out = Path(args.metadata_out) if args.metadata_out else out_path.with_suffix('.json')
    metadata_out.write_text(json.dumps(metadata, indent=2), encoding='utf-8')

    summary = summarize(subset, relabeled, species_names)
    summary.update({
        'source_dataset': str(Path(args.dataset).resolve()),
        'relabeled_dataset': str(out_path.resolve()),
        'mech': str(Path(args.mech).resolve()),
        'reactor': args.reactor,
        'dt': args.dt,
        'selected_rows': int(len(indices)),
    })
    summary_path = Path(args.summary_out)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps({'out': str(out_path.resolve()), 'summary': str(summary_path.resolve())}, indent=2))


if __name__ == '__main__':
    main()
