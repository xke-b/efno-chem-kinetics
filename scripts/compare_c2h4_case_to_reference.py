#!/usr/bin/env python3
"""Compare a DeepFlame C2H4 case against a matched-mesh reference case."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from compare_deepflame_c2h4_best_vs_stock import (
    KEY_SPECIES,
    TEMP_BINS,
    build_summary,
    read_case_time_fields,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument('--reference-case', required=True)
    p.add_argument('--model-case', required=True)
    p.add_argument('--time', required=True)
    p.add_argument('--frozen-temperature', type=float, default=510.0)
    p.add_argument('--reference-label', default='reference')
    p.add_argument('--model-label', default='model')
    p.add_argument('--out-json', required=True)
    p.add_argument('--out-fig', default=None)
    return p.parse_args()



def plot(summary: dict, out_fig: Path, *, reference_label: str, model_label: str, time_name: str) -> None:
    bins = summary['temperature_bin_metrics']
    labels = list(bins.keys())
    ref_q = [bins[k].get('stock_qdot_mean', np.nan) for k in labels]
    model_q = [bins[k].get('model_qdot_mean', np.nan) for k in labels]
    sign_mismatch = [bins[k].get('sign_mismatch_fraction_strong_qdot', np.nan) for k in labels]

    ranked = summary['ranked_species_distortions'][:6]
    species = [r['species'] for r in ranked]
    ratios = [r['model_to_stock_mean_ratio'] for r in ranked]

    fig, axes = plt.subplots(1, 3, figsize=(13, 4), constrained_layout=True)
    x = np.arange(len(labels))
    width = 0.38
    axes[0].bar(x - width/2, ref_q, width=width, label=reference_label)
    axes[0].bar(x + width/2, model_q, width=width, label=model_label)
    axes[0].set_xticks(x, labels, rotation=25, ha='right')
    axes[0].set_title('Mean Qdot by reference-temperature bin')
    axes[0].legend(frameon=False)

    axes[1].bar(x, sign_mismatch)
    axes[1].set_xticks(x, labels, rotation=25, ha='right')
    axes[1].set_ylim(0, 1)
    axes[1].set_title('Qdot sign mismatch fraction')

    axes[2].bar(np.arange(len(species)), ratios)
    axes[2].axhline(1.0, color='k', linestyle='--', linewidth=1)
    axes[2].set_xticks(np.arange(len(species)), species, rotation=25, ha='right')
    axes[2].set_title(f'Top species mean-ratio distortions\n({model_label}/{reference_label})')
    axes[2].set_ylabel('mean ratio')

    fig.suptitle(f'C2H4 case comparison at {time_name}: {model_label} vs {reference_label}')
    out_fig.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_fig, dpi=180, bbox_inches='tight')



def main() -> None:
    args = parse_args()
    reference = read_case_time_fields(Path(args.reference_case), args.time)
    model = read_case_time_fields(Path(args.model_case), args.time)
    summary = build_summary(reference, model, args.frozen_temperature)
    summary.update({
        'reference_case': str(Path(args.reference_case).resolve()),
        'model_case': str(Path(args.model_case).resolve()),
        'reference_label': args.reference_label,
        'model_label': args.model_label,
        'time': args.time,
        'frozen_temperature': args.frozen_temperature,
        'note': 'Matched-mesh C2H4 case comparison against a chosen reference case.',
    })
    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(summary, indent=2), encoding='utf-8')
    if args.out_fig:
        plot(summary, Path(args.out_fig), reference_label=args.reference_label, model_label=args.model_label, time_name=args.time)
    print(json.dumps({'out_json': str(out_json.resolve()), 'out_fig': str(Path(args.out_fig).resolve()) if args.out_fig else None}, indent=2))


if __name__ == '__main__':
    main()
