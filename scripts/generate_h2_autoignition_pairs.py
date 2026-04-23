#!/usr/bin/env python3
"""Generate paired H2 autoignition states for EFNO-style one-step learning.

The script keeps the thermochemical state layout aligned with common DeepFlame/
DFODE-kit conventions:
    [T, P, Y_1, ..., Y_ns]

Example smoke test:
    source /opt/conda/etc/profile.d/conda.sh
    conda activate deepflame
    python scripts/generate_h2_autoignition_pairs.py \
      --mech /opt/src/deepflame-dev/mechanisms/H2/ES80_H2-7-16.yaml \
      --out data/h2_autoignition_smoke.npy \
      --n-init 8 \
      --steps 10 \
      --dt 1e-7
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cantera as ct
import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mech", required=True)
    parser.add_argument("--out", required=True, help="Output .npy path")
    parser.add_argument("--metadata-out", default=None, help="Optional metadata JSON path")
    parser.add_argument("--n-init", type=int, default=5000)
    parser.add_argument("--steps", type=int, default=1000)
    parser.add_argument("--dt", type=float, default=1e-7)
    parser.add_argument("--pressure", type=float, default=ct.one_atm)
    parser.add_argument("--phi-min", type=float, default=0.5)
    parser.add_argument("--phi-max", type=float, default=2.0)
    parser.add_argument("--temp-min", type=float, default=1200.0)
    parser.add_argument("--temp-max", type=float, default=1500.0)
    parser.add_argument("--fuel", default="H2:1")
    parser.add_argument("--oxidizer", default="O2:1,N2:3.76")
    parser.add_argument(
        "--reactor",
        choices=["const_pressure", "const_volume"],
        default="const_pressure",
        help="Paper is ambiguous here; keep it configurable.",
    )
    parser.add_argument("--seed", type=int, default=7)
    return parser.parse_args()


def build_reactor(gas: ct.Solution, reactor_kind: str):
    if reactor_kind == "const_pressure":
        reactor = ct.IdealGasConstPressureReactor(gas, energy="on")
    elif reactor_kind == "const_volume":
        reactor = ct.IdealGasReactor(gas, energy="on")
    else:
        raise ValueError(f"Unsupported reactor type: {reactor_kind}")
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
    reactor, net = build_reactor(gas, reactor_kind)

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
        "mech": str(Path(args.mech).resolve()),
        "output": str(out_path),
        "reactor": args.reactor,
        "n_species": gas.n_species,
        "species_names": gas.species_names,
        "n_reactions": gas.n_reactions,
        "n_init": args.n_init,
        "steps": args.steps,
        "dt": args.dt,
        "pressure": args.pressure,
        "phi_range": [args.phi_min, args.phi_max],
        "temperature_range": [args.temp_min, args.temp_max],
        "fuel": args.fuel,
        "oxidizer": args.oxidizer,
        "seed": args.seed,
        "dataset_shape": list(dataset.shape),
        "state_layout": ["T", "P", *gas.species_names, "T_next", "P_next", *[f"{s}_next" for s in gas.species_names]],
    }

    metadata_out = Path(args.metadata_out).resolve() if args.metadata_out else out_path.with_suffix(".json")
    metadata_out.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"Saved dataset: {out_path}")
    print(f"Saved metadata: {metadata_out}")
    print(f"dataset_shape={dataset.shape}")


if __name__ == "__main__":
    main()
