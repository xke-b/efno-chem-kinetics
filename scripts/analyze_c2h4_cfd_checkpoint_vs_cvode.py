#!/usr/bin/env python3
"""Analyze one-step C2H4 checkpoint behavior on real CFD states against CVODE.

This script extracts active thermochemical states from a DeepFlame case time,
runs one-step Cantera/CVODE chemistry integration from those states, runs a
trained DFODE-kit checkpoint on the same states, and compares predicted species
changes against the CVODE one-step reference.

It is intended for diagnosing coupled-CFD failures by locating which CFD states
produce the largest chemistry mismatch and what those states have in common.
"""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

import cantera as ct
import numpy as np
import torch

from dfode_kit.models.fno1d import FNO1d
from dfode_kit.utils import BCT, inverse_BCT, inverse_power_transform


SPECIES = [
    'H', 'H2', 'O', 'O2', 'OH', 'H2O', 'HO2', 'CO', 'CO2', 'HCO', 'CH3', 'CH4',
    'CH2O', 'T-CH2', 'S-CH2', 'C2H4', 'C2H5', 'C2H2', 'C2H3', 'CH2CHO',
    'HCCO', 'CH2CO', 'CH2OH', 'N2'
]
KEY_SPECIES = ['C2H5', 'C2H3', 'CH2CHO', 'CH2CO', 'CH2OH', 'HCCO', 'HO2', 'OH', 'CO', 'CO2']
TEMP_BINS = [510.0, 700.0, 900.0, 1200.0, 1600.0, 2600.0]
SSPI_THRESHOLD = 1e-15
BCT_LAMBDA = 0.1
BCT_INVERSE_FLOOR = -1.0 / BCT_LAMBDA + 1e-8


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument('--checkpoint', required=True)
    p.add_argument('--case-dir', required=True)
    p.add_argument('--time', required=True)
    p.add_argument('--mech', required=True)
    p.add_argument('--dt', type=float, default=1e-7)
    p.add_argument('--frozen-temperature', type=float, default=510.0)
    p.add_argument('--batch-size', type=int, default=8192)
    p.add_argument('--out-json', required=True)
    return p.parse_args()



