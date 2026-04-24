#!/usr/bin/env python3
"""Gentler early-to-late curriculum test for C2H4: smaller LR and shorter late-stage fine-tune."""

from __future__ import annotations

import json
import os
import random
import subprocess
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path('/root/workspace')
DFODE_ROOT = Path('/opt/src/DFODE-kit')
MECH = ROOT / 'runs' / 'deepflame_c2h4_smoke' / 'c2h4_stock_baseline_np8_gpu_stocksrc' / 'Wu24sp.yaml'
EARLY_CKPT = ROOT / 'artifacts' / 'models' / 'c2h4_casepair_dp100_fno_smoke.pt'
LATE_DATA = ROOT / 'data' / 'c2h4_case_pairs_late_dp100.npy'
LATE_META = ROOT / 'data' / 'c2h4_case_pairs_late_dp100.json'
CKPT = ROOT / 'artifacts' / 'models' / 'c2h4_casepair_dp100_early_to_late_curriculum_gentle_fno_smoke.pt'
EXPORT_DIR = ROOT / 'artifacts' / 'models' / 'c2h4_casepair_dp100_early_to_late_curriculum_gentle_fno_smoke_deepflame_bundle'
SUMMARY = ROOT / 'artifacts' / 'experiments' / 'c2h4_casepair_dp100_early_to_late_curriculum_gentle' / 'summary.json'
DT = 1e-7
EPOCHS = 1
STAGE_LR = 1e-4
SEED = 0

SPECIES = [
    'H', 'H2', 'O', 'O2', 'OH', 'H2O', 'HO2', 'CO', 'CO2', 'HCO', 'CH3', 'CH4',
    'CH2O', 'T-CH2', 'S-CH2', 'C2H4', 'C2H5', 'C2H2', 'C2H3', 'CH2CHO',
    'HCCO', 'CH2CO', 'CH2OH', 'N2'
]


def run(cmd: list[str]) -> None:
    env = os.environ.copy()
    existing = env.get('PYTHONPATH', '')
    env['PYTHONPATH'] = f"{DFODE_ROOT}:{existing}" if existing else str(DFODE_ROOT)
    subprocess.run(cmd, check=True, env=env)



def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    if torch.backends.cudnn.is_available():
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False



def bct(x: np.ndarray) -> np.ndarray:
    return ((np.clip(x, 0.0, 1.0) ** 0.1) - 1.0) / 0.1



def build_element_mass_matrix(gas) -> np.ndarray:
    matrix = np.zeros((gas.n_species, gas.n_elements), dtype=np.float32)
    for s_idx, species in enumerate(gas.species()):
        molecular_weight = gas.molecular_weights[s_idx]
        for e_idx, _ in enumerate(gas.element_names):
            n_atoms = species.composition.get(gas.element_names[e_idx], 0.0)
            if n_atoms == 0:
                continue
            atomic_weight = gas.atomic_weights[e_idx]
            matrix[s_idx, e_idx] = n_atoms * atomic_weight / molecular_weight
    return matrix



def formation_calculate(mech_path: str) -> np.ndarray:
    import cantera as ct
    gas = ct.Solution(mech_path)
    formation = np.zeros(gas.n_species, dtype=np.float32)
    for i in range(gas.n_species):
        gas.TPX = 298.15, ct.one_atm, {gas.species_names[i]: 1.0}
        formation[i] = gas.enthalpy_mass
    return formation



def prepare_late_tensors(payload: dict, device: torch.device) -> dict:
    labeled_data = np.load(LATE_DATA)
    n_species = len(SPECIES)
    s1 = labeled_data[:, : 2 + n_species].copy()
    s2 = labeled_data[:, 2 + n_species :].copy()
    s1[:, 2:] = np.clip(s1[:, 2:], 0.0, 1.0)
    s2[:, 2:] = np.clip(s2[:, 2:], 0.0, 1.0)

    raw_features = np.hstack((s1[:, :2], bct(s1[:, 2:])))
    raw_labels = bct(s2[:, 2:-1]) - bct(s1[:, 2:-1])

    features_mean = torch.tensor(payload['data_in_mean'], dtype=torch.float32, device=device)
    features_std = torch.tensor(payload['data_in_std'], dtype=torch.float32, device=device)
    labels_mean = torch.tensor(payload['data_target_mean'], dtype=torch.float32, device=device)
    labels_std = torch.tensor(payload['data_target_std'], dtype=torch.float32, device=device)

    features = (torch.tensor(raw_features, dtype=torch.float32, device=device) - features_mean) / features_std
    labels = (torch.tensor(raw_labels, dtype=torch.float32, device=device) - labels_mean) / labels_std
    return {
        'features': features,
        'labels': labels,
        'features_mean': features_mean,
        'features_std': features_std,
        'labels_mean': labels_mean,
        'labels_std': labels_std,
        'n_rows': int(len(labeled_data)),
    }



