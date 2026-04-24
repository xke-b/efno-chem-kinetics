#!/usr/bin/env python3
"""Plot the C2H4 staged-switch timing sweep summary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt


ORDER = [
    'pure_dp100',
    'switch_4.5e-6',
    'switch_4e-6',
    'switch_3e-6',
    'gentle_full',
]
LABELS = {
    'pure_dp100': 'dp100',
    'switch_4.5e-6': 'switch@4.5e-6',
    'switch_4e-6': 'switch@4e-6',
    'switch_3e-6': 'switch@3e-6',
    'gentle_full': 'gentle from t=0',
}
COLORS = {
    'pure_dp100': '#1b9e77',
    'switch_4.5e-6': '#66a61e',
    'switch_4e-6': '#e6ab02',
    'switch_3e-6': '#d95f02',
    'gentle_full': '#7570b3',
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', required=True)
    parser.add_argument('--out', required=True)
    return parser.parse_args()



def main() -> None:
    args = parse_args()
    payload = json.loads(Path(args.summary).read_text())
    data = payload['switch_family_summary']
    stock = data['stock']

    x = range(len(ORDER))
    qdot_ratio = [data[key]['qdot_mean'] / stock['qdot_mean'] for key in ORDER]
    pmax = [data[key]['pressure_max'] for key in ORDER]
    dt_mean = [data[key]['mean_abs_delta_T'] for key in ORDER]
    labels = [LABELS[key] for key in ORDER]
    colors = [COLORS[key] for key in ORDER]

    fig, axes = plt.subplots(1, 3, figsize=(13, 4), constrained_layout=True)

    axes[0].bar(x, qdot_ratio, color=colors)
    axes[0].set_title('Mean Qdot / stock')
    axes[0].set_ylabel('ratio')
    axes[0].set_xticks(list(x), labels, rotation=30, ha='right')
    axes[0].axhline(1.0, color='black', linewidth=1, linestyle='--')

    axes[1].bar(x, pmax, color=colors)
    axes[1].set_title('Pressure max at 5e-6')
    axes[1].set_ylabel('Pa')
    axes[1].set_xticks(list(x), labels, rotation=30, ha='right')
    axes[1].axhline(stock['pressure_max'], color='black', linewidth=1, linestyle='--', label='stock')
    axes[1].legend(frameon=False)

    axes[2].bar(x, dt_mean, color=colors)
    axes[2].set_title('Mean |ΔT| from 2e-6')
    axes[2].set_ylabel('K')
    axes[2].set_xticks(list(x), labels, rotation=30, ha='right')
    axes[2].axhline(stock['mean_abs_delta_T'], color='black', linewidth=1, linestyle='--', label='stock')
    axes[2].legend(frameon=False)

    fig.suptitle('C2H4 staged-switch timing sweep')

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=180, bbox_inches='tight')
    print(json.dumps({'out': str(out_path.resolve())}, indent=2))


if __name__ == '__main__':
    main()
