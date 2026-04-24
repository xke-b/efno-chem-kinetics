#!/usr/bin/env python3
"""Export a DFODE-kit FNO checkpoint into a DeepFlame bundle.

The current DeepFlame Python bridge only requires a case-local `inference.py` with
an `inference(vec0)` entrypoint plus a checkpoint referenced by
`constant/CanteraTorchProperties`. Unlike the existing MLP bridge, an FNO model
can stay as a single shared multi-output network, so this exporter writes:

- a compact exported checkpoint with the FNO weights and normalization stats
- a self-contained `inference.py` that rebuilds the FNO model without depending
  on DFODE-kit at runtime

This is an enabling integration bridge. It does not by itself guarantee that the
trained FNO is a good chemistry surrogate for a target DeepFlame case.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch

from dfode_kit.models.fno1d import FNO1d
from dfode_kit.utils import BCT, inverse_BCT, inverse_power_transform


BCT_LAMBDA = 0.1
POWER_LAMBDA = 0.1
BCT_INVERSE_FLOOR = -1.0 / BCT_LAMBDA + 1e-8


INFERENCE_TEMPLATE = """import os
import torch
import numpy as np
import cantera as ct


BCT_LAMBDA = 0.1
POWER_LAMBDA = 0.1
BCT_INVERSE_FLOOR = -1.0 / BCT_LAMBDA + 1e-8

device_main = \"cuda:0\"
DEFAULT_BATCH_SIZE = 8192

torch.set_printoptions(precision=10)


