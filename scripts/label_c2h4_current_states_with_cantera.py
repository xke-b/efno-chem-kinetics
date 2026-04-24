#!/usr/bin/env python3
"""Label current-state C2H4 datasets with one-step Cantera chemistry in chunks.

This is a scale-ready path for solver-native / Xiao-style current-state manifolds.
It accepts an `N x (2 + n_species)` current-state dataset `[T, P, Y...]` and
writes an `N x 2*(2+n_species)` paired dataset `[state_t, state_t+dt]` without
holding the full labeled output in RAM.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import cantera as ct
import numpy as np


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument('--dataset', required=True)
    p.add_argument('--metadata', default=None, help='Optional metadata JSON carrying input species_names order')
    p.add_argument('--mech', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--metadata-out', default=None)
    p.add_argument('--dt', type=float, default=1e-7)
    p.add_argument('--reactor', choices=['const_pressure', 'const_volume'], default='const_pressure')
    p.add_argument('--chunk-size', type=int, default=2000)
    p.add_argument('--max-samples', type=int, default=None)
    return p.parse_args()



def build_reactor(gas: ct.Solution, reactor_kind: str):
    if reactor_kind == 'const_pressure':
        reactor = ct.IdealGasConstPressureReactor(gas, energy='on')
    elif reactor_kind == 'const_volume':
        reactor = ct.IdealGasReactor(gas, energy='on')
    else:
        raise ValueError(f'Unsupported reactor kind: {reactor_kind}')
    net = ct.ReactorNet([reactor])
    net.rtol = 1e-9
    net.atol = 1e-15
    return reactor, net



def advance_state(gas: ct.Solution, row: np.ndarray, dt: float, reactor_kind: str) -> np.ndarray:
    gas.TPY = float(row[0]), float(row[1]), np.clip(row[2:], 0.0, 1.0)
    _reactor, net = build_reactor(gas, reactor_kind)
    net.advance(dt)
    return np.concatenate(([gas.T, gas.P], gas.Y.copy()))



def permutation(source: list[str], target: list[str]) -> np.ndarray:
    if source == target:
        return np.arange(len(source), dtype=np.int64)
    if set(source) != set(target):
        raise ValueError('Source and target species sets differ; cannot build permutation')
    source_index = {name: i for i, name in enumerate(source)}
    return np.array([source_index[name] for name in target], dtype=np.int64)



def main() -> None:
    args = parse_args()
    dataset_path = Path(args.dataset).resolve()
    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    current_states = np.load(dataset_path, mmap_mode='r')
    if current_states.ndim != 2:
        raise ValueError(f'Expected a 2D dataset, got shape {current_states.shape}')

    total_rows = int(current_states.shape[0])
    n_cols = int(current_states.shape[1])
    if args.max_samples is not None:
        total_rows = min(total_rows, int(args.max_samples))
    if total_rows <= 0:
        raise ValueError('No rows selected for labeling')

    gas = ct.Solution(str(Path(args.mech).resolve()))
    expected_cols = 2 + gas.n_species
    if n_cols != expected_cols:
        raise ValueError(f'Expected {expected_cols} columns from mechanism, got {n_cols}')

    mech_species = list(gas.species_names)
    input_species = mech_species
    if args.metadata:
        meta = json.loads(Path(args.metadata).read_text())
        input_species = list(meta.get('species_names', mech_species))
    if len(input_species) != gas.n_species:
        raise ValueError('Input species_names length does not match mechanism species count')
    to_mech = permutation(input_species, mech_species)
    from_mech = permutation(mech_species, input_species)

    labeled = np.lib.format.open_memmap(
        out_path,
        mode='w+',
        dtype=np.float64,
        shape=(total_rows, 2 * n_cols),
    )

    start = time.time()
    rows_done = 0
    chunk_timings = []
    for start_idx in range(0, total_rows, args.chunk_size):
        stop_idx = min(start_idx + args.chunk_size, total_rows)
        chunk = np.asarray(current_states[start_idx:stop_idx], dtype=np.float64)
        t0 = time.time()
        next_chunk = np.empty_like(chunk)
        chunk_mech = np.column_stack([chunk[:, :2], chunk[:, 2:][:, to_mech]])
        for i, row in enumerate(chunk_mech):
            next_mech = advance_state(gas, row, args.dt, args.reactor)
            next_chunk[i, :2] = next_mech[:2]
            next_chunk[i, 2:] = next_mech[2:][from_mech]
        labeled[start_idx:stop_idx, :n_cols] = chunk
        labeled[start_idx:stop_idx, n_cols:] = next_chunk
        labeled.flush()
        elapsed = time.time() - t0
        rows_done = stop_idx
        rows_per_sec = (stop_idx - start_idx) / max(elapsed, 1e-12)
        chunk_timings.append({
            'start': int(start_idx),
            'stop': int(stop_idx),
            'rows': int(stop_idx - start_idx),
            'seconds': elapsed,
            'rows_per_second': rows_per_sec,
        })
        print(json.dumps({
            'progress_rows': rows_done,
            'total_rows': total_rows,
            'chunk_rows': int(stop_idx - start_idx),
            'chunk_seconds': elapsed,
            'chunk_rows_per_second': rows_per_sec,
        }))

    total_seconds = time.time() - start
    overall_rows_per_second = total_rows / max(total_seconds, 1e-12)

    metadata = {
        'source_dataset': str(dataset_path),
        'output': str(out_path),
        'mech': str(Path(args.mech).resolve()),
        'dt': args.dt,
        'reactor': args.reactor,
        'chunk_size': args.chunk_size,
        'selected_rows': total_rows,
        'input_shape': [int(total_rows), int(n_cols)],
        'output_shape': [int(total_rows), int(2 * n_cols)],
        'species_names': input_species,
        'mechanism_species_names': mech_species,
        'total_seconds': total_seconds,
        'overall_rows_per_second': overall_rows_per_second,
        'chunk_timings': chunk_timings,
        'note': 'Chunked one-step chemistry labeling for current-state C2H4 datasets using energy-on Cantera reactors.',
    }
    metadata_out = Path(args.metadata_out).resolve() if args.metadata_out else out_path.with_suffix('.json')
    metadata_out.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print(json.dumps(metadata, indent=2))


if __name__ == '__main__':
    main()
