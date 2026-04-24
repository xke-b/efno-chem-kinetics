#!/usr/bin/env python3
"""Plot the H2 legacy-vs-corrected decode ablation for manuscript use."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ORDER = [
    ('teacherforced_rollout0p1_legacy', 'teacherforced_rollout0p1_bctdecode', 'teacher-forced'),
    ('self_rollout0p1_legacy', 'self_rollout0p1_bctdecode', 'self-rollout'),
    ('self_rollout0p1_predicted_main_bct_legacy', 'self_rollout0p1_predicted_main_bct_bctdecode', 'self + pred-main BCT'),
]


METRICS = [
    ('rollout_species_mae_h1000', 'Rollout species MAE @ h=1000'),
    ('rollout_temperature_mae_h1000', 'Rollout temperature MAE @ h=1000'),
    ('rollout_element_mass_mae_h1000', 'Rollout element-mass MAE @ h=1000'),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', required=True)
    parser.add_argument('--out', required=True)
    return parser.parse_args()



def main() -> None:
    args = parse_args()
    payload = json.loads(Path(args.summary).read_text())
    ref = payload['reference_cases']
    corr = payload['cases']

    labels = [label for _, _, label in ORDER]
    x = np.arange(len(labels))
    width = 0.36
    legacy_color = '#d95f02'
    corrected_color = '#1b9e77'

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.2), constrained_layout=True)

    for ax, (metric_key, title) in zip(axes, METRICS):
        legacy_vals = [ref[legacy]['aggregate'][metric_key]['mean'] for legacy, _, _ in ORDER]
        corrected_vals = [corr[new]['aggregate'][metric_key]['mean'] for _, new, _ in ORDER]
        ax.bar(x - width / 2, legacy_vals, width=width, color=legacy_color, label='legacy decode')
        ax.bar(x + width / 2, corrected_vals, width=width, color=corrected_color, label='corrected BCT-state decode')
        ax.set_xticks(x, labels, rotation=18, ha='right')
        ax.set_yscale('log')
        ax.set_title(title)
        ax.grid(axis='y', linestyle=':', alpha=0.4)

    axes[0].set_ylabel('error (log scale)')
    axes[0].legend(frameon=False, loc='upper left')
    fig.suptitle('H$_2$ corrected-decode ablation: rollout metrics improve sharply after fixing the state-space update rule')

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=180, bbox_inches='tight')
    print(json.dumps({'out': str(out_path.resolve())}, indent=2))


if __name__ == '__main__':
    main()
