#!/usr/bin/env python3
"""Generate C2H4 labeled pairs from a canonical 1D flame with interpolation + perturbation.

This is a first local-paper-inspired data path for C2H4:
- solve a 1D freely propagating premixed flame in Cantera
- collect canonical flame states
- densify the flame structure by interpolation in temperature space
- perturb states in a physics-aware way
- label perturbed states with one-step chemistry integration
- filter aggressively with simple physical checks (including HRR-ratio)

It is intentionally a small, reproducible prototype rather than a final data pipeline.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cantera as ct
import numpy as np


INERT_CANDIDATES = {'N2', 'AR', 'HE'}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--mech', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--metadata-out', default=None)
    parser.add_argument('--phi', type=float, default=1.0)
    parser.add_argument('--pressure', type=float, default=ct.one_atm)
    parser.add_argument('--tin', type=float, default=300.0)
    parser.add_argument('--width', type=float, default=0.03)
    parser.add_argument('--fuel', default='C2H4:1')
    parser.add_argument('--oxidizer', default='O2:1,N2:3.76')
    parser.add_argument('--dt', type=float, default=1e-7)
    parser.add_argument('--transport', default='Mix')
    parser.add_argument('--refine-ratio', type=float, default=3.0)
    parser.add_argument('--refine-slope', type=float, default=0.05)
    parser.add_argument('--refine-curve', type=float, default=0.10)
    parser.add_argument('--interp-temp-step', type=float, default=5.0)
    parser.add_argument('--perturb-copies', type=int, default=2)
    parser.add_argument('--alpha-t', type=float, default=100.0)
    parser.add_argument('--alpha-p-frac', type=float, default=0.15)
    parser.add_argument('--alpha-y', type=float, default=0.15)
    parser.add_argument('--min-temp', type=float, default=290.0)
    parser.add_argument('--max-extra-temp', type=float, default=100.0)
    parser.add_argument('--hrr-ratio-limit', type=float, default=100.0)
    parser.add_argument('--max-attempts', type=int, default=20)
    parser.add_argument('--seed', type=int, default=0)
    return parser.parse_args()



def solve_free_flame(gas: ct.Solution, args: argparse.Namespace) -> ct.FreeFlame:
    gas.TP = args.tin, args.pressure
    gas.set_equivalence_ratio(args.phi, fuel=args.fuel, oxidizer=args.oxidizer)
    flame = ct.FreeFlame(gas, width=args.width)
    flame.transport_model = args.transport
    flame.set_refine_criteria(ratio=args.refine_ratio, slope=args.refine_slope, curve=args.refine_curve)
    flame.solve(loglevel=0, auto=True)
    return flame



def inert_index(species_names: list[str]) -> int:
    for i, name in enumerate(species_names):
        if name.upper() in INERT_CANDIDATES:
            return i
    return len(species_names) - 1



def flame_states(flame: ct.FreeFlame) -> np.ndarray:
    temps = np.asarray(flame.T)
    pressure = float(flame.P)
    Y = np.asarray(flame.Y).T
    return np.column_stack([temps, np.full_like(temps, pressure), Y])



def interpolate_by_temperature(states: np.ndarray, temp_step: float) -> np.ndarray:
    order = np.argsort(states[:, 0])
    states = states[order]
    temps = states[:, 0]
    t_grid = np.arange(float(temps.min()), float(temps.max()) + temp_step, temp_step)

    rows = [states]
    for t_new in t_grid:
        idx = np.searchsorted(temps, t_new)
        if idx <= 0 or idx >= len(temps):
            continue
        t0, t1 = temps[idx - 1], temps[idx]
        if t1 <= t0 or not (t0 < t_new < t1):
            continue
        w = (t_new - t0) / (t1 - t0)
        interp = states[idx - 1] + w * (states[idx] - states[idx - 1])
        rows.append(interp[None, :])
    out = np.vstack(rows)
    uniq = np.unique(np.round(out, decimals=12), axis=0)
    return uniq



def heat_release_rate(gas: ct.Solution, state: np.ndarray) -> float:
    gas.TPY = float(state[0]), float(state[1]), state[2:]
    return float(gas.heat_release_rate)



def label_state(gas: ct.Solution, state: np.ndarray, dt: float) -> np.ndarray:
    gas.TPY = float(state[0]), float(state[1]), state[2:]
    reactor = ct.IdealGasConstPressureReactor(gas, energy='on')
    net = ct.ReactorNet([reactor])
    net.rtol = 1e-9
    net.atol = 1e-15
    before = np.concatenate(([gas.T, gas.P], gas.Y.copy()))
    net.advance(dt)
    after = np.concatenate(([gas.T, gas.P], gas.Y.copy()))
    return np.concatenate([before, after])



def perturb_state(
    state: np.ndarray,
    *,
    rng: np.random.Generator,
    t_min: float,
    t_max: float,
    p_min: float,
    p_max: float,
    alpha_t: float,
    alpha_p_frac: float,
    alpha_y: float,
    inert_idx: int,
) -> np.ndarray:
    out = state.copy()
    out[0] = out[0] + alpha_t * rng.uniform(-1.0, 1.0)
    out[1] = out[1] + (p_max - p_min) * alpha_p_frac * rng.uniform(-1.0, 1.0)

    reactive = out[2:].copy()
    inert_value = reactive[inert_idx]
    for i in range(len(reactive)):
        if i == inert_idx:
            continue
        reactive[i] = reactive[i] ** (1.0 + alpha_y * rng.uniform(-1.0, 1.0)) if reactive[i] > 0 else 0.0
    reactive = np.clip(reactive, 0.0, 1.0)
    reactive[inert_idx] = inert_value
    reactive_sum = np.sum(np.delete(reactive, inert_idx))
    if reactive_sum > 0 and inert_value < 1.0:
        scale = max(1.0 - inert_value, 0.0) / reactive_sum
        for i in range(len(reactive)):
            if i != inert_idx:
                reactive[i] *= scale
    out[2:] = reactive
    out[0] = float(np.clip(out[0], t_min, t_max))
    out[1] = max(float(out[1]), 1.0)
    out[2:] = np.clip(out[2:], 0.0, 1.0)
    return out



def maybe_keep_pair(
    gas: ct.Solution,
    original_state: np.ndarray,
    perturbed_state: np.ndarray,
    dt: float,
    hrr_ratio_limit: float,
) -> tuple[bool, np.ndarray | None, dict]:
    base_hrr = heat_release_rate(gas, original_state)
    pert_hrr = heat_release_rate(gas, perturbed_state)
    pair = label_state(gas, perturbed_state, dt)
    next_state = pair[len(pair) // 2 :]
    next_y = next_state[2:]
    valid = True
    reason = 'kept'

    if not np.isfinite(pair).all():
        valid = False
        reason = 'nonfinite_label'
    elif np.any(next_y < -1e-10) or np.any(next_y > 1 + 1e-10):
        valid = False
        reason = 'species_bounds'
    elif abs(float(np.sum(next_y)) - 1.0) > 1e-4:
        valid = False
        reason = 'species_sum'
    else:
        if abs(base_hrr) > 1e-12:
            ratio = abs(pert_hrr) / abs(base_hrr)
            if ratio > hrr_ratio_limit or ratio < 1.0 / hrr_ratio_limit:
                valid = False
                reason = 'hrr_ratio'
        elif abs(pert_hrr) > hrr_ratio_limit:
            valid = False
            reason = 'hrr_from_near_zero'

    return valid, pair if valid else None, {
        'base_hrr': base_hrr,
        'pert_hrr': pert_hrr,
        'reason': reason,
    }



def main() -> None:
    args = parse_args()
    rng = np.random.default_rng(args.seed)
    gas = ct.Solution(args.mech)
    flame = solve_free_flame(gas, args)
    canonical = flame_states(flame)
    interpolated = interpolate_by_temperature(canonical, args.interp_temp_step)
    species_names = gas.species_names
    inert_idx = inert_index(species_names)

    temp_max_allowed = float(canonical[:, 0].max()) + args.max_extra_temp
    p_min, p_max = float(interpolated[:, 1].min()), float(interpolated[:, 1].max())

    pairs = []
    reject_reasons: dict[str, int] = {}
    attempts = 0
    for state in interpolated:
        for _ in range(args.perturb_copies):
            kept = False
            for _attempt in range(args.max_attempts):
                attempts += 1
                perturbed = perturb_state(
                    state,
                    rng=rng,
                    t_min=args.min_temp,
                    t_max=temp_max_allowed,
                    p_min=p_min,
                    p_max=p_max,
                    alpha_t=args.alpha_t,
                    alpha_p_frac=args.alpha_p_frac,
                    alpha_y=args.alpha_y,
                    inert_idx=inert_idx,
                )
                valid, pair, info = maybe_keep_pair(
                    gas,
                    original_state=state,
                    perturbed_state=perturbed,
                    dt=args.dt,
                    hrr_ratio_limit=args.hrr_ratio_limit,
                )
                if valid:
                    pairs.append(pair)
                    kept = True
                    break
                reject_reasons[info['reason']] = reject_reasons.get(info['reason'], 0) + 1
            if not kept:
                reject_reasons['max_attempts_exhausted'] = reject_reasons.get('max_attempts_exhausted', 0) + 1

    dataset = np.asarray(pairs, dtype=np.float64)
    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(out_path, dataset)

    metadata = {
        'mech': str(Path(args.mech).resolve()),
        'output': str(out_path),
        'phi': args.phi,
        'pressure': args.pressure,
        'tin': args.tin,
        'width': args.width,
        'fuel': args.fuel,
        'oxidizer': args.oxidizer,
        'dt': args.dt,
        'transport': args.transport,
        'interp_temp_step': args.interp_temp_step,
        'perturb_copies': args.perturb_copies,
        'alpha_t': args.alpha_t,
        'alpha_p_frac': args.alpha_p_frac,
        'alpha_y': args.alpha_y,
        'hrr_ratio_limit': args.hrr_ratio_limit,
        'max_attempts': args.max_attempts,
        'seed': args.seed,
        'n_species': gas.n_species,
        'species_names': species_names,
        'inert_species': species_names[inert_idx],
        'canonical_states': int(len(canonical)),
        'interpolated_states': int(len(interpolated)),
        'dataset_shape': list(dataset.shape),
        'label_attempts': attempts,
        'reject_reasons': reject_reasons,
        'state_layout': ['T', 'P', *species_names, 'T_next', 'P_next', *[f'{s}_next' for s in species_names]],
        'note': 'Prototype C2H4 canonical-flame dataset with interpolation-balanced sampling, perturbation augmentation, and one-step Cantera labeling.',
    }

    metadata_out = Path(args.metadata_out).resolve() if args.metadata_out else out_path.with_suffix('.json')
    metadata_out.write_text(json.dumps(metadata, indent=2), encoding='utf-8')

    print(json.dumps(metadata, indent=2))


if __name__ == '__main__':
    main()
