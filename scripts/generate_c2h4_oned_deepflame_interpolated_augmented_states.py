#!/usr/bin/env python3
"""Build Xiao-style interpolated/perturbed current states from a DeepFlame oneD HDF5 sample."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cantera as ct
import h5py
import numpy as np


INERT_CANDIDATES = {'N2', 'AR', 'HE'}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument('--source-h5', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--metadata-out', default=None)
    p.add_argument('--interp-temp-step', type=float, default=10.0)
    p.add_argument('--target-size', type=int, default=20000)
    p.add_argument('--perturb-copies', type=int, default=1)
    p.add_argument('--alpha-t', type=float, default=50.0)
    p.add_argument('--alpha-p-frac', type=float, default=0.05)
    p.add_argument('--alpha-y', type=float, default=0.10)
    p.add_argument('--min-temp', type=float, default=290.0)
    p.add_argument('--max-extra-temp', type=float, default=100.0)
    p.add_argument('--hrr-ratio-limit', type=float, default=50.0)
    p.add_argument('--max-attempts', type=int, default=20)
    p.add_argument('--seed', type=int, default=0)
    return p.parse_args()



def inert_index(species_names: list[str]) -> int:
    for i, name in enumerate(species_names):
        if name.upper() in INERT_CANDIDATES:
            return i
    return len(species_names) - 1



def read_h5_states(h5_path: Path) -> tuple[list[str], list[tuple[str, np.ndarray]]]:
    with h5py.File(h5_path, 'r') as h5:
        species_names = [str(x) for x in h5.attrs['species_names']]
        entries = [(name, h5['scalar_fields'][name][...]) for name in sorted(h5['scalar_fields'].keys(), key=float)]
    return species_names, entries



def interpolate_snapshot_by_temperature(states: np.ndarray, temp_step: float) -> np.ndarray:
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
    return np.unique(np.round(out, decimals=12), axis=0)



def heat_release_rate(gas: ct.Solution, state: np.ndarray) -> float:
    gas.TPY = float(state[0]), float(state[1]), np.clip(state[2:], 0.0, 1.0)
    return float(gas.heat_release_rate)



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

    reactive = np.clip(out[2:].copy(), 0.0, 1.0)
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



def keep_state(
    gas: ct.Solution,
    original_state: np.ndarray,
    candidate_state: np.ndarray,
    hrr_ratio_limit: float,
    n2_min: float,
    n2_max: float,
    inert_idx: int,
) -> tuple[bool, str]:
    if not np.isfinite(candidate_state).all():
        return False, 'nonfinite_state'
    next_y = candidate_state[2:]
    if np.any(next_y < -1e-10) or np.any(next_y > 1 + 1e-10):
        return False, 'species_bounds'
    if abs(float(np.sum(next_y)) - 1.0) > 1e-4:
        return False, 'species_sum'
    if not (n2_min <= candidate_state[2 + inert_idx] <= n2_max):
        return False, 'inert_window'

    base_hrr = heat_release_rate(gas, original_state)
    pert_hrr = heat_release_rate(gas, candidate_state)
    if abs(base_hrr) > 1e-12:
        ratio = abs(pert_hrr) / abs(base_hrr)
        if ratio > hrr_ratio_limit or ratio < 1.0 / hrr_ratio_limit:
            return False, 'hrr_ratio'
    elif abs(pert_hrr) > hrr_ratio_limit:
        return False, 'hrr_from_near_zero'
    return True, 'kept'



def main() -> None:
    args = parse_args()
    rng = np.random.default_rng(args.seed)

    species_names, snapshots = read_h5_states(Path(args.source_h5).resolve())
    if species_names[:2] != ['T', 'p']:
        raise ValueError(f'Unexpected HDF5 state layout prefix: {species_names[:2]}')
    chem_species = species_names[2:]
    inert_idx = inert_index(chem_species)

    canonical_rows = []
    for _, snapshot in snapshots:
        canonical_rows.append(snapshot)
    canonical = np.vstack(canonical_rows)

    interpolated_rows = []
    for _, snapshot in snapshots:
        interpolated_rows.append(interpolate_snapshot_by_temperature(snapshot, args.interp_temp_step))
    interpolated = np.vstack(interpolated_rows)
    interpolated = np.unique(np.round(interpolated, decimals=12), axis=0)

    with h5py.File(Path(args.source_h5).resolve(), 'r') as h5:
        mech = str(h5.attrs['mechanism'])
    gas = ct.Solution(mech)

    temp_max_allowed = float(canonical[:, 0].max()) + args.max_extra_temp
    p_min, p_max = float(interpolated[:, 1].min()), float(interpolated[:, 1].max())
    n2_vals = interpolated[:, 2 + inert_idx]
    n2_span = float(n2_vals.max() - n2_vals.min())
    n2_min = float(n2_vals.min() - 0.05 * n2_span)
    n2_max = float(n2_vals.max() + 0.05 * n2_span)

    accepted = []
    reject_reasons: dict[str, int] = {}
    attempts = 0
    base_states = interpolated.copy()
    rng.shuffle(base_states)

    while len(accepted) < args.target_size:
        any_kept = False
        for state in base_states:
            for _ in range(args.perturb_copies):
                kept = False
                for _attempt in range(args.max_attempts):
                    attempts += 1
                    candidate = perturb_state(
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
                    valid, reason = keep_state(
                        gas,
                        original_state=state,
                        candidate_state=candidate,
                        hrr_ratio_limit=args.hrr_ratio_limit,
                        n2_min=n2_min,
                        n2_max=n2_max,
                        inert_idx=inert_idx,
                    )
                    if valid:
                        accepted.append(candidate)
                        any_kept = True
                        kept = True
                        break
                    reject_reasons[reason] = reject_reasons.get(reason, 0) + 1
                if len(accepted) >= args.target_size:
                    break
                if not kept:
                    reject_reasons['max_attempts_exhausted'] = reject_reasons.get('max_attempts_exhausted', 0) + 1
            if len(accepted) >= args.target_size:
                break
        if not any_kept:
            break

    dataset = np.asarray(accepted[: args.target_size], dtype=np.float64)
    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(out_path, dataset)

    metadata = {
        'source_h5': str(Path(args.source_h5).resolve()),
        'mechanism': mech,
        'output': str(out_path),
        'interp_temp_step': args.interp_temp_step,
        'target_size': args.target_size,
        'perturb_copies': args.perturb_copies,
        'alpha_t': args.alpha_t,
        'alpha_p_frac': args.alpha_p_frac,
        'alpha_y': args.alpha_y,
        'min_temp': args.min_temp,
        'max_extra_temp': args.max_extra_temp,
        'hrr_ratio_limit': args.hrr_ratio_limit,
        'max_attempts': args.max_attempts,
        'seed': args.seed,
        'n_species': len(chem_species),
        'species_names': chem_species,
        'inert_species': chem_species[inert_idx],
        'canonical_states': int(len(canonical)),
        'interpolated_states': int(len(interpolated)),
        'dataset_shape': list(dataset.shape),
        'label_attempts': attempts,
        'reject_reasons': reject_reasons,
        'state_layout': ['T', 'P', *chem_species],
        'note': 'DeepFlame oneD C2H4 current-state dataset with Xiao-style temperature interpolation and constrained perturbation, before chemistry labeling.',
    }
    metadata_out = Path(args.metadata_out).resolve() if args.metadata_out else out_path.with_suffix('.json')
    metadata_out.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print(json.dumps(metadata, indent=2))


if __name__ == '__main__':
    main()
