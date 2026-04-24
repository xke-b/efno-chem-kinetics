#!/usr/bin/env python3
"""Train/export a C2H4 FNO baseline from a specified dataset."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path('/root/workspace')
DFODE_ROOT = Path('/opt/src/DFODE-kit')
DEFAULT_MECH = ROOT / 'runs' / 'deepflame_c2h4_smoke' / 'c2h4_stock_baseline_np8_gpu_stocksrc' / 'Wu24sp.yaml'
DT = 1e-7

MAIN_SPECIES = [
    'H', 'H2', 'O', 'O2', 'OH', 'H2O', 'HO2', 'CO', 'CO2', 'HCO', 'CH3', 'CH4',
    'CH2O', 'T-CH2', 'S-CH2', 'C2H4', 'C2H5', 'C2H2', 'C2H3', 'CH2CHO',
    'HCCO', 'CH2CO', 'CH2OH',
]


SPECIES_WEIGHT_PROFILES = {
    'c2h4_intermediates_v1': {
        'C2H5': 20.0,
        'C2H3': 20.0,
        'CH2CHO': 20.0,
        'CH2CO': 20.0,
        'CH2OH': 20.0,
        'HCCO': 20.0,
    },
    'c2h4_intermediates_radicals_v1': {
        'C2H5': 20.0,
        'C2H3': 20.0,
        'CH2CHO': 20.0,
        'CH2CO': 20.0,
        'CH2OH': 20.0,
        'HCCO': 20.0,
        'OH': 10.0,
        'HO2': 10.0,
    },
    'c2h4_intermediates_oh_v1': {
        'C2H5': 20.0,
        'C2H3': 20.0,
        'CH2CHO': 20.0,
        'CH2CO': 20.0,
        'CH2OH': 20.0,
        'HCCO': 20.0,
        'OH': 10.0,
    },
    'c2h4_intermediates_ohsoft_v1': {
        'C2H5': 20.0,
        'C2H3': 20.0,
        'CH2CHO': 20.0,
        'CH2CO': 20.0,
        'CH2OH': 20.0,
        'HCCO': 20.0,
        'OH': 3.0,
    },
}



def build_species_loss_channel_weights(profile_name: str | None) -> list[float] | None:
    if not profile_name:
        return None
    profile = SPECIES_WEIGHT_PROFILES[profile_name]
    return [float(profile.get(name, 1.0)) for name in MAIN_SPECIES]



def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument('--dataset', required=True)
    p.add_argument('--metadata', required=True)
    p.add_argument('--tag', required=True)
    p.add_argument('--epochs', type=int, default=6)
    p.add_argument('--seed', type=int, default=0)
    p.add_argument('--batch-size', type=int, default=512)
    p.add_argument('--lr', type=float, default=1e-3)
    p.add_argument('--mech', default=str(DEFAULT_MECH))
    p.add_argument('--target-mode', default='species_only', choices=['species_only', 'species_power_delta'])
    p.add_argument('--power-lambda', type=float, default=0.1)
    p.add_argument('--width', type=int, default=32)
    p.add_argument('--modes', type=int, default=8)
    p.add_argument('--n-layers', type=int, default=4)
    p.add_argument('--attention-heads', type=int, default=0)
    p.add_argument('--attention-layers', type=int, default=0)
    p.add_argument('--attention-dropout', type=float, default=0.0)
    p.add_argument('--attention-position', choices=['post_spectral', 'interleaved'], default='post_spectral')
    p.add_argument('--validation-fraction', type=float, default=0.1)
    p.add_argument('--early-stopping-patience', type=int, default=12)
    p.add_argument('--early-stopping-min-delta', type=float, default=1e-4)
    p.add_argument('--lr-scheduler', choices=['none', 'reduce_on_plateau'], default='reduce_on_plateau')
    p.add_argument('--plateau-patience', type=int, default=4)
    p.add_argument('--plateau-factor', type=float, default=0.5)
    p.add_argument('--plateau-min-delta', type=float, default=1e-5)
    p.add_argument('--min-lr', type=float, default=1e-5)
    p.add_argument('--species-weight-profile', choices=sorted(SPECIES_WEIGHT_PROFILES.keys()), default=None)
    p.add_argument('--activity-l1-weight', type=float, default=0.0)
    p.add_argument('--enthalpy-loss-weight', type=float, default=1.0)
    p.add_argument('--note', default='C2H4 FNO baseline from explicit dataset.')
    return p.parse_args()



def run(cmd: list[str]) -> None:
    env = os.environ.copy()
    existing = env.get('PYTHONPATH', '')
    env['PYTHONPATH'] = f"{DFODE_ROOT}:{existing}" if existing else str(DFODE_ROOT)
    subprocess.run(cmd, check=True, env=env)



def torch_load_jsonish(path: Path) -> dict:
    import torch
    payload = torch.load(path, map_location='cpu')
    result = {'model_path': str(path)}
    if 'export_metadata' in payload:
        result['export_metadata'] = payload.get('export_metadata', {})
    for key in ['training_history', 'best_epoch', 'best_metric', 'dataset_split', 'training_config']:
        if key in payload:
            result[key] = payload[key]
    return result



def main() -> None:
    args = parse_args()
    dataset = Path(args.dataset)
    metadata = Path(args.metadata)
    mech = Path(args.mech)
    tag = args.tag

    species_loss_channel_weights = build_species_loss_channel_weights(args.species_weight_profile)

    ckpt = ROOT / 'artifacts' / 'models' / f'{tag}.pt'
    export_dir = ROOT / 'artifacts' / 'models' / f'{tag}_deepflame_bundle'
    summary_path = ROOT / 'artifacts' / 'experiments' / f'{tag}_baseline' / 'summary.json'

    ckpt.parent.mkdir(parents=True, exist_ok=True)
    train_py = f'''
import sys
sys.path.insert(0, {str(DFODE_ROOT)!r})
from dfode_kit.training.train import train
from dfode_kit.training.config import TrainingConfig, ModelConfig, OptimizerConfig, TrainerConfig
cfg = TrainingConfig(
    model=ModelConfig(name='fno1d', params={{
        'width': {args.width},
        'modes': {args.modes},
        'n_layers': {args.n_layers},
        'activation': 'gelu',
        'attention_heads': {args.attention_heads},
        'attention_layers': {args.attention_layers},
        'attention_dropout': {args.attention_dropout},
        'attention_position': {args.attention_position!r},
    }}),
    optimizer=OptimizerConfig(name='adam', lr={args.lr}),
    trainer=TrainerConfig(
        name='supervised_physics',
        max_epochs={args.epochs},
        lr_decay_epoch=3,
        lr_decay_factor=0.5,
        batch_size={args.batch_size},
        params={{
            'target_mode': {args.target_mode!r},
            'power_lambda': {args.power_lambda},
            'species_loss_channel_weights': {species_loss_channel_weights!r},
            'validation_fraction': {args.validation_fraction},
            'early_stopping_patience': {args.early_stopping_patience},
            'early_stopping_min_delta': {args.early_stopping_min_delta},
            'lr_scheduler': {args.lr_scheduler!r},
            'plateau_patience': {args.plateau_patience},
            'plateau_factor': {args.plateau_factor},
            'plateau_min_delta': {args.plateau_min_delta},
            'min_lr': {args.min_lr},
            'activity_l1_weight': {args.activity_l1_weight},
            'enthalpy_loss_weight': {args.enthalpy_loss_weight},
            'restore_best_state': True,
        }},
    ),
    time_step={DT},
    seed={args.seed},
)
train('{mech}', '{dataset}', '{ckpt}', {DT}, cfg)
'''
    run([sys.executable, '-c', train_py])

    run([
        sys.executable,
        str(ROOT / 'scripts' / 'export_dfode_fno_to_deepflame_bundle.py'),
        '--checkpoint', str(ckpt),
        '--out-dir', str(export_dir),
        '--validate-dataset', str(dataset),
        '--max-validate-samples', '128',
    ])
    checkpoint_info = torch_load_jsonish(ckpt)
    export_info = torch_load_jsonish(export_dir / 'DNN_model_fno.pt')

    summary = {
        'mechanism': str(mech),
        'dataset': str(dataset),
        'metadata': str(metadata),
        'checkpoint': str(ckpt),
        'export_dir': str(export_dir),
        'dt': DT,
        'epochs': args.epochs,
        'seed': args.seed,
        'batch_size': args.batch_size,
        'lr': args.lr,
        'checkpoint_info': checkpoint_info,
        'export': export_info,
        'target_mode': args.target_mode,
        'power_lambda': args.power_lambda,
        'model_width': args.width,
        'model_modes': args.modes,
        'model_n_layers': args.n_layers,
        'attention_heads': args.attention_heads,
        'attention_layers': args.attention_layers,
        'attention_dropout': args.attention_dropout,
        'attention_position': args.attention_position,
        'validation_fraction': args.validation_fraction,
        'early_stopping_patience': args.early_stopping_patience,
        'early_stopping_min_delta': args.early_stopping_min_delta,
        'lr_scheduler': args.lr_scheduler,
        'plateau_patience': args.plateau_patience,
        'plateau_factor': args.plateau_factor,
        'plateau_min_delta': args.plateau_min_delta,
        'min_lr': args.min_lr,
        'species_weight_profile': args.species_weight_profile,
        'species_loss_channel_weights': species_loss_channel_weights,
        'activity_l1_weight': args.activity_l1_weight,
        'enthalpy_loss_weight': args.enthalpy_loss_weight,
        'note': args.note,
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
