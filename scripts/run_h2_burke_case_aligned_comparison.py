#!/usr/bin/env python3
"""Mechanism/dt-aligned offline comparison for the DeepFlame H2 Burke case."""

from __future__ import annotations

import json
import statistics
import subprocess
from pathlib import Path

import numpy as np

ROOT = Path('/root/workspace')
MECH = '/opt/src/deepflame-dev/examples/dfLowMachFoam/pytorch/twoD_HIT_flame/H2/Burke2012_s9r23.yaml'
FULL_DATA = ROOT / 'data' / 'h2_burke_case_aligned.npy'
FULL_META = ROOT / 'data' / 'h2_burke_case_aligned.json'
TRAIN_DATA = ROOT / 'data' / 'h2_burke_case_aligned_train.npy'
TRAIN_META = ROOT / 'data' / 'h2_burke_case_aligned_train.json'
TEST_DATA = ROOT / 'data' / 'h2_burke_case_aligned_test.npy'
TEST_META = ROOT / 'data' / 'h2_burke_case_aligned_test.json'
EXP_DIR = ROOT / 'artifacts' / 'experiments' / 'h2_burke_case_aligned_comparison'
EXP_DIR.mkdir(parents=True, exist_ok=True)
SEEDS = [0, 1, 2]
EPOCHS = 25
N_INIT = 12
STEPS = 400
DT = 1e-6

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



def ensure_dataset() -> None:
    if FULL_DATA.exists() and FULL_META.exists():
        return
    run([
        'python', str(ROOT / 'scripts' / 'generate_h2_autoignition_pairs.py'),
        '--mech', MECH,
        '--out', str(FULL_DATA),
        '--metadata-out', str(FULL_META),
        '--n-init', str(N_INIT),
        '--steps', str(STEPS),
        '--dt', str(DT),
        '--seed', '17',
    ])



def split_holdout() -> None:
    data = np.load(FULL_DATA)
    meta = json.loads(FULL_META.read_text())
    n_init = int(meta['n_init'])
    steps = int(meta['steps'])
    trajectory_ids = np.arange(n_init)
    train_ids = trajectory_ids[: int(round(0.75 * n_init))]
    test_ids = trajectory_ids[int(round(0.75 * n_init)):]

    rows = data.reshape(n_init, steps, -1)
    train = rows[train_ids].reshape(-1, data.shape[1])
    test = rows[test_ids].reshape(-1, data.shape[1])
    np.save(TRAIN_DATA, train)
    np.save(TEST_DATA, test)

    train_meta = dict(meta)
    train_meta['output'] = str(TRAIN_DATA)
    train_meta['dataset_shape'] = list(train.shape)
    train_meta['trajectory_ids'] = train_ids.tolist()
    train_meta['n_init'] = int(len(train_ids))
    train_meta['steps'] = steps
    train_meta['holdout_split'] = 'train'
    TRAIN_META.write_text(json.dumps(train_meta, indent=2), encoding='utf-8')

    test_meta = dict(meta)
    test_meta['output'] = str(TEST_DATA)
    test_meta['dataset_shape'] = list(test.shape)
    test_meta['trajectory_ids'] = test_ids.tolist()
    test_meta['n_init'] = int(len(test_ids))
    test_meta['steps'] = steps
    test_meta['holdout_split'] = 'test'
    TEST_META.write_text(json.dumps(test_meta, indent=2), encoding='utf-8')



def train_model(name: str, trainer_name: str, trainer_params: dict, seed: int) -> Path:
    ckpt = ROOT / 'data' / f'h2_burke_{name}_seed{seed}.pt'
    train_py = f'''
from dfode_kit.training.train import train
from dfode_kit.training.config import TrainingConfig, ModelConfig, OptimizerConfig, TrainerConfig
cfg = TrainingConfig(
    model=ModelConfig(name='mlp', params={{'hidden_layers':[64,64]}}),
    optimizer=OptimizerConfig(name='adam', lr=1e-3),
    trainer=TrainerConfig(
        name='{trainer_name}',
        max_epochs={EPOCHS},
        lr_decay_epoch=10,
        lr_decay_factor=0.5,
        batch_size=512,
        params={json.dumps(trainer_params)},
    ),
    time_step={DT},
    seed={seed},
)
train('{MECH}', '{TRAIN_DATA}', '{ckpt}', {DT}, cfg)
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



def main() -> None:
    ensure_dataset()
    split_holdout()

    cases = {
        'supervised_mlp': {
            'trainer_name': 'supervised_physics',
            'trainer_params': {'target_mode': 'temperature_species'},
        },
        'corrected_self_rollout_predmainbct': {
            'trainer_name': 'efno_style',
            'trainer_params': {
                'target_mode': 'temperature_species',
                'species_data_space': 'bct_delta',
                'species_decode_mode': 'bct_state_addition',
                'lambda_data': 1.0,
                'lambda_elements': 0.0,
                'lambda_mass': 0.0,
                'temperature_loss_weight': 0.1,
                'species_loss_weight': 4.0,
                'rollout_consistency_weight': 0.1,
                'rollout_consistency_mode': 'self',
                'rollout_feature_clip': 10.0,
                'gradient_clip_norm': 1.0,
                'rollout_species_feature_mode': 'predicted_main_bct',
                'rollout_last_species_feature_mode': 'self',
            },
        },
    }

    summary = {
        'dataset': {
            'full': str(FULL_DATA),
            'train': str(TRAIN_DATA),
            'test': str(TEST_DATA),
            'mechanism': MECH,
            'dt': DT,
            'n_init': N_INIT,
            'steps': STEPS,
        },
        'epochs': EPOCHS,
        'seeds': SEEDS,
        'cases': {},
    }
    for case_name, cfg in cases.items():
        results = []
        for seed in SEEDS:
            ckpt = train_model(case_name, cfg['trainer_name'], cfg['trainer_params'], seed)
            metrics = evaluate_model(ckpt, EXP_DIR / f'{case_name}_seed{seed}_eval.json')
            metrics['seed'] = seed
            results.append(metrics)
        summary['cases'][case_name] = summarize_case(results)

    ranking = []
    for case_name, payload in summary['cases'].items():
        agg = payload['aggregate']
        ranking.append({
            'name': case_name,
            'one_step_species_mae_mean': agg['one_step_species_mae']['mean'],
            'one_step_temperature_mae_mean': agg['one_step_temperature_mae']['mean'],
            'one_step_element_mass_mae_mean': agg['one_step_element_mass_mae']['mean'],
            'rollout_species_mae_h1000_mean': agg['rollout_species_mae_h1000']['mean'],
            'rollout_temperature_mae_h1000_mean': agg['rollout_temperature_mae_h1000']['mean'],
            'rollout_element_mass_mae_h1000_mean': agg['rollout_element_mass_mae_h1000']['mean'],
        })
    summary['ranking_by_rollout_species_mae_mean'] = sorted(ranking, key=lambda x: x['rollout_species_mae_h1000_mean'])
    (EXP_DIR / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
