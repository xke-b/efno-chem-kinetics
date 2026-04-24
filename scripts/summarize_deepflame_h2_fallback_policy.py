#!/usr/bin/env python3
"""Summarize simple deployment-side fallback policies from HP-risk artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path



def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument('--inputs', nargs='+', required=True)
    p.add_argument('--out', required=True)
    return p.parse_args()



def main() -> None:
    args = parse_args()
    cases = {}
    for path_str in args.inputs:
        path = Path(path_str)
        data = json.loads(path.read_text())
        hp = data['hp_reconstruction']
        n_active = int(data['n_cells_dnn_active'])
        n_fail = int(hp['n_failures'])
        extreme_successes = hp['sample_extreme_successes']

        temp_guard_300_or_4000 = sum(
            1 for x in extreme_successes
            if x['predicted_T'] < 300.0 or x['predicted_T'] > 4000.0
        )
        delta_guard_500 = sum(1 for x in extreme_successes if abs(x['delta_T']) > 500.0)
        combined_sample_guard = sum(
            1 for x in extreme_successes
            if x['predicted_T'] < 300.0 or x['predicted_T'] > 4000.0 or abs(x['delta_T']) > 500.0
        )

        cases[path.stem] = {
            'n_active_cells': n_active,
            'n_hp_failures': n_fail,
            'hp_failure_fraction': n_fail / n_active if n_active else 0.0,
            'sample_extreme_success_count': len(extreme_successes),
            'sample_temp_guard_hits_T_lt_300_or_gt_4000': temp_guard_300_or_4000,
            'sample_delta_guard_hits_abs_dT_gt_500': delta_guard_500,
            'sample_combined_guard_hits': combined_sample_guard,
            'interpretation': (
                'A guaranteed-safe minimal fallback policy is to route all outright HP failures to CVODE. '
                'Additional temperature/delta-T guards appear justified because many nominally successful '
                'reconstructions are still extreme.'
            ),
        }

    out = {
        'policy_candidates': {
            'fallback_on_hp_failure': 'Send cells with HP reconstruction failure to CVODE.',
            'fallback_on_temperature_guard': 'Also fallback cells if predicted next T < 300 K or > 4000 K.',
            'fallback_on_deltaT_guard': 'Also fallback cells if |predicted next T - current T| > 500 K.',
        },
        'cases': cases,
        'note': (
            'This uses exact HP-failure counts from the risk analysis artifacts. The extra temperature/delta-T '
            'guard counts here are conservative samples because the current risk artifacts only store sample '
            'extreme successes, not the full successful-cell population.'
        ),
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding='utf-8')
    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    main()
