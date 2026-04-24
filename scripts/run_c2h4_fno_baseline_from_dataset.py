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
    return {'model_path': str(path), 'export_metadata': payload.get('export_metadata', {})}



def main() -> None:
    args = parse_args()
    dataset = Path(args.dataset)
    metadata = Path(args.metadata)
    mech = Path(args.mech)
    tag = args.tag

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
        'width': 32,
        'modes': 8,
        'n_layers': 4,
        'activation': 'gelu',
    }}),
    optimizer=OptimizerConfig(name='adam', lr={args.lr}),
    trainer=TrainerConfig(
        name='supervised_physics',
        max_epochs={args.epochs},
        lr_decay_epoch=3,
        lr_decay_factor=0.5,
        batch_size={args.batch_size},
        params={{'target_mode': 'species_only'}},
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
        'export': export_info,
        'note': args.note,
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