def read_internal_scalar_field(path: Path, fallback_n_cells: int | None = None) -> np.ndarray:
    with gzip.open(path, 'rt', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('internalField') and 'List<scalar>' in stripped:
            count = int(lines[i + 1].strip())
            start = i + 3
            return np.array([float(lines[start + j].strip()) for j in range(count)], dtype=np.float64)
        if stripped.startswith('internalField') and 'uniform' in stripped:
            if fallback_n_cells is None:
                raise ValueError(f'Uniform field without fallback in {path}')
            value = float(stripped.split('uniform', 1)[1].replace(';', '').strip())
            return np.full(fallback_n_cells, value, dtype=np.float64)
    raise ValueError(f'Could not parse internalField from {path}')



def read_case_time_fields(case_dir: Path, time_name: str) -> dict[str, np.ndarray]:
    processor_dirs = sorted(p for p in case_dir.glob('processor*') if p.is_dir())
    fields = {name: [] for name in ['T', 'p', 'Qdot', 'rho', 'selectDNN', *SPECIES]}
    for proc_dir in processor_dirs:
        time_dir = proc_dir / time_name
        t = read_internal_scalar_field(time_dir / 'T.gz')
        fields['T'].append(t)
        n = len(t)
        for name in ['p', 'Qdot', 'rho', 'selectDNN', *SPECIES]:
            fields[name].append(read_internal_scalar_field(time_dir / f'{name}.gz', fallback_n_cells=n))
    return {k: np.concatenate(v) for k, v in fields.items()}



def build_model_from_checkpoint(checkpoint: dict, device: torch.device):
    cfg = checkpoint['training_config']
    params = dict(cfg['model']['params'])
    model = FNO1d(
        input_tokens=int(checkpoint['data_in_mean'].shape[0]),
        output_tokens=int(checkpoint['data_target_mean'].shape[0]),
        width=int(params.get('width', 32)),
        modes=int(params.get('modes', 8)),
        n_layers=int(params.get('n_layers', 4)),
        activation=str(params.get('activation', 'gelu')),
        attention_heads=int(params.get('attention_heads', 0)),
        attention_layers=int(params.get('attention_layers', 0)),
        attention_dropout=float(params.get('attention_dropout', 0.0)),
        attention_position=str(params.get('attention_position', 'post_spectral')),
    )
    model.load_state_dict(checkpoint['net'])
    model.eval()
    model.to(device)
    return model



def predict_next_species(checkpoint: dict, states: np.ndarray, batch_size: int, device: torch.device) -> np.ndarray:
    model = build_model_from_checkpoint(checkpoint, device)
    x_mean = torch.tensor(np.asarray(checkpoint['data_in_mean']), dtype=torch.float32, device=device)
    x_std = torch.tensor(np.asarray(checkpoint['data_in_std']), dtype=torch.float32, device=device)
    y_mean = np.asarray(checkpoint['data_target_mean'], dtype=np.float32)
    y_std = np.asarray(checkpoint['data_target_std'], dtype=np.float32)
    trainer_params = checkpoint['training_config']['trainer']['params']
    target_mode = str(trainer_params.get('target_mode', 'species_only'))
    power_lambda = float(trainer_params.get('power_lambda', 0.1))

    outputs = np.empty((states.shape[0], states.shape[1] - 2), dtype=np.float64)
    for start in range(0, len(states), batch_size):
        stop = min(start + batch_size, len(states))
        batch = states[start:stop]
        y = np.clip(batch[:, 2:], 0.0, 1.0)
        x = np.hstack((batch[:, :2], BCT(y, lam=BCT_LAMBDA))).astype(np.float32)
        x_norm = torch.tensor((x - x_mean.cpu().numpy()) / x_std.cpu().numpy(), dtype=torch.float32, device=device)
        with torch.no_grad():
            pred_norm = model(x_norm).cpu().numpy()
        raw = pred_norm * y_std + y_mean
        if target_mode == 'species_power_delta':
            main_species = y[:, :-1] + inverse_power_transform(raw, lam=power_lambda)
        else:
            base_bct = BCT(y[:, :-1], lam=BCT_LAMBDA).astype(np.float32)
            pred_bct = np.maximum(base_bct + raw, BCT_INVERSE_FLOOR)
            main_species = inverse_BCT(pred_bct, lam=BCT_LAMBDA)
        main_species = np.clip(main_species, 0.0, 1.0)
        out = y.copy()
        out[:, :-1] = main_species
        denom = np.sum(out[:, :-1], axis=1, keepdims=True)
        denom = np.clip(denom, 1e-30, None)
        out[:, :-1] = out[:, :-1] / denom * (1.0 - out[:, -1:])
        outputs[start:stop] = out
    return outputs



def _permutation(source: list[str], target: list[str]) -> np.ndarray:
    if source == target:
        return np.arange(len(source), dtype=np.int64)
    if set(source) != set(target):
        raise ValueError('Source and target species sets differ; cannot build permutation')
    source_index = {name: i for i, name in enumerate(source)}
    return np.array([source_index[name] for name in target], dtype=np.int64)



def cvode_next_species(states: np.ndarray, mech: str, dt: float) -> np.ndarray:
    gas = ct.Solution(mech)
    mech_species = list(gas.species_names)
    to_mech = _permutation(SPECIES, mech_species)
    from_mech = _permutation(mech_species, SPECIES)
    out = np.empty((states.shape[0], states.shape[1] - 2), dtype=np.float64)
    for i, row in enumerate(states):
        gas.TPY = float(row[0]), float(row[1]), np.clip(row[2:][to_mech], 0.0, 1.0)
        reactor = ct.IdealGasConstPressureReactor(gas, energy='on')
        net = ct.ReactorNet([reactor])
        net.rtol = 1e-9
        net.atol = 1e-15
        net.advance(dt)
        out[i] = gas.Y.copy()[from_mech]
    return out



def physical_metrics(pred_delta: np.ndarray, true_delta: np.ndarray) -> dict:
    err = pred_delta - true_delta
    mae = float(np.mean(np.abs(err)))
    rmse = float(np.sqrt(np.mean(err ** 2)))
    true_mean = float(np.mean(true_delta))
    ss_tot = float(np.sum((true_delta - true_mean) ** 2))
    ss_res = float(np.sum(err ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else None

    small_true = np.abs(true_delta) < SSPI_THRESHOLD
    if np.any(small_true):
        sspi = float(np.mean(np.abs(pred_delta[small_true]) < SSPI_THRESHOLD))
        small_mae = float(np.mean(np.abs(err[small_true])))
        small_rmse = float(np.sqrt(np.mean(err[small_true] ** 2)))
        small_count = int(np.sum(small_true))
    else:
        sspi = None
        small_mae = None
        small_rmse = None
        small_count = 0
    return {
        'mae_physical': mae,
        'rmse_physical': rmse,
        'r2_physical': r2,
        'num_predictions': int(true_delta.size),
        'num_states': int(true_delta.shape[0]),
        'num_small_predictions': small_count,
        'small_target_threshold': SSPI_THRESHOLD,
        'small_target_sspi': sspi,
        'small_target_mae_physical': small_mae,
        'small_target_rmse_physical': small_rmse,
    }



def summarize_worst_states(fields: dict[str, np.ndarray], active_idx: np.ndarray, score: np.ndarray, pred_delta: np.ndarray, true_delta: np.ndarray, top_k: int = 50) -> dict:
    order = np.argsort(score)[::-1]
    top = order[:top_k]
    worst_global = active_idx[top]

    def summarize_subset(indices: np.ndarray) -> dict:
        if len(indices) == 0:
            return {}
        g = active_idx[indices]
        return {
            'count': int(len(indices)),
            'T_mean': float(np.mean(fields['T'][g])),
            'T_min': float(np.min(fields['T'][g])),
            'T_max': float(np.max(fields['T'][g])),
            'p_mean': float(np.mean(fields['p'][g])),
            'Qdot_mean': float(np.mean(fields['Qdot'][g])),
            'abs_Qdot_mean': float(np.mean(np.abs(fields['Qdot'][g]))),
            'delta_true_l1_mean': float(np.mean(np.sum(np.abs(true_delta[indices]), axis=1))),
            'delta_pred_l1_mean': float(np.mean(np.sum(np.abs(pred_delta[indices]), axis=1))),
        }

    bins = {}
    active_T = fields['T'][active_idx]
    for lo, hi in zip(TEMP_BINS[:-1], TEMP_BINS[1:]):
        all_mask = (active_T >= lo) & (active_T < hi)
        worst_mask = (active_T[top] >= lo) & (active_T[top] < hi)
        all_frac = float(np.mean(all_mask)) if len(active_T) else 0.0
        worst_frac = float(np.mean(worst_mask)) if len(top) else 0.0
        bins[f'{lo:.0f}-{hi:.0f}K'] = {
            'all_fraction': all_frac,
            'worst_fraction': worst_frac,
            'overrepresentation_factor': float(worst_frac / all_frac) if all_frac > 0 else None,
        }

    top_rows = []
    for local_i, global_i in zip(top, worst_global):
        rec = {
            'global_index': int(global_i),
            'state_score_delta_rmse': float(score[local_i]),
            'T': float(fields['T'][global_i]),
            'p': float(fields['p'][global_i]),
            'Qdot': float(fields['Qdot'][global_i]),
            'selectDNN': float(fields['selectDNN'][global_i]),
            'true_delta_l1': float(np.sum(np.abs(true_delta[local_i]))),
            'pred_delta_l1': float(np.sum(np.abs(pred_delta[local_i]))),
        }
        for name in KEY_SPECIES[:6]:
            idx = SPECIES.index(name)
            rec[f'current_{name}'] = float(fields[name][global_i])
            rec[f'true_delta_{name}'] = float(true_delta[local_i, idx])
            rec[f'pred_delta_{name}'] = float(pred_delta[local_i, idx])
        top_rows.append(rec)

    return {
        'score_definition': 'per-state RMSE over full 24-species physical delta vector against CVODE',
        'top_k': top_rows,
        'top1pct_summary': summarize_subset(order[: max(1, len(order) // 100)]),
        'top5pct_summary': summarize_subset(order[: max(1, len(order) // 20)]),
        'temperature_bin_overrepresentation': bins,
    }



def main() -> None:
    args = parse_args()
    fields = read_case_time_fields(Path(args.case_dir), args.time)
    current_states = np.column_stack([fields['T'], fields['p'], *[fields[s] for s in SPECIES]])
    active_mask = fields['T'] > args.frozen_temperature
    active_idx = np.nonzero(active_mask)[0]
    active_states = current_states[active_mask]

    checkpoint = torch.load(args.checkpoint, map_location='cpu')
    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    pred_next = predict_next_species(checkpoint, active_states, args.batch_size, device)
    true_next = cvode_next_species(active_states, args.mech, args.dt)

    current_y = active_states[:, 2:]
    pred_delta = pred_next - current_y
    true_delta = true_next - current_y

    per_state_rmse = np.sqrt(np.mean((pred_delta - true_delta) ** 2, axis=1))

    key_species_metrics = {}
    for name in KEY_SPECIES:
        idx = SPECIES.index(name)
        key_species_metrics[name] = physical_metrics(pred_delta[:, idx:idx+1], true_delta[:, idx:idx+1])
        key_species_metrics[name].update({
            'current_mean': float(np.mean(current_y[:, idx])),
            'true_delta_mean': float(np.mean(true_delta[:, idx])),
            'pred_delta_mean': float(np.mean(pred_delta[:, idx])),
        })

    summary = {
        'checkpoint': str(Path(args.checkpoint).resolve()),
        'case_dir': str(Path(args.case_dir).resolve()),
        'time': args.time,
        'mech': str(Path(args.mech).resolve()),
        'dt': args.dt,
        'frozen_temperature': args.frozen_temperature,
        'n_cells_total': int(len(current_states)),
        'n_active_cells': int(len(active_states)),
        'model_target_mode': str(checkpoint['training_config']['trainer']['params'].get('target_mode', 'species_only')),
        'global_delta_metrics': physical_metrics(pred_delta, true_delta),
        'key_species_delta_metrics': key_species_metrics,
        'worst_state_analysis': summarize_worst_states(fields, active_idx, per_state_rmse, pred_delta, true_delta),
        'active_state_summary': {
            'T_mean': float(np.mean(active_states[:, 0])),
            'T_min': float(np.min(active_states[:, 0])),
            'T_max': float(np.max(active_states[:, 0])),
            'p_mean': float(np.mean(active_states[:, 1])),
            'Qdot_mean': float(np.mean(fields['Qdot'][active_mask])),
            'abs_Qdot_mean': float(np.mean(np.abs(fields['Qdot'][active_mask]))),
        },
        'note': 'One-step CFD-state checkpoint-vs-CVODE chemistry delta comparison on real DeepFlame active cells, motivated by Xiao-style metric analysis and coupled-failure diagnosis.',
    }

    out_path = Path(args.out_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps({'out_json': str(out_path.resolve())}, indent=2))


if __name__ == '__main__':
    main()
