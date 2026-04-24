#!/usr/bin/env python3
"""Analyze geometric consequences of legacy vs corrected species decode modes."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch

from dfode_kit.models.mlp import build_mlp
from dfode_kit.training.config import ModelConfig
from dfode_kit.training.efno_style import BCT_INVERSE_FLOOR, BCT_LAMBDA
from dfode_kit.training.train import _prepare_training_tensors
from dfode_kit.utils import inverse_BCT_torch

ROOT = Path('/root/workspace')
DATASET = ROOT / 'data' / 'h2_autoignition_longprobe_train.npy'
OUT = ROOT / 'artifacts' / 'experiments' / 'h2_efno_bct_state_decode_ablation' / 'decode_geometry_seed0.json'
CHECKPOINTS = {
    'self_rollout0p1_legacy_seed0': ROOT / 'data' / 'h2_holdout_mlp_self_rollout0p1_seed0.pt',
    'self_rollout0p1_bctdecode_seed0': ROOT / 'data' / 'h2_holdout_mlp_self_rollout0p1_bctdecode_seed0.pt',
}


def decode_stats(path: Path) -> dict:
    ckpt = torch.load(path, map_location='cpu')
    train_cfg = ckpt['training_config']
    decode_mode = train_cfg['trainer']['params'].get('species_decode_mode', 'legacy_mass_fraction_addition')
    data = np.load(DATASET)
    tensors = _prepare_training_tensors(data, n_species=7, device=torch.device('cpu'), target_mode='temperature_species')
    model = build_mlp(
        model_config=ModelConfig(name='mlp', params=train_cfg['model']['params']),
        n_species=7,
        device=torch.device('cpu'),
    )
    model.load_state_dict(ckpt['net'])
    model.eval()

    with torch.no_grad():
        feats = tensors['features']
        preds = model(feats)
        current_bct_full = feats[:, 2:] * tensors['features_std'][2:] + tensors['features_mean'][2:]
        base_y_full = inverse_BCT_torch(current_bct_full, lam=BCT_LAMBDA)
        base_y_main = base_y_full[:, :-1]
        base_bct_main = current_bct_full[:, :-1]
        pred_delta_bct = preds[:, 1:] * tensors['labels_std'][1:] + tensors['labels_mean'][1:]
        if decode_mode == 'legacy_mass_fraction_addition':
            pred_bct_state = torch.clamp(base_y_main + pred_delta_bct, min=BCT_INVERSE_FLOOR)
        elif decode_mode == 'bct_state_addition':
            pred_bct_state = torch.clamp(base_bct_main + pred_delta_bct, min=BCT_INVERSE_FLOOR)
        else:
            raise ValueError(decode_mode)
        y_pred_main = inverse_BCT_torch(pred_bct_state, lam=BCT_LAMBDA)
        y_pred_last = torch.clamp(1.0 - y_pred_main.sum(dim=1, keepdim=True), min=0.0)
        y_pred_pre_norm = torch.cat((y_pred_main, y_pred_last), dim=1)
        pre_norm_sum = y_pred_pre_norm.sum(dim=1)

    return {
        'species_decode_mode': decode_mode,
        'num_samples': int(feats.shape[0]),
        'pre_norm_sum_mean': float(pre_norm_sum.mean().item()),
        'pre_norm_sum_min': float(pre_norm_sum.min().item()),
        'pre_norm_sum_max': float(pre_norm_sum.max().item()),
        'pre_norm_sum_std': float(pre_norm_sum.std(unbiased=False).item()),
        'fraction_pre_norm_sum_gt_1p0_plus_1e-6': float((pre_norm_sum > 1.0 + 1e-6).float().mean().item()),
        'fraction_pre_norm_sum_lt_1p0_minus_1e-6': float((pre_norm_sum < 1.0 - 1e-6).float().mean().item()),
    }


def main() -> None:
    results = {name: decode_stats(path) for name, path in CHECKPOINTS.items()}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