def train_curriculum() -> dict:
    sys.path.insert(0, str(DFODE_ROOT))
    import cantera as ct
    from dfode_kit.models.registry import create_model
    from dfode_kit.training.registry import create_trainer
    from dfode_kit.training.train import _register_defaults
    from dfode_kit.training.config import ModelConfig, OptimizerConfig, TrainerConfig

    set_seed(SEED)
    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    payload = torch.load(EARLY_CKPT, map_location='cpu')
    cfg = payload['training_config']

    _register_defaults()
    model_cfg = ModelConfig(name=cfg['model']['name'], params=dict(cfg['model']['params']))
    optimizer_cfg = OptimizerConfig(name=cfg['optimizer']['name'], lr=STAGE_LR)
    trainer_cfg = TrainerConfig(
        name=cfg['trainer']['name'],
        max_epochs=EPOCHS,
        lr_decay_epoch=1,
        lr_decay_factor=1.0,
        batch_size=cfg['trainer']['batch_size'],
        params=dict(cfg['trainer']['params']),
    )

    gas = ct.Solution(str(MECH))
    model = create_model(model_cfg.name, model_config=model_cfg, n_species=gas.n_species, device=device)
    model.load_state_dict(payload['net'])

    tensors = prepare_late_tensors(payload, device)
    trainer = create_trainer(trainer_cfg.name, trainer_config=trainer_cfg, optimizer_config=optimizer_cfg)
    trainer.fit(
        model=model,
        time_step=DT,
        features=tensors['features'],
        labels=tensors['labels'],
        features_mean=tensors['features_mean'],
        features_std=tensors['features_std'],
        labels_mean=tensors['labels_mean'],
        labels_std=tensors['labels_std'],
        formation_enthalpies=torch.tensor(formation_calculate(str(MECH)), dtype=torch.float32, device=device),
        element_mass_matrix=torch.tensor(build_element_mass_matrix(gas), dtype=torch.float32, device=device),
    )

    CKPT.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            'net': model.state_dict(),
            'data_in_mean': payload['data_in_mean'],
            'data_in_std': payload['data_in_std'],
            'data_target_mean': payload['data_target_mean'],
            'data_target_std': payload['data_target_std'],
            'training_config': {
                'model': cfg['model'],
                'optimizer': {'name': cfg['optimizer']['name'], 'lr': STAGE_LR},
                'trainer': {
                    'name': trainer_cfg.name,
                    'max_epochs': trainer_cfg.max_epochs,
                    'lr_decay_epoch': trainer_cfg.lr_decay_epoch,
                    'lr_decay_factor': trainer_cfg.lr_decay_factor,
                    'batch_size': trainer_cfg.batch_size,
                    'params': dict(trainer_cfg.params),
                },
                'time_step': DT,
                'seed': SEED,
                'curriculum_init_checkpoint': str(EARLY_CKPT),
                'curriculum_stage_dataset': str(LATE_DATA),
                'curriculum_stage': 'late_dp100_gentle_finetune_with_early_normalization',
                'curriculum_stage_lr': STAGE_LR,
            },
        },
        CKPT,
    )
    return {
        'late_rows': tensors['n_rows'],
        'init_checkpoint': str(EARLY_CKPT),
        'late_dataset': str(LATE_DATA),
        'stage_lr': STAGE_LR,
        'stage_epochs': EPOCHS,
    }



def export_bundle() -> dict:
    run([
        sys.executable,
        str(ROOT / 'scripts' / 'export_dfode_fno_to_deepflame_bundle.py'),
        '--checkpoint', str(CKPT),
        '--out-dir', str(EXPORT_DIR),
        '--validate-dataset', str(LATE_DATA),
        '--max-validate-samples', '128',
    ])
    payload = torch.load(EXPORT_DIR / 'DNN_model_fno.pt', map_location='cpu')
    return {'model_path': str(EXPORT_DIR / 'DNN_model_fno.pt'), 'export_metadata': payload.get('export_metadata', {})}



def main() -> None:
    stage_info = train_curriculum()
    export_info = export_bundle()
    summary = {
        'mechanism': str(MECH),
        'init_checkpoint': str(EARLY_CKPT),
        'late_dataset': str(LATE_DATA),
        'late_metadata': str(LATE_META),
        'checkpoint': str(CKPT),
        'export_dir': str(EXPORT_DIR),
        'dt': DT,
        'stage_epochs': EPOCHS,
        'stage_lr': STAGE_LR,
        'seed': SEED,
        'stage_info': stage_info,
        'export': export_info,
        'note': 'Gentler curriculum test: start from early dp100 checkpoint, then fine-tune briefly on late dp100 data with a smaller learning rate.',
    }
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY.write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
