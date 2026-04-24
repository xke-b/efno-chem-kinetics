#!/usr/bin/env python3
"""Plot H2 coupled deployment operating windows for manuscript use."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt


FT_COLORS = {
    'baseline': '#d95f02',
    'ft550': '#7570b3',
    'ft600': '#1b9e77',
    'ft650': '#66a61e',
}
FT_LABELS = {
    'baseline': 'baseline',
    'ft550': 'FT550',
    'ft600': 'FT600',
    'ft650': 'FT650',
}
RISK_COLORS = {
    'plain_ft650': '#1b9e77',
    'risk_t04': '#7570b3',
    'risk_t05': '#66a61e',
    'risk_t06': '#d95f02',
}
RISK_LABELS = {
    'plain_ft650': 'plain FT650',
    'risk_t04': 'risk@0.4',
    'risk_t05': 'risk@0.5',
    'risk_t06': 'risk@0.6',
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--frozen-summary', required=True)
    parser.add_argument('--risk-summary', required=True)
    parser.add_argument('--out', required=True)
    return parser.parse_args()



def _sorted_times(selected_times: dict[str, dict]) -> list[str]:
    return sorted(selected_times.keys(), key=float)



def main() -> None:
    args = parse_args()
    frozen = json.loads(Path(args.frozen_summary).read_text())
    risk = json.loads(Path(args.risk_summary).read_text())

    frozen_times = _sorted_times(frozen['selected_times'])
    risk_times = _sorted_times(risk['selected_times'])
    frozen_x = [float(t) * 1e6 for t in frozen_times]
    risk_x = [float(t) * 1e6 for t in risk_times]

    fig, axes = plt.subplots(2, 2, figsize=(12.5, 8), constrained_layout=True)

    for key in ['baseline', 'ft550', 'ft600', 'ft650']:
        y_learned = [frozen['selected_times'][t][key]['learned_fraction_active'] for t in frozen_times]
        y_hp = [frozen['selected_times'][t][key]['hp_failure_fraction_active'] for t in frozen_times]
        axes[0, 0].plot(frozen_x, y_learned, marker='o', label=FT_LABELS[key], color=FT_COLORS[key])
        axes[0, 1].plot(frozen_x, y_hp, marker='o', label=FT_LABELS[key], color=FT_COLORS[key])

    for key in ['plain_ft650', 'risk_t04', 'risk_t05', 'risk_t06']:
        y_learned = [risk['selected_times'][t][key]['learned_fraction_active'] for t in risk_times]
        y_hp = [risk['selected_times'][t][key]['hp_failure_fraction_active'] for t in risk_times]
        axes[1, 0].plot(risk_x, y_learned, marker='o', label=RISK_LABELS[key], color=RISK_COLORS[key])
        axes[1, 1].plot(risk_x, y_hp, marker='o', label=RISK_LABELS[key], color=RISK_COLORS[key])

    axes[0, 0].set_title('Frozen-temperature sweep: learned fraction')
    axes[0, 1].set_title('Frozen-temperature sweep: HP-failure fraction')
    axes[1, 0].set_title('FT650 guard family: learned fraction')
    axes[1, 1].set_title('FT650 guard family: HP-failure fraction')

    for ax in axes.flat:
        ax.set_xlabel('time ($\mu$s)')
        ax.set_ylabel('fraction of active cells')
        ax.grid(True, linestyle=':', alpha=0.4)
        ax.set_ylim(-0.02, 1.02)

    axes[0, 0].legend(frameon=False, ncol=2, loc='best')
    axes[1, 0].legend(frameon=False, ncol=2, loc='best')

    fig.suptitle('H$_2$ coupled operating windows: threshold choice and risk guards reshape the learned/fallback regime')

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=180, bbox_inches='tight')
    print(json.dumps({'out': str(out_path.resolve())}, indent=2))


if __name__ == '__main__':
    main()