class SpectralConv1d(torch.nn.Module):
    def __init__(self, in_channels: int, out_channels: int, modes: int) -> None:
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.modes = modes
        scale = 1 / max(1, in_channels * out_channels)
        self.weights = torch.nn.Parameter(
            scale * torch.randn(in_channels, out_channels, modes, dtype=torch.cfloat)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        batch_size, _, signal_length = x.shape
        x_ft = torch.fft.rfft(x, dim=-1)
        usable_modes = min(self.modes, x_ft.size(-1))
        out_ft = torch.zeros(
            batch_size,
            self.out_channels,
            x_ft.size(-1),
            dtype=torch.cfloat,
            device=x.device,
        )
        out_ft[:, :, :usable_modes] = torch.einsum(
            \"bim,iom->bom\",
            x_ft[:, :, :usable_modes],
            self.weights[:, :, :usable_modes],
        )
        return torch.fft.irfft(out_ft, n=signal_length, dim=-1)


class FNO1d(torch.nn.Module):
    def __init__(self, *, input_tokens: int, output_tokens: int, width: int, modes: int, n_layers: int, activation: str, attention_heads: int = 0, attention_layers: int = 0, attention_dropout: float = 0.0) -> None:
        super().__init__()
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.width = width
        self.modes = min(modes, input_tokens // 2 + 1)
        self.n_layers = n_layers
        self.attention_heads = attention_heads
        self.attention_layers = attention_layers
        self.attention_dropout = attention_dropout
        self.lift = torch.nn.Linear(1, width)
        self.spectral_layers = torch.nn.ModuleList(
            [SpectralConv1d(width, width, self.modes) for _ in range(n_layers)]
        )
        self.pointwise_layers = torch.nn.ModuleList(
            [torch.nn.Conv1d(width, width, kernel_size=1) for _ in range(n_layers)]
        )
        self.attention_norms = torch.nn.ModuleList()
        self.attention_layers_seq = torch.nn.ModuleList()
        self.attention_ffn_norms = torch.nn.ModuleList()
        self.attention_ffns = torch.nn.ModuleList()
        for _ in range(attention_layers):
            self.attention_norms.append(torch.nn.LayerNorm(width))
            self.attention_layers_seq.append(torch.nn.MultiheadAttention(width, attention_heads, dropout=attention_dropout, batch_first=True))
            self.attention_ffn_norms.append(torch.nn.LayerNorm(width))
            self.attention_ffns.append(torch.nn.Sequential(
                torch.nn.Linear(width, width),
                _make_activation(activation),
                torch.nn.Linear(width, width),
            ))
        self.project_channels = torch.nn.Sequential(
            torch.nn.Linear(width, width),
            _make_activation(activation),
            torch.nn.Linear(width, 1),
        )
        self.project_tokens = torch.nn.Linear(input_tokens, output_tokens)
        self.activation = _make_activation(activation)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.lift(x.unsqueeze(-1))
        x = x.permute(0, 2, 1)
        for spectral, pointwise in zip(self.spectral_layers, self.pointwise_layers):
            x = self.activation(spectral(x) + pointwise(x))
        x = x.permute(0, 2, 1)
        for norm, attn, ffn_norm, ffn in zip(self.attention_norms, self.attention_layers_seq, self.attention_ffn_norms, self.attention_ffns):
            attn_in = norm(x)
            attn_out, _ = attn(attn_in, attn_in, attn_in, need_weights=False)
            x = x + attn_out
            x = x + ffn(ffn_norm(x))
        x = self.project_channels(x).squeeze(-1)
        return self.project_tokens(x)


def _make_activation(name: str) -> torch.nn.Module:
    name = name.lower()
    if name == \"gelu\":
        return torch.nn.GELU()
    if name in {\"leaky_relu\", \"lrelu\"}:
        return torch.nn.LeakyReLU()
    raise ValueError(f\"Unsupported activation {name!r}\")


def _bct(y):
    return (np.power(y, BCT_LAMBDA) - 1.0) / BCT_LAMBDA


def _inverse_bct(z):
    z = np.maximum(z, BCT_INVERSE_FLOOR)
    return np.power(BCT_LAMBDA * z + 1.0, 1.0 / BCT_LAMBDA)


def _inverse_power_delta(z):
    return np.sign(z) * np.power(np.abs(z) * POWER_LAMBDA, 1.0 / POWER_LAMBDA)


try:
    path_r = r\"./constant/CanteraTorchProperties\"
    with open(path_r, \"r\") as f:
        data = f.read()
        i = data.index('torchModel')
        a = data.index('\"', i)
        b = data.index('\"', a + 1)
        modelName = data[a + 1:b]

        i = data.index('frozenTemperature')
        a = data.index(';', i)
        b = data.rfind(' ', i + 1, a)
        frozenTemperature = float(data[b + 1:a])

        i = data.index('inferenceDeltaTime')
        a = data.index(';', i)
        b = data.rfind(' ', i + 1, a)
        delta_t = float(data[b + 1:a])

        i = data.index('CanteraMechanismFile')
        a = data.index('\"', i)
        b = data.index('\"', a + 1)
        mechanismName = data[a + 1:b]

        i = data.index('GPU')
        a = data.index(';', i)
        b = data.rfind(' ', i + 1, a)
        switch_GPU = data[b + 1:a]

    gas = ct.Solution(mechanismName)
    n_species = gas.n_species

    switch_on = [\"true\", \"True\", \"on\", \"yes\", \"y\", \"t\", \"any\"]
    switch_off = [\"false\", \"False\", \"off\", \"no\", \"n\", \"f\", \"none\"]
    if switch_GPU in switch_on and torch.cuda.is_available():
        device = torch.device(device_main)
    else:
        device = torch.device(\"cpu\")

    payload = torch.load(modelName, map_location='cpu')
    meta = payload['export_metadata']
    target_mode = str(meta.get('target_mode', 'species_only'))
    power_lambda = float(meta.get('power_lambda', POWER_LAMBDA))
    globals()['POWER_LAMBDA'] = power_lambda
    model = FNO1d(
        input_tokens=int(meta['input_tokens']),
        output_tokens=int(meta['output_tokens']),
        width=int(meta['width']),
        modes=int(meta['modes']),
        n_layers=int(meta['n_layers']),
        activation=str(meta['activation']),
        attention_heads=int(meta.get('attention_heads', 0)),
        attention_layers=int(meta.get('attention_layers', 0)),
        attention_dropout=float(meta.get('attention_dropout', 0.0)),
    )
    model.load_state_dict(payload['net'])
    model.eval()
    model.to(device=device)

    Xmu = torch.tensor(np.asarray(payload['data_in_mean']), dtype=torch.float32, device=device).unsqueeze(0)
    Xstd = torch.tensor(np.asarray(payload['data_in_std']), dtype=torch.float32, device=device).unsqueeze(0)
    Ymu = torch.tensor(np.asarray(payload['data_target_mean']), dtype=torch.float32, device=device).unsqueeze(0)
    Ystd = torch.tensor(np.asarray(payload['data_target_std']), dtype=torch.float32, device=device).unsqueeze(0)
except Exception as e:
    print(e.args)


def _run_model_in_batches(vec0_input):
    outputs = []
    batch_size = DEFAULT_BATCH_SIZE
    start = 0
    while start < vec0_input.shape[0]:
        stop = min(start + batch_size, vec0_input.shape[0])
        batch = vec0_input[start:stop]
        try:
            with torch.no_grad():
                rho0 = torch.from_numpy(batch[:, -1:]).to(device=device, dtype=torch.float32)
                input_y = torch.from_numpy(batch[:, 2:-1].copy()).to(device=device, dtype=torch.float32)
                input_bct_np = batch[:, 0:-1].copy()
                input_bct_np[:, 2:] = _bct(np.clip(input_bct_np[:, 2:], 0.0, 1.0))
                input_bct = torch.from_numpy(input_bct_np).to(device=device, dtype=torch.float32)
                input_norm = (input_bct - Xmu) / Xstd
                output_norm = model(input_norm)
                output_raw = output_norm * Ystd + Ymu

                if target_mode == 'species_power_delta':
                    output_delta = _inverse_power_delta(output_raw.detach().cpu().numpy())
                    output_main = np.clip(batch[:, 2:-2] + output_delta, 0.0, 1.0)
                else:
                    output_bct = torch.clamp(input_bct[:, 2:-1] + output_raw, min=BCT_INVERSE_FLOOR)
                    output_main = _inverse_bct(output_bct.detach().cpu().numpy())
                output_y = input_y.clone()
                output_y[:, :-1] = torch.from_numpy(output_main).to(device=device, dtype=torch.float32)
                denom = torch.sum(output_y[:, :-1], dim=1, keepdim=True)
                output_y[:, :-1] = output_y[:, :-1] / torch.clamp(denom, min=1e-12) * (1 - output_y[:, -1:])
                output = (output_y - input_y) * rho0 / delta_t
                outputs.append(output.cpu().numpy())
                start = stop
        except RuntimeError as e:
            if 'out of memory' not in str(e).lower() or batch_size <= 1:
                raise
            if device.type == 'cuda':
                torch.cuda.empty_cache()
            batch_size = max(1, batch_size // 2)
            print(f'FNO inference batch OOM, retrying with batch_size={batch_size}')
    return np.vstack(outputs) if outputs else np.zeros((0, n_species), dtype=np.float64)



def inference(vec0):
    vec0 = np.abs(np.reshape(vec0, (-1, 3 + n_species)))
    vec0[:, 1] *= 101325
    mask = vec0[:, 0] > frozenTemperature
    vec0_input = vec0[mask, :]
    print(f'real inference points number: {vec0_input.shape[0]}')

    try:
        if vec0_input.shape[0] == 0:
            return np.zeros((vec0.shape[0], n_species), dtype=np.float64)

        output = _run_model_in_batches(vec0_input)
        result = np.zeros((vec0.shape[0], n_species), dtype=np.float64)
        result[mask, :] = output
        return result
    except Exception as e:
        print(e.args)
        return np.zeros((vec0.shape[0], n_species), dtype=np.float64)
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--checkpoint', required=True)
    parser.add_argument('--out-dir', required=True)
    parser.add_argument('--model-filename', default='DNN_model_fno.pt')
    parser.add_argument('--validate-dataset', default=None)
    parser.add_argument('--max-validate-samples', type=int, default=128)
    return parser.parse_args()


class RuntimeFNOBundle(torch.nn.Module):
    def __init__(self, *, input_tokens: int, output_tokens: int, width: int, modes: int, n_layers: int, activation: str) -> None:
        super().__init__()
        self.model = FNO1d(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            width=width,
            modes=modes,
            n_layers=n_layers,
            activation=activation,
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.model(x)



def build_export_payload(checkpoint: dict) -> dict:
    cfg = checkpoint.get('training_config', {})
    model_cfg = cfg.get('model', {})
    if model_cfg.get('name') != 'fno1d':
        raise ValueError('Checkpoint model.name must be fno1d')

    params = dict(model_cfg.get('params', {}))
    trainer_params = cfg.get('trainer', {}).get('params', {})
    state = checkpoint['net']
    final_weight_key = 'project_tokens.weight'
    if final_weight_key not in state:
        raise ValueError('Unsupported FNO checkpoint: missing project_tokens.weight')

    input_tokens = int(state['project_tokens.weight'].shape[1])
    output_tokens = int(state['project_tokens.weight'].shape[0])
    payload = {
        'net': state,
        'data_in_mean': np.asarray(checkpoint['data_in_mean']),
        'data_in_std': np.asarray(checkpoint['data_in_std']),
        'data_target_mean': np.asarray(checkpoint['data_target_mean'])[-output_tokens:],
        'data_target_std': np.asarray(checkpoint['data_target_std'])[-output_tokens:],
        'export_metadata': {
            'source_checkpoint': str(checkpoint.get('source_checkpoint', '')),
            'source_training_config': cfg,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'width': int(params.get('width', 32)),
            'modes': int(params.get('modes', 8)),
            'n_layers': int(params.get('n_layers', 4)),
            'activation': str(params.get('activation', 'gelu')),
            'attention_heads': int(params.get('attention_heads', 0)),
            'attention_layers': int(params.get('attention_layers', 0)),
            'attention_dropout': float(params.get('attention_dropout', 0.0)),
            'target_mode': str(trainer_params.get('target_mode', 'species_only')),
            'power_lambda': float(trainer_params.get('power_lambda', POWER_LAMBDA)),
            'export_type': 'dfode_fno_to_deepflame_bundle',
        },
    }
    return payload



def _predict_original_species(checkpoint: dict, state: np.ndarray) -> np.ndarray:
    cfg = checkpoint['training_config']
    model_cfg = cfg['model']
    params = dict(model_cfg.get('params', {}))
    target_mode = str(cfg.get('trainer', {}).get('params', {}).get('target_mode', 'species_only'))
    power_lambda = float(cfg.get('trainer', {}).get('params', {}).get('power_lambda', POWER_LAMBDA))
    n_species = len(state) - 2
    output_dim = int(params.get('output_dim', n_species - 1))
    model = FNO1d(
        input_tokens=2 + n_species,
        output_tokens=output_dim,
        width=int(params.get('width', 32)),
        modes=int(params.get('modes', 8)),
        n_layers=int(params.get('n_layers', 4)),
        activation=str(params.get('activation', 'gelu')),
        attention_heads=int(params.get('attention_heads', 0)),
        attention_layers=int(params.get('attention_layers', 0)),
        attention_dropout=float(params.get('attention_dropout', 0.0)),
    )
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
    raw = pred_norm * y_std[-output_dim:] + y_mean[-output_dim:]
    if target_mode == 'species_power_delta':
        main_species = y[:-1] + inverse_power_transform(raw, lam=power_lambda)
    else:
        base_bct = BCT(y[:-1], lam=BCT_LAMBDA).astype(np.float32)
        pred_bct = np.maximum(base_bct + raw, BCT_INVERSE_FLOOR)
        main_species = inverse_BCT(pred_bct, lam=BCT_LAMBDA)
    main_species = np.clip(main_species, 0.0, 1.0)
    out = y.copy()
    out[:-1] = main_species
    denom = np.sum(out[:-1], keepdims=True)
    if float(denom) > 0:
        out[:-1] = out[:-1] / denom * (1.0 - out[-1])
    return out



def _predict_exported_species(payload: dict, state: np.ndarray) -> np.ndarray:
    meta = payload['export_metadata']
    target_mode = str(meta.get('target_mode', 'species_only'))
    power_lambda = float(meta.get('power_lambda', POWER_LAMBDA))
    n_species = len(state) - 2
    model = FNO1d(
        input_tokens=int(meta['input_tokens']),
        output_tokens=int(meta['output_tokens']),
        width=int(meta['width']),
        modes=int(meta['modes']),
        n_layers=int(meta['n_layers']),
        activation=str(meta['activation']),
        attention_heads=int(meta.get('attention_heads', 0)),
        attention_layers=int(meta.get('attention_layers', 0)),
        attention_dropout=float(meta.get('attention_dropout', 0.0)),
    )
    model.load_state_dict(payload['net'])
    model.eval()

    y = np.clip(state[2:], 0.0, 1.0)
    x = np.hstack((state[:2], BCT(y, lam=BCT_LAMBDA))).astype(np.float32)
    x_mean = np.asarray(payload['data_in_mean'], dtype=np.float32)
    x_std = np.asarray(payload['data_in_std'], dtype=np.float32)
    y_mean = np.asarray(payload['data_target_mean'], dtype=np.float32)
    y_std = np.asarray(payload['data_target_std'], dtype=np.float32)
    x_norm = torch.tensor(((x - x_mean) / x_std)[None, :], dtype=torch.float32)
    with torch.no_grad():
        pred_norm = model(x_norm).numpy()[0]
    raw = pred_norm * y_std + y_mean
    if target_mode == 'species_power_delta':
        main_species = y[:-1] + inverse_power_transform(raw, lam=power_lambda)
    else:
        base_bct = BCT(y[:-1], lam=BCT_LAMBDA).astype(np.float32)
        pred_bct = np.maximum(base_bct + raw, BCT_INVERSE_FLOOR)
        main_species = inverse_BCT(pred_bct, lam=BCT_LAMBDA)
    main_species = np.clip(main_species, 0.0, 1.0)
    out = y.copy()
    out[:-1] = main_species
    denom = np.sum(out[:-1], keepdims=True)
    if float(denom) > 0:
        out[:-1] = out[:-1] / denom * (1.0 - out[-1])
    return out



def validate_export(checkpoint: dict, payload: dict, dataset_path: str, max_samples: int) -> dict:
    dataset = np.load(dataset_path)
    state_width = 2 + payload['export_metadata']['input_tokens'] - 2
    current_states = dataset[:, :state_width]
    sample_count = min(max_samples, len(current_states))
    diffs = []
    for state in current_states[:sample_count]:
        ref = _predict_original_species(checkpoint, state)
        got = _predict_exported_species(payload, state)
        diffs.append(np.max(np.abs(ref - got)))
    return {
        'validation_samples': sample_count,
        'max_abs_next_species_diff': float(np.max(diffs)) if diffs else 0.0,
        'mean_abs_next_species_diff': float(np.mean(diffs)) if diffs else 0.0,
    }



def main() -> None:
    args = parse_args()
    checkpoint = torch.load(args.checkpoint, map_location='cpu')
    checkpoint['source_checkpoint'] = str(Path(args.checkpoint).resolve())
    payload = build_export_payload(checkpoint)

    if args.validate_dataset:
        payload['export_metadata']['validation'] = validate_export(
            checkpoint=checkpoint,
            payload=payload,
            dataset_path=args.validate_dataset,
            max_samples=args.max_validate_samples,
        )

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    model_path = out_dir / args.model_filename
    inference_path = out_dir / 'inference.py'
    torch.save(payload, model_path)
    inference_path.write_text(INFERENCE_TEMPLATE, encoding='utf-8')

    print(json.dumps({
        'model_path': str(model_path.resolve()),
        'inference_path': str(inference_path.resolve()),
        'export_metadata': payload['export_metadata'],
    }, indent=2))


if __name__ == '__main__':
    main()
