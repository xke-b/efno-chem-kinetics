#!/usr/bin/env python3
"""Analyze how often species renormalization is actually active in self-rollout feature construction."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch

from dfode_kit.models.mlp import build_mlp
from dfode_kit.training.config import ModelConfig
from dfode_kit.training.efno_style import BCT_FEATURE_FLOOR, BCT_INVERSE_FLOOR, BCT_LAMBDA
from dfode_kit.training.train import _prepare_training_tensors
from dfode_kit.utils import BCT_torch, inverse_BCT_torch

ROOT = Path('/root/workspace')
DATASET = ROOT / 'data' / 'h2_autoignition_longprobe_train.npy'
OUT = ROOT / 'artifacts' / 'experiments' / 'h2_efno_self_rollout_predicted_full_bct_prenorm_ablation' / 'normalization_activity_seed0.json'
CHECKPOINTS = {
    'self_rollout0p1_seed0': ROOT / 'data' / 'h2_holdout_mlp_self_rollout0p1_seed0.pt',
    'predicted_main_bct_seed0': ROOT / 'data' / 'h2_holdout_mlp_self_rollout0p1_predicted_main_bct_seed0.pt',
}


def analyze_checkpoint(path: Path) -> dict:
    ckpt = torch.load(path, map_location='cpu')
    train_cfg = ckpt['training_config']
    n_species = int(ckpt['model_params']['output_dim']) if 'model_params' in ckpt else 7
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
        features_mean = tensors['features_mean']
        features_std = tensors['features_std']
        labels_mean = tensors['labels_mean']
        labels_std = tensors['labels_std']
        base_y_full = inverse_BCT_torch(
            feats[:, 2:] * features_std[2:] + features_mean[2:],
            lam=BCT_LAMBDA,
        )
        base_y_main = base_y_full[:, :-1]
        pred_delta_bct = preds[:, 1:] * labels_std[1:] + labels_mean[1:]
        pred_bct_state = torch.clamp(base_y_main.add(pred_delta_bct), min=BCT_INVERSE_FLOOR)
        y_pred_main = inverse_BCT_torch(pred_bct_state, lam=BCT_LAMBDA)
        y_pred_last = torch.clamp(1.0 - y_pred_main.sum(dim=1, keepdim=True), min=0.0)
        y_pred_pre_norm = torch.cat((y_pred_main, y_pred_last), dim=1)
        pre_norm_sum = y_pred_pre_norm.sum(dim=1)
        y_pred_norm = y_pred_pre_norm / torch.clamp(pre_norm_sum.unsqueeze(1), min=1e-12)
        full_bct_prenorm = BCT_torch(torch.clamp(y_pred_pre_norm, min=BCT_FEATURE_FLOOR), lam=BCT_LAMBDA)
        full_bct_norm = BCT_torch(torch.clamp(y_pred_norm, min=BCT_FEATURE_FLOOR), lam=BCT_LAMBDA)
        diff = torch.abs(full_bct_prenorm - full_bct_norm)

    return {
        'num_samples': int(feats.shape[0]),
        'pre_norm_sum_mean': float(pre_norm_sum.mean().item()),
        'pre_norm_sum_min': float(pre_norm_sum.min().item()),
        'pre_norm_sum_max': float(pre_norm_sum.max().item()),
        'pre_norm_sum_std': float(pre_norm_sum.std(unbiased=False).item()),
        'fraction_pre_norm_sum_gt_1p0_plus_1e-9': float((pre_norm_sum > 1.0 + 1e-9).float().mean().item()),
        'fraction_pre_norm_sum_lt_1p0_minus_1e-9': float((pre_norm_sum < 1.0 - 1e-9).float().mean().item()),
        'mean_abs_bct_diff_fullblock_prenorm_vs_norm': float(diff.mean().item()),
        'max_abs_bct_diff_fullblock_prenorm_vs_norm': float(diff.max().item()),
        'mean_abs_last_species_bct_diff_prenorm_vs_norm': float(diff[:, -1].mean().item()),
        'max_abs_last_species_bct_diff_prenorm_vs_norm': float(diff[:, -1].max().item()),
    }


def main() -> None:
    results = {name: analyze_checkpoint(path) for name, path in CHECKPOINTS.items()}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
