#!/usr/bin/env python3
"""Seeded ablation of corrected BCT-state species decoding in EFNO rollout training."""

from __future__ import annotations

import json
import statistics
import subprocess
from pathlib import Path

ROOT = Path('/root/workspace')
MECH = '/opt/src/deepflame-dev/mechanisms/H2/ES80_H2-7-16.yaml'
TRAIN_DATA = ROOT / 'data' / 'h2_autoignition_longprobe_train.npy'
TEST_DATA = ROOT / 'data' / 'h2_autoignition_longprobe_test.npy'
TEST_META = ROOT / 'data' / 'h2_autoignition_longprobe_test.json'
EXP_DIR = ROOT / 'artifacts' / 'experiments' / 'h2_efno_bct_state_decode_ablation'
EXP_DIR.mkdir(parents=True, exist_ok=True)
EPOCHS = 25
SEEDS = [0, 1, 2]

BASE = {
    'target_mode': 'temperature_species',
    'species_data_space': 'bct_delta',
    'species_decode_mode': 'bct_state_addition',
    'lambda_data': 1.0,
    'lambda_elements': 0.0,
    'lambda_mass': 0.0,
    'temperature_loss_weight': 0.1,
    'species_loss_weight': 4.0,
    'rollout_consistency_weight': 0.1,
    'rollout_feature_clip': 10.0,
    'gradient_clip_norm': 1.0,
}

CASES = {
    'teacherforced_rollout0p1_bctdecode': {
        **BASE,
        'rollout_consistency_mode': 'teacher_forced',
    },
    'self_rollout0p1_bctdecode': {
        **BASE,
        'rollout_consistency_mode': 'self',
        'rollout_species_feature_mode': 'self',
        'rollout_last_species_feature_mode': 'self',
    },
    'self_rollout0p1_predicted_main_bct_bctdecode': {
        **BASE,
        'rollout_consistency_mode': 'self',
        'rollout_species_feature_mode': 'predicted_main_bct',
        'rollout_last_species_feature_mode': 'self',
    },
}

REFERENCE_SUMMARIES = {
    'teacherforced_rollout0p1_legacy': (
        ROOT / 'artifacts' / 'experiments' / 'h2_efno_teacher_forced_rollout_ablation' / 'summary.json',
        'teacherforced_rollout0p1_tempw_0p1_speciesw_4p0',
    ),
    'self_rollout0p1_legacy': (
        ROOT / 'artifacts' / 'experiments' / 'h2_efno_rollout_consistency_ablation' / 'summary.json',
        'rollout0p1_tempw_0p1_speciesw_4p0',
    ),
    'self_rollout0p1_predicted_main_bct_legacy': (
        ROOT / 'artifacts' / 'experiments' / 'h2_efno_self_rollout_predicted_main_bct_ablation' / 'summary.json',
        'self_rollout0p1_predicted_main_bct',
    ),
}

METRIC_KEYS = [
    'one_step_species_mae',
    'one_step_temperature_mae',
    'one_step_element_mass_mae',
]
ROLLOUT_KEYS = [
    ('rollout_species_mae_by_horizon', 'rollout_species_mae_h1000'),
    ('rollout_temperature_mae_by_horizon', 'rollout_temperature_mae_h1000'),
    ('rollout_element_mass_mae_by_horizon', 'rollout_element_mass_mae_h1000'),
]


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)



def train_model(name: str, trainer_params: dict, seed: int) -> Path:
    ckpt = ROOT / 'data' / f'h2_holdout_mlp_{name}_seed{seed}.pt'
    train_py = f'''
from dfode_kit.training.train import train
from dfode_kit.training.config import TrainingConfig, ModelConfig, OptimizerConfig, TrainerConfig
cfg = TrainingConfig(
    model=ModelConfig(name='mlp', params={{'hidden_layers':[64,64]}}),
    optimizer=OptimizerConfig(name='adam', lr=1e-3),
    trainer=TrainerConfig(
        name='efno_style',
        max_epochs={EPOCHS},
        lr_decay_epoch=10,
        lr_decay_factor=0.5,
        batch_size=512,
        params={json.dumps(trainer_params)},
    ),
    time_step=1e-7,
    seed={seed},
)
train('{MECH}', '{TRAIN_DATA}', '{ckpt}', 1e-7, cfg)
'''
    run(['python', '-c', train_py])
    return ckpt



def evaluate_model(ckpt: Path, out_json: Path) -> dict:
    run([
        'python', str(ROOT / 'scripts' / 'evaluate_species_delta_checkpoint.py'),
        '--checkpoint', str(ckpt),
        '--dataset', str(TEST_DATA),
        '--metadata', str(TEST_META),
        '--out', str(out_json),
    ])
    return json.loads(out_json.read_text())



def summarize_case(results: list[dict]) -> dict:
    summary = {'replicates': results, 'aggregate': {}}
    for key in METRIC_KEYS:
        vals = [r[key] for r in results]
        summary['aggregate'][key] = {
            'mean': statistics.fmean(vals),
            'min': min(vals),
            'max': max(vals),
            'stdev': statistics.pstdev(vals),
        }
    for source_key, out_key in ROLLOUT_KEYS:
        vals = [r[source_key][-1] for r in results]
        summary['aggregate'][out_key] = {
            'mean': statistics.fmean(vals),
            'min': min(vals),
            'max': max(vals),
            'stdev': statistics.pstdev(vals),
        }
    return summary


def extract_reference_case(path: Path, case_name: str) -> dict:
    payload = json.loads(path.read_text())
    return payload['cases'][case_name]


def main() -> None:
    summary = {'epochs': EPOCHS, 'seeds': SEEDS, 'cases': {}, 'reference_cases': {}}
    for ref_name, (ref_path, case_name) in REFERENCE_SUMMARIES.items():
        summary['reference_cases'][ref_name] = extract_reference_case(ref_path, case_name)

    for case_name, trainer_params in CASES.items():
        case_results = []
        for seed in SEEDS:
            ckpt = train_model(case_name, trainer_params, seed)
            metrics = evaluate_model(ckpt, EXP_DIR / f'{case_name}_seed{seed}_eval.json')
            metrics['seed'] = seed
            case_results.append(metrics)
        summary['cases'][case_name] = summarize_case(case_results)

    (EXP_DIR / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
