#!/usr/bin/env python3
"""Export a DFODE-kit MLP checkpoint into the DeepFlame multi-network format.

DeepFlame's current PyTorch H2 inference path expects a checkpoint with
independent scalar-output networks named net0..net{n_species-2}, plus
feature/target normalization arrays for species-only BCT deltas.

DFODE-kit currently saves a single multi-output MLP under `net`. For plain MLP
architectures, each output channel is still an affine readout from a shared
hidden trunk, so we can export an equivalent DeepFlame-compatible checkpoint by
replicating the shared hidden layers and slicing the final linear layer per
species output.

For thermochemical DFODE-kit checkpoints (`temperature_species` or
`temperature_next_species`), this exporter drops the temperature head and keeps
only the species-output channels expected by DeepFlame's species-source-term
inference path.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch

from dfode_kit.models.mlp import MLP
from dfode_kit.utils import BCT, inverse_BCT


BCT_LAMBDA = 0.1
BCT_INVERSE_FLOOR = -1.0 / BCT_LAMBDA + 1e-8


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--checkpoint', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--n-species', type=int, required=True)
    parser.add_argument('--validate-dataset', default=None)
    parser.add_argument('--validate-metadata', default=None)
    parser.add_argument('--validation-out', default=None)
    parser.add_argument('--max-validate-samples', type=int, default=128)
    return parser.parse_args()


class DeepFlameScalarMLP(torch.nn.Module):
    def __init__(self, layer_info: list[int]):
        super().__init__()
        self.net = torch.nn.Sequential()
        n = len(layer_info) - 1
        for i in range(n - 1):
            self.net.add_module(f'linear_layer_{i}', torch.nn.Linear(layer_info[i], layer_info[i + 1]))
            self.net.add_module(f'gelu_layer_{i}', torch.nn.GELU())
        self.net.add_module(f'linear_layer_{n - 1}', torch.nn.Linear(layer_info[n - 1], layer_info[n]))

    def forward(self, x):
        return self.net(x)



def _build_species_only_stats(checkpoint: dict, n_species: int) -> tuple[np.ndarray, np.ndarray]:
    target_mean = np.asarray(checkpoint['data_target_mean'])
    target_std = np.asarray(checkpoint['data_target_std'])
    if target_mean.shape[0] == n_species - 1:
        return target_mean, target_std
    if target_mean.shape[0] == n_species:
        return target_mean[1:], target_std[1:]
    raise ValueError(
        f'Unsupported target stats length {target_mean.shape[0]} for n_species={n_species}'
    )



def export_checkpoint(checkpoint: dict, n_species: int) -> dict:
    cfg = checkpoint.get('training_config', {})
    model_cfg = cfg.get('model', {})
    if model_cfg.get('name', 'mlp') != 'mlp':
        raise ValueError('Only MLP checkpoints are exportable to the current DeepFlame PyTorch format.')

    hidden_layers = list(model_cfg.get('params', {}).get('hidden_layers', [400, 400, 400, 400]))
    input_dim = 2 + n_species
    output_dim = checkpoint['net']['net.linear_layer_%d.weight' % (len(hidden_layers))].shape[0]
    if output_dim not in {n_species - 1, n_species}:
        raise ValueError(f'Unexpected DFODE output_dim={output_dim} for n_species={n_species}')

    source_state = checkpoint['net']
    species_mean, species_std = _build_species_only_stats(checkpoint, n_species)
    exported = {
        'data_in_mean': np.asarray(checkpoint['data_in_mean']),
        'data_in_std': np.asarray(checkpoint['data_in_std']),
        'data_target_mean': species_mean,
        'data_target_std': species_std,
        'export_metadata': {
            'source_checkpoint': str(checkpoint.get('source_checkpoint', '')),
            'source_training_config': cfg,
            'n_species': n_species,
            'hidden_layers': hidden_layers,
            'export_type': 'dfode_mlp_to_deepflame_multinet',
            'dropped_temperature_head': bool(output_dim == n_species),
        },
    }

    final_weight = source_state[f'net.linear_layer_{len(hidden_layers)}.weight']
    final_bias = source_state[f'net.linear_layer_{len(hidden_layers)}.bias']
    species_offset = 1 if output_dim == n_species else 0

    for species_idx in range(n_species - 1):
        scalar_model = DeepFlameScalarMLP([input_dim, *hidden_layers, 1])
        scalar_state = scalar_model.state_dict()
        for layer_idx in range(len(hidden_layers)):
            scalar_state[f'net.linear_layer_{layer_idx}.weight'] = source_state[
                f'net.linear_layer_{layer_idx}.weight'
            ].clone()
            scalar_state[f'net.linear_layer_{layer_idx}.bias'] = source_state[
                f'net.linear_layer_{layer_idx}.bias'
            ].clone()
        scalar_state[f'net.linear_layer_{len(hidden_layers)}.weight'] = final_weight[
            species_idx + species_offset : species_idx + species_offset + 1
        ].clone()
        scalar_state[f'net.linear_layer_{len(hidden_layers)}.bias'] = final_bias[
            species_idx + species_offset : species_idx + species_offset + 1
        ].clone()
        exported[f'net{species_idx}'] = scalar_state

    return exported



def _predict_next_species_original_species_branch(checkpoint: dict, state: np.ndarray, n_species: int) -> np.ndarray:
    cfg = checkpoint.get('training_config', {})
    hidden_layers = list(cfg.get('model', {}).get('params', {}).get('hidden_layers', [400, 400, 400, 400]))
    output_dim = cfg.get('model', {}).get('params', {}).get('output_dim')
    if output_dim is None:
        output_dim = checkpoint['net'][f'net.linear_layer_{len(hidden_layers)}.weight'].shape[0]

    model = MLP([2 + n_species, *hidden_layers, int(output_dim)])
    model.load_state_dict(checkpoint['net'])
    model.eval()

    y = np.clip(state[2:], 0.0, 1.0)
    x = np.hstack((state[:2], BCT(y, lam=BCT_LAMBDA))).astype(np.float32)
    x_mean = np.asarray(checkpoint['data_in_mean'], dtype=np.float32)
    x_std = np.asarray(checkpoint['data_in_std'], dtype=np.float32)
    y_mean = np.asarray(checkpoint['data_target_mean'], dtype=np.float32)
    y_std = np.asarray(checkpoint['data_target_std'], dtype=np.float32)

    x_norm = torch.tensor(((x - x_mean) / x_std)[None, :], dtype=torch.float32)
    with torch.no_grad():
        pred_norm = model(x_norm).numpy()[0]
    raw = pred_norm * y_std + y_mean
    species_raw = raw[1:] if raw.shape[0] == n_species else raw

    base_bct = BCT(y[:-1], lam=BCT_LAMBDA).astype(np.float32)
    pred_bct = np.maximum(base_bct + species_raw, BCT_INVERSE_FLOOR)
    main_species = inverse_BCT(pred_bct, lam=BCT_LAMBDA)
    main_species = np.clip(main_species, 0.0, 1.0)
    last_species = max(0.0, 1.0 - float(main_species.sum()))
    out = y.copy()
    out[:-1] = main_species
    denom = np.sum(out[:-1], keepdims=True)
    if float(denom) > 0:
        out[:-1] = out[:-1] / denom * (1.0 - out[-1])
    return out



def _predict_next_species_deepflame(exported: dict, state: np.ndarray, n_species: int) -> np.ndarray:
    hidden_layers = list(exported['export_metadata']['hidden_layers'])
    x = state.copy().astype(np.float64)
    x[2:] = np.clip(x[2:], 0.0, 1.0)
    input_y = x[2:].copy()
    input_bct = x.copy()
    input_bct[2:] = BCT(input_bct[2:], lam=BCT_LAMBDA)

    x_mean = np.asarray(exported['data_in_mean'], dtype=np.float64)
    x_std = np.asarray(exported['data_in_std'], dtype=np.float64)
    input_norm = ((input_bct - x_mean) / x_std).astype(np.float32)
    input_tensor = torch.tensor(input_norm[None, :], dtype=torch.float32)

    outputs = []
    for species_idx in range(n_species - 1):
        model = DeepFlameScalarMLP([2 + n_species, *hidden_layers, 1])
        model.load_state_dict(exported[f'net{species_idx}'])
        model.eval()
        with torch.no_grad():
            outputs.append(model(input_tensor).numpy()[0, 0])
    outputs = np.asarray(outputs, dtype=np.float32)

    y_mean = np.asarray(exported['data_target_mean'], dtype=np.float32)
    y_std = np.asarray(exported['data_target_std'], dtype=np.float32)
    out_bct = outputs * y_std + y_mean + input_bct[2:-1]
    out_bct = np.maximum(out_bct, BCT_INVERSE_FLOOR)
    next_y = input_y.copy()
    next_y[:-1] = inverse_BCT(out_bct, lam=BCT_LAMBDA)
    denom = np.sum(next_y[:-1], keepdims=True)
    if float(denom) > 0:
        next_y[:-1] = next_y[:-1] / denom * (1.0 - next_y[-1])
    return next_y



def validate_export(
    checkpoint: dict,
    exported: dict,
    dataset_path: str,
    metadata_path: str,
    n_species: int,
    max_samples: int,
) -> dict:
    dataset = np.load(dataset_path)
    metadata = json.loads(Path(metadata_path).read_text())
    state_width = 2 + n_species
    current_states = dataset[:, :state_width]
    sample_count = min(max_samples, len(current_states))
    current_states = current_states[:sample_count]

    next_species_diffs = []
    source_diffs = []
    densities = []

    import cantera as ct

    gas = ct.Solution(metadata['mech'])
    dt = float(metadata['dt'])
    for state in current_states:
        y_original = _predict_next_species_original_species_branch(checkpoint, state, n_species)
        y_deepflame = _predict_next_species_deepflame(exported, state, n_species)
        next_species_diffs.append(np.max(np.abs(y_original - y_deepflame)))

        gas.TPY = float(state[0]), float(state[1]), state[2:]
        rho = gas.density
        densities.append(rho)
        src_original = (y_original - state[2:]) * rho / dt
        src_deepflame = (y_deepflame - state[2:]) * rho / dt
        source_diffs.append(np.max(np.abs(src_original - src_deepflame)))

    return {
        'validation_samples': sample_count,
        'max_abs_next_species_diff': float(np.max(next_species_diffs)) if next_species_diffs else 0.0,
        'mean_abs_next_species_diff': float(np.mean(next_species_diffs)) if next_species_diffs else 0.0,
        'max_abs_source_diff': float(np.max(source_diffs)) if source_diffs else 0.0,
        'mean_abs_source_diff': float(np.mean(source_diffs)) if source_diffs else 0.0,
        'density_range': [float(np.min(densities)), float(np.max(densities))] if densities else [0.0, 0.0],
    }



def main() -> None:
    args = parse_args()
    checkpoint = torch.load(args.checkpoint, map_location='cpu')
    checkpoint['source_checkpoint'] = str(Path(args.checkpoint).resolve())
    exported = export_checkpoint(checkpoint, args.n_species)

    validation = None
    if args.validate_dataset and args.validate_metadata:
        validation = validate_export(
            checkpoint=checkpoint,
            exported=exported,
            dataset_path=args.validate_dataset,
            metadata_path=args.validate_metadata,
            n_species=args.n_species,
            max_samples=args.max_validate_samples,
        )
        exported['export_metadata']['validation'] = validation

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(exported, out_path)
    print(f'Saved exported checkpoint: {out_path}')

    if args.validation_out:
        payload = {
            'source_checkpoint': str(Path(args.checkpoint).resolve()),
            'exported_checkpoint': str(out_path.resolve()),
            'n_species': args.n_species,
            'validation': validation,
        }
        Path(args.validation_out).write_text(json.dumps(payload, indent=2), encoding='utf-8')
        print(json.dumps(payload, indent=2))


if __name__ == '__main__':
    main()
