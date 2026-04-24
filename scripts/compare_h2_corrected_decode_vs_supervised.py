#!/usr/bin/env python3
"""Compare corrected-decode EFNO rollout branches against seeded supervised baseline summaries."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path('/root/workspace')
SUPERVISED = ROOT / 'artifacts' / 'experiments' / 'h2_temp_species_seeded_replicates' / 'summary.json'
CORRECTED = ROOT / 'artifacts' / 'experiments' / 'h2_efno_bct_state_decode_ablation' / 'summary.json'
OUT = ROOT / 'artifacts' / 'experiments' / 'h2_corrected_decode_vs_supervised_comparison' / 'summary.json'
OUT.parent.mkdir(parents=True, exist_ok=True)

KEYS = [
    'one_step_species_mae',
    'one_step_temperature_mae',
    'one_step_element_mass_mae',
    'rollout_species_mae_h1000',
    'rollout_temperature_mae_h1000',
    'rollout_element_mass_mae_h1000',
]


def agg(case: dict) -> dict:
    return {k: case['aggregate'][k]['mean'] for k in KEYS}


def ratio(a: float, b: float) -> float | None:
    if b == 0:
        return None
    return a / b


def main() -> None:
    supervised = json.loads(SUPERVISED.read_text())['cases']['supervised_deltaT_25ep']
    corrected = json.loads(CORRECTED.read_text())['cases']

    supervised_agg = agg(supervised)
    comparisons = {}
    for name in ['teacherforced_rollout0p1_bctdecode', 'self_rollout0p1_bctdecode', 'self_rollout0p1_predicted_main_bct_bctdecode']:
        case_agg = agg(corrected[name])
        comparisons[name] = {
            'metrics': case_agg,
            'relative_to_supervised': {
                k: {
                    'difference': case_agg[k] - supervised_agg[k],
                    'ratio': ratio(case_agg[k], supervised_agg[k]),
                }
                for k in KEYS
            },
        }

    summary = {
        'supervised_reference': supervised_agg,
        'corrected_decode_cases': comparisons,
        'ranking_by_rollout_species_mae_h1000': sorted(
            ({'name': name, **payload['metrics']} for name, payload in comparisons.items()),
            key=lambda x: x['rollout_species_mae_h1000'],
        ),
    }
    OUT.write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
