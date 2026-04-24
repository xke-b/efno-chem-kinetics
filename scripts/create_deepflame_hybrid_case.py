#!/usr/bin/env python3
"""Create a guarded DeepFlame smoke case copy from a base case.

Current supported mode:
- riskguard_ft650_logistic_v1
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

BASE_CONSTANTS_BLOCK = '''HP_DELTA_T_GUARD = 500.0
HP_MIN_T_GUARD = 300.0
fallback_gas = ct.Solution(mechanismName)
'''

RISK_GUARD_CONSTANTS_TEMPLATE = '''HP_DELTA_T_GUARD = 500.0
HP_MIN_T_GUARD = 300.0
HP_RISK_THRESHOLD = {risk_threshold}
H2O_SPECIES_INDEX = {h2o_index}
O2_SPECIES_INDEX = {o2_index}
OH_SPECIES_INDEX = {oh_index}
HP_RISK_FEATURE_MEAN = np.array({feature_mean}, dtype=np.float64)
HP_RISK_FEATURE_STD = np.array({feature_std}, dtype=np.float64)
HP_RISK_WEIGHTS = np.array({weights}, dtype=np.float64)
HP_RISK_BIAS = {bias}
fallback_gas = ct.Solution(mechanismName)


def _hp_risk_score(current_row):
    features = np.array([
        float(current_row[0]),
        float(current_row[1]),
        float(current_row[2 + O2_SPECIES_INDEX]),
        float(current_row[2 + H2O_SPECIES_INDEX]),
        float(current_row[2 + OH_SPECIES_INDEX]),
    ], dtype=np.float64)
    features_norm = (features - HP_RISK_FEATURE_MEAN) / HP_RISK_FEATURE_STD
    logit = float(np.dot(features_norm, HP_RISK_WEIGHTS) + HP_RISK_BIAS)
    return 1.0 / (1.0 + np.exp(-np.clip(logit, -50.0, 50.0)))
'''

BASE_LOOP_BLOCK = '''    active_indices = np.flatnonzero(mask)
    fallback_counter = 0
    hp_failure_counter = 0
    guard_counter = 0

    for i, current_row in enumerate(vec0_input):
        try:
            with torch.no_grad():
'''

RISK_LOOP_BLOCK = '''    active_indices = np.flatnonzero(mask)
    fallback_counter = 0
    hp_failure_counter = 0
    guard_counter = 0
    risk_guard_counter = 0

    for i, current_row in enumerate(vec0_input):
        try:
            risk_score = _hp_risk_score(current_row)
            if risk_score >= HP_RISK_THRESHOLD:
                risk_guard_counter += 1
                guard_counter += 1
                raise RuntimeError('risk_guard_triggered')

            with torch.no_grad():
'''

BASE_EXCEPT_BLOCK = '''        except Exception as exc:
            if str(exc) != 'hybrid_guard_triggered':
                hp_failure_counter += 1
            next_y_fallback = _cvode_species_fallback(current_row)
            result[active_indices[i], :] = (next_y_fallback - current_row[2:-1]) * current_row[-1] / delta_t
            fallback_counter += 1

    print(f'hybrid fallback cells: {fallback_counter} (hp_failures={hp_failure_counter}, guard_only={guard_counter})')
'''

RISK_EXCEPT_BLOCK = '''        except Exception as exc:
            if str(exc) not in ('hybrid_guard_triggered', 'risk_guard_triggered'):
                hp_failure_counter += 1
            next_y_fallback = _cvode_species_fallback(current_row)
            result[active_indices[i], :] = (next_y_fallback - current_row[2:-1]) * current_row[-1] / delta_t
            fallback_counter += 1

    print(f'hybrid fallback cells: {fallback_counter} (hp_failures={hp_failure_counter}, guard_only={guard_counter}, state_guard={risk_guard_counter})')
'''


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument('--src-case', required=True)
    p.add_argument('--dst-case', required=True)
    p.add_argument('--frozen-temperature', type=float, default=650.0)
    p.add_argument('--risk-threshold', type=float, default=None)
    p.add_argument('--risk-config', default='/root/workspace/artifacts/models/deepflame_h2_ft650_logistic_hp_risk_v1.json')
    p.add_argument('--overwrite', action='store_true')
    return p.parse_args()


def set_frozen_temperature(case_dir: Path, frozen_temperature: float) -> None:
    path = case_dir / 'constant' / 'CanteraTorchProperties'
    text = path.read_text()
    import re

    text_new, n = re.subn(
        r'(frozenTemperature\s+)([0-9.eE+-]+)(;)',
        lambda m: f"{m.group(1)}{frozen_temperature:g}{m.group(3)}",
        text,
    )
    if n != 1:
        raise RuntimeError(f'Expected exactly one frozenTemperature in {path}')
    path.write_text(text_new)


def load_risk_config(path: str | Path) -> dict:
    return json.loads(Path(path).read_text())


def render_risk_guard_constants(risk_config: dict, risk_threshold: float) -> str:
    species_indices = risk_config['species_indices']
    return RISK_GUARD_CONSTANTS_TEMPLATE.format(
        risk_threshold=risk_threshold,
        h2o_index=species_indices['H2O'],
        o2_index=species_indices['O2'],
        oh_index=species_indices['OH'],
        feature_mean=repr(risk_config['feature_mean']),
        feature_std=repr(risk_config['feature_std']),
        weights=repr(risk_config['weights']),
        bias=repr(risk_config['bias']),
    )


def patch_inference(case_dir: Path, risk_config: dict, risk_threshold: float) -> None:
    path = case_dir / 'inference.py'
    text = path.read_text()
    text = text.replace(BASE_CONSTANTS_BLOCK, render_risk_guard_constants(risk_config, risk_threshold))
    text = text.replace(BASE_LOOP_BLOCK, RISK_LOOP_BLOCK)
    text = text.replace(BASE_EXCEPT_BLOCK, RISK_EXCEPT_BLOCK)
    path.write_text(text)


def main() -> None:
    args = parse_args()
    src = Path(args.src_case)
    dst = Path(args.dst_case)
    risk_config = load_risk_config(args.risk_config)
    risk_threshold = args.risk_threshold
    if risk_threshold is None:
        risk_threshold = float(risk_config['default_risk_threshold'])
    if dst.exists():
        if not args.overwrite:
            raise SystemExit(f'{dst} exists; pass --overwrite to replace it')
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    set_frozen_temperature(dst, args.frozen_temperature)
    patch_inference(dst, risk_config, risk_threshold)
    print(f'Created {dst}')


if __name__ == '__main__':
    main()
