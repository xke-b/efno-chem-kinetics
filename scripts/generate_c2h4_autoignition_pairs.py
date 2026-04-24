#!/usr/bin/env python3
"""Generate paired C2H4 autoignition states for one-step learning.

This mirrors the H2 generator but defaults to the 24-species Wu mechanism and
C2H4/air mixtures so the resulting dataset is at least mechanism- and
chemistry-timestep-aligned with the stock DeepFlame C2H4 case.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cantera as ct
import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--mech', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--metadata-out', default=None)
    parser.add_argument('--n-init', type=int, default=200)
    parser.add_argument('--steps', type=int, default=200)
    parser.add_argument('--dt', type=float, default=1e-7)
    parser.add_argument('--pressure', type=float, default=ct.one_atm)
    parser.add_argument('--phi-min', type=float, default=0.6)
    parser.add_argument('--phi-max', type=float, default=1.8)
    parser.add_argument('--temp-min', type=float, default=1000.0)
    parser.add_argument('--temp-max', type=float, default=1800.0)
    parser.add_argument('--fuel', default='C2H4:1')
    parser.add_argument('--oxidizer', default='O2:1,N2:3.76')
    parser.add_argument(
        '--reactor',
        choices=['const_pressure', 'const_volume'],
        default='const_pressure',
        help='Keep configurable; exact stock-case correspondence is not claimed yet.',
    )
    parser.add_argument('--seed', type=int, default=11)
    return parser.parse_args()



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



def advance_case(
    gas: ct.Solution,
    phi: float,
    temperature: float,
    pressure: float,
    fuel: str,
    oxidizer: str,
    dt: float,
    steps: int,
    reactor_kind: str,
) -> np.ndarray:
    gas.TP = temperature, pressure
    gas.set_equivalence_ratio(phi, fuel=fuel, oxidizer=oxidizer)
    _reactor, net = build_reactor(gas, reactor_kind)

    rows = []
    for _ in range(steps):
        before = np.concatenate(([gas.T, gas.P], gas.Y.copy()))
        net.advance(net.time + dt)
        after = np.concatenate(([gas.T, gas.P], gas.Y.copy()))
        rows.append(np.concatenate((before, after)))
    return np.asarray(rows, dtype=np.float64)



def main() -> None:
    args = parse_args()
    rng = np.random.default_rng(args.seed)
    gas = ct.Solution(args.mech)

    phi_samples = rng.uniform(args.phi_min, args.phi_max, size=args.n_init)
    temp_samples = rng.uniform(args.temp_min, args.temp_max, size=args.n_init)

    pairs = []
    for phi, temp in zip(phi_samples, temp_samples):
        pairs.append(
            advance_case(
                gas=gas,
                phi=float(phi),
                temperature=float(temp),
                pressure=args.pressure,
                fuel=args.fuel,
                oxidizer=args.oxidizer,
                dt=args.dt,
                steps=args.steps,
                reactor_kind=args.reactor,
            )
        )

    dataset = np.vstack(pairs)
    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(out_path, dataset)

    metadata = {
        'mech': str(Path(args.mech).resolve()),
        'output': str(out_path),
        'reactor': args.reactor,
        'n_species': gas.n_species,
        'species_names': gas.species_names,
        'n_reactions': gas.n_reactions,
        'n_init': args.n_init,
        'steps': args.steps,
        'dt': args.dt,
        'pressure': args.pressure,
        'phi_range': [args.phi_min, args.phi_max],
        'temperature_range': [args.temp_min, args.temp_max],
        'fuel': args.fuel,
        'oxidizer': args.oxidizer,
        'seed': args.seed,
        'dataset_shape': list(dataset.shape),
        'state_layout': ['T', 'P', *gas.species_names, 'T_next', 'P_next', *[f'{s}_next' for s in gas.species_names]],
        'note': 'Homogeneous C2H4 autoignition smoke dataset aligned to Wu24sp + dt=1e-7, not yet CFD-state sampled.',
    }

    metadata_out = Path(args.metadata_out).resolve() if args.metadata_out else out_path.with_suffix('.json')
    metadata_out.write_text(json.dumps(metadata, indent=2), encoding='utf-8')

    print(f'Saved dataset: {out_path}')
    print(f'Saved metadata: {metadata_out}')
    print(f'dataset_shape={dataset.shape}')


if __name__ == '__main__':
    main()
