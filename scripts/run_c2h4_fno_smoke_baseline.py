#!/usr/bin/env python3
"""Build the first mechanism/dt-aligned C2H4 FNO smoke baseline.

This is an enabling prototype path:
- generate a small homogeneous C2H4 dataset under Wu24sp + dt=1e-7
- train a small DFODE-kit FNO checkpoint
- export it into a DeepFlame bundle with a case-local inference script

The result is not claimed to be case-ready; it is the first concrete bridge from
C2H4 runtime baseline establishment to a deployable FNO artifact.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path('/root/workspace')
DFODE_ROOT = Path('/opt/src/DFODE-kit')
MECH = ROOT / 'runs' / 'deepflame_c2h4_smoke' / 'c2h4_stock_baseline_np8_gpu_stocksrc' / 'Wu24sp.yaml'
DATA = ROOT / 'data' / 'c2h4_autoignition_smoke.npy'
META = ROOT / 'data' / 'c2h4_autoignition_smoke.json'
CKPT = ROOT / 'artifacts' / 'models' / 'c2h4_fno_smoke.pt'
EXPORT_DIR = ROOT / 'artifacts' / 'models' / 'c2h4_fno_smoke_deepflame_bundle'
SUMMARY = ROOT / 'artifacts' / 'experiments' / 'c2h4_fno_smoke_baseline' / 'summary.json'
DT = 1e-7
N_INIT = 24
STEPS = 40
EPOCHS = 8
SEED = 0



def run(cmd: list[str]) -> None:
    env = os.environ.copy()
    existing = env.get('PYTHONPATH', '')
    env['PYTHONPATH'] = f"{DFODE_ROOT}:{existing}" if existing else str(DFODE_ROOT)
    subprocess.run(cmd, check=True, env=env)



def ensure_dataset() -> None:
    if DATA.exists() and META.exists():
        return
    run([
        sys.executable,
        str(ROOT / 'scripts' / 'generate_c2h4_autoignition_pairs.py'),
        '--mech', str(MECH),
        '--out', str(DATA),
        '--metadata-out', str(META),
        '--n-init', str(N_INIT),
        '--steps', str(STEPS),
        '--dt', str(DT),
        '--seed', '17',
    ])



def train_fno() -> None:
    CKPT.parent.mkdir(parents=True, exist_ok=True)
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
    optimizer=OptimizerConfig(name='adam', lr=1e-3),
    trainer=TrainerConfig(
        name='supervised_physics',
        max_epochs={EPOCHS},
        lr_decay_epoch=4,
        lr_decay_factor=0.5,
        batch_size=256,
        params={{'target_mode': 'species_only'}},
    ),
    time_step={DT},
    seed={SEED},
)
train('{MECH}', '{DATA}', '{CKPT}', {DT}, cfg)
'''
    run([sys.executable, '-c', train_py])



def export_bundle() -> dict:
    run([
        sys.executable,
        str(ROOT / 'scripts' / 'export_dfode_fno_to_deepflame_bundle.py'),
        '--checkpoint', str(CKPT),
        '--out-dir', str(EXPORT_DIR),
        '--validate-dataset', str(DATA),
        '--max-validate-samples', '64',
    ])
    payload = torch_load_jsonish(EXPORT_DIR / 'DNN_model_fno.pt')
    return payload



def torch_load_jsonish(path: Path) -> dict:
    import sys
    import torch

    sys.path.insert(0, str(DFODE_ROOT))

    payload = torch.load(path, map_location='cpu')
    meta = payload.get('export_metadata', {})
    return {
        'model_path': str(path),
        'export_metadata': meta,
    }



def main() -> None:
    ensure_dataset()
    train_fno()
    export_info = export_bundle()

    summary = {
        'mechanism': str(MECH),
        'dataset': str(DATA),
        'metadata': str(META),
        'checkpoint': str(CKPT),
        'export_dir': str(EXPORT_DIR),
        'dt': DT,
        'n_init': N_INIT,
        'steps': STEPS,
        'epochs': EPOCHS,
        'seed': SEED,
        'export': export_info,
        'note': 'First C2H4 FNO smoke baseline and DeepFlame bundle; deployment value still unproven.',
    }
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY.write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
