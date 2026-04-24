#!/usr/bin/env python3
"""Select regime-targeted C2H4 rows for chemistry-proxy relabeling.

The goal is to avoid random partial relabeling by preferentially selecting states
that overlap with the diagnosed deployment pathologies:
- cooler active states, where the current best model over-drives source terms
- hotter active states that still carry meaningful intermediate chemistry support

This script writes explicit dataset row indices plus summary statistics so the
selection can be reused reproducibly by downstream relabeling and mixing steps.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

DEFAULT_INTERMEDIATE_SPECIES = [
    'C2H5',
    'C2H3',
    'CH2CHO',
    'HCCO',
    'CH2CO',
    'CH2OH',
    'HO2',
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument('--dataset', required=True)
    p.add_argument('--metadata', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--summary-out', required=True)
    p.add_argument('--count', type=int, default=5000)
    p.add_argument('--cool-min-temp', type=float, default=510.0)
    p.add_argument('--cool-max-temp', type=float, default=1600.0)
    p.add_argument('--hot-min-temp', type=float, default=1600.0)
    p.add_argument('--hot-max-temp', type=float, default=2600.0)
    p.add_argument('--cool-fraction', type=float, default=0.6)
    p.add_argument('--intermediate-species', nargs='*', default=DEFAULT_INTERMEDIATE_SPECIES)
    p.add_argument('--seed', type=int, default=0)
    return p.parse_args()



def _normalize(arr: np.ndarray) -> np.ndarray:
    lo = float(arr.min())
    hi = float(arr.max())
    if hi <= lo:
        return np.zeros_like(arr)
    return (arr - lo) / (hi - lo)



def _summary_block(dataset: np.ndarray, indices: np.ndarray, species_names: list[str], intermediate_indices: list[int]) -> dict:
    subset = dataset[indices]
    T = subset[:, 0]
    P = subset[:, 1]
    Y = subset[:, 2 : 2 + len(species_names)]
    inter = Y[:, intermediate_indices].sum(axis=1)
    return {
        'count': int(len(indices)),
        'temperature': {
            'mean': float(T.mean()),
            'min': float(T.min()),
            'max': float(T.max()),
            'p10': float(np.quantile(T, 0.1)),
            'p90': float(np.quantile(T, 0.9)),
        },
        'pressure': {
            'mean': float(P.mean()),
            'min': float(P.min()),
            'max': float(P.max()),
        },
        'intermediate_sum': {
            'mean': float(inter.mean()),
            'p50': float(np.quantile(inter, 0.5)),
            'p90': float(np.quantile(inter, 0.9)),
            'p99': float(np.quantile(inter, 0.99)),
        },
    }



def main() -> None:
    args = parse_args()
    dataset = np.load(args.dataset)
    meta = json.loads(Path(args.metadata).read_text())
    species_names = meta['species_names']
    n_species = len(species_names)
    species_to_idx = {name: i for i, name in enumerate(species_names)}
    missing = [name for name in args.intermediate_species if name not in species_to_idx]
    if missing:
        raise ValueError(f'Missing species in dataset: {missing}')
    intermediate_indices = [species_to_idx[name] for name in args.intermediate_species]

    T = dataset[:, 0]
    Y = dataset[:, 2 : 2 + n_species]
    intermediate_sum = Y[:, intermediate_indices].sum(axis=1)
    score = _normalize(np.log10(intermediate_sum + 1e-30))

    cool_mask = (T >= args.cool_min_temp) & (T < args.cool_max_temp)
    hot_mask = (T >= args.hot_min_temp) & (T <= args.hot_max_temp)

    cool_candidates = np.where(cool_mask)[0]
    hot_candidates = np.where(hot_mask)[0]
    if len(cool_candidates) == 0 or len(hot_candidates) == 0:
        raise ValueError('One of the target temperature buckets is empty; adjust temperature bounds.')

    rng = np.random.default_rng(args.seed)
    cool_target = min(int(round(args.count * args.cool_fraction)), len(cool_candidates))
    hot_target = min(args.count - cool_target, len(hot_candidates))
    if cool_target + hot_target < args.count:
        remaining = args.count - (cool_target + hot_target)
        leftovers = np.setdiff1d(np.arange(len(dataset)), np.concatenate([cool_candidates[:0], hot_candidates[:0]]))
        # fill later after ranked selection if needed
    
    def top_ranked(candidates: np.ndarray, k: int) -> np.ndarray:
        if k <= 0:
            return np.array([], dtype=int)
        cand_scores = score[candidates]
        order = np.argsort(-cand_scores, kind='stable')
        ranked = candidates[order]
        return np.sort(ranked[:k])

    cool_selected = top_ranked(cool_candidates, cool_target)
    hot_selected = top_ranked(hot_candidates, hot_target)
    selected = np.unique(np.concatenate([cool_selected, hot_selected]))

    if len(selected) < args.count:
        used = np.zeros(len(dataset), dtype=bool)
        used[selected] = True
        leftover_candidates = np.where(~used)[0]
        leftover_ranked = top_ranked(leftover_candidates, args.count - len(selected))
        selected = np.sort(np.concatenate([selected, leftover_ranked]))

    if len(selected) > args.count:
        selected = np.sort(selected[:args.count])

    random_indices = np.sort(rng.choice(len(dataset), size=min(args.count, len(dataset)), replace=False))

    selection_payload = {
        'source_dataset': str(Path(args.dataset).resolve()),
        'source_metadata': str(Path(args.metadata).resolve()),
        'count': int(len(selected)),
        'indices': selected.tolist(),
        'cool_indices_count': int(len(np.intersect1d(selected, cool_candidates))),
        'hot_indices_count': int(len(np.intersect1d(selected, hot_candidates))),
        'cool_temp_range': [args.cool_min_temp, args.cool_max_temp],
        'hot_temp_range': [args.hot_min_temp, args.hot_max_temp],
        'cool_fraction_target': args.cool_fraction,
        'intermediate_species': args.intermediate_species,
        'seed': args.seed,
        'note': 'Regime-targeted relabel candidate indices prioritizing cool-active and intermediate-rich C2H4 states.',
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(selection_payload, indent=2), encoding='utf-8')

    summary = {
        'selection': {
            'count': int(len(selected)),
            'cool_count': int(len(np.intersect1d(selected, cool_candidates))),
            'hot_count': int(len(np.intersect1d(selected, hot_candidates))),
            'cool_fraction_realized': float(len(np.intersect1d(selected, cool_candidates)) / max(len(selected), 1)),
            'hot_fraction_realized': float(len(np.intersect1d(selected, hot_candidates)) / max(len(selected), 1)),
        },
        'targeted_subset': _summary_block(dataset, selected, species_names, intermediate_indices),
        'random_subset': _summary_block(dataset, random_indices, species_names, intermediate_indices),
        'intermediate_species': args.intermediate_species,
        'source_dataset': str(Path(args.dataset).resolve()),
        'source_metadata': str(Path(args.metadata).resolve()),
    }
    summary_path = Path(args.summary_out)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps({'selection_out': str(out_path.resolve()), 'summary_out': str(summary_path.resolve())}, indent=2))


if __name__ == '__main__':
    main()
