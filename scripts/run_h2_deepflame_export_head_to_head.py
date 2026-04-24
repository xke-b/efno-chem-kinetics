#!/usr/bin/env python3
"""Head-to-head comparison of exported DeepFlame-compatible H2 candidate checkpoints.

This evaluates the shortlisted offline H2 candidates after exporting them into the
current DeepFlame multi-network species format. Metrics are computed using the
species-only deployment path:
  1. predict next species with the exported DeepFlame-style model
  2. reconstruct next temperature from current enthalpy + next species at the
     same pressure (matching the species-only deployment contract)
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path('/root/workspace')
SCRIPTS_DIR = ROOT / 'scripts'
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from export_dfode_checkpoint_to_deepflame import export_checkpoint, validate_export, _predict_next_species_deepflame


DATASET = ROOT / 'data' / 'h2_autoignition_longprobe_test.npy'
METADATA = ROOT / 'data' / 'h2_autoignition_longprobe_test.json'
OUT_DIR = ROOT / 'artifacts' / 'experiments' / 'h2_deepflame_export_head_to_head'
MODEL_DIR = ROOT / 'artifacts' / 'models' / 'h2_deepflame_candidates'
OUT_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)

CASES = {
    'supervised_deltaT_25ep': ROOT / 'data' / 'h2_holdout_mlp_supervised_deltaT_25ep_seed0.pt',
    'teacherforced_rollout0p1_bctdecode': ROOT / 'data' / 'h2_holdout_mlp_teacherforced_rollout0p1_bctdecode_seed0.pt',
    'self_rollout0p1_bctdecode': ROOT / 'data' / 'h2_holdout_mlp_self_rollout0p1_bctdecode_seed0.pt',
    'self_rollout0p1_predicted_main_bct_bctdecode': ROOT / 'data' / 'h2_holdout_mlp_self_rollout0p1_predicted_main_bct_bctdecode_seed0.pt',
}


def build_element_mass_matrix(mech_path: str) -> np.ndarray:
    import cantera as ct

    gas = ct.Solution(mech_path)
    matrix = np.zeros((gas.n_species, gas.n_elements), dtype=np.float64)
    for s_idx, species in enumerate(gas.species()):
        molecular_weight = gas.molecular_weights[s_idx]
        for e_idx, element_name in enumerate(gas.element_names):
            n_atoms = species.composition.get(element_name, 0.0)
            if n_atoms == 0:
                continue
            matrix[s_idx, e_idx] = n_atoms * gas.atomic_weights[e_idx] / molecular_weight
    return matrix



def deepflame_predict_next_state(exported: dict, current: np.ndarray, setter_gas, getter_gas) -> np.ndarray:
    next_y = _predict_next_species_deepflame(exported, current, exported['export_metadata']['n_species'])
    setter_gas.TPY = float(current[0]), float(current[1]), current[2:]
    h = setter_gas.enthalpy_mass
    getter_gas.Y = next_y
    getter_gas.HP = h, float(current[1])
    next_t = getter_gas.T
    return np.concatenate(([next_t, current[1]], next_y))



def evaluate_exported(exported: dict, dataset: np.ndarray, metadata: dict) -> dict:
    import cantera as ct

    n_species = int(metadata['n_species'])
    state_width = 2 + n_species
    n_init = int(metadata['n_init'])
    steps = int(metadata['steps'])
    mech_path = metadata['mech']

    current_states = dataset[:, :state_width]
    target_states = dataset[:, state_width:]
    element_mass_matrix = build_element_mass_matrix(mech_path)
    setter_gas = ct.Solution(mech_path)
    getter_gas = ct.Solution(mech_path)

    one_step_preds = []
    for row in current_states:
        one_step_preds.append(deepflame_predict_next_state(exported, row, setter_gas, getter_gas))
    pred_states = np.asarray(one_step_preds)
    pred_y = pred_states[:, 2:]
    true_y = target_states[:, 2:]

    metrics = {
        'one_step_species_mae': float(np.mean(np.abs(pred_y - true_y))),
        'one_step_temperature_mae': float(np.mean(np.abs(pred_states[:, 0] - target_states[:, 0]))),
        'one_step_element_mass_mae': float(np.mean(np.abs(pred_y @ element_mass_matrix - true_y @ element_mass_matrix))),
    }

    trajectories = dataset.reshape(n_init, steps, 2 * state_width)
    rollout_species = []
    rollout_temperature = []
    rollout_element = []
    for i in range(n_init):
        state = trajectories[i, 0, :state_width].copy()
        per_species = []
        per_temp = []
        per_elem = []
        for j in range(steps):
            pred_state = deepflame_predict_next_state(exported, state, setter_gas, getter_gas)
            true_next = trajectories[i, j, state_width:]
            pred_y = pred_state[2:]
            true_y = true_next[2:]
            per_species.append(float(np.mean(np.abs(pred_y - true_y))))
            per_temp.append(float(abs(pred_state[0] - true_next[0])))
            per_elem.append(float(np.mean(np.abs(pred_y @ element_mass_matrix - true_y @ element_mass_matrix))))
            state = pred_state.copy()
        rollout_species.append(per_species)
        rollout_temperature.append(per_temp)
        rollout_element.append(per_elem)

    rollout_species = np.asarray(rollout_species)
    rollout_temperature = np.asarray(rollout_temperature)
    rollout_element = np.asarray(rollout_element)
    metrics['rollout_species_mae_by_horizon'] = rollout_species.mean(axis=0).tolist()
    metrics['rollout_temperature_mae_by_horizon'] = rollout_temperature.mean(axis=0).tolist()
    metrics['rollout_element_mass_mae_by_horizon'] = rollout_element.mean(axis=0).tolist()
    return metrics



def summarize_case(metrics: list[dict]) -> dict:
    out = {'replicates': metrics, 'aggregate': {}}
    for key in ['one_step_species_mae', 'one_step_temperature_mae', 'one_step_element_mass_mae']:
        vals = [m[key] for m in metrics]
        out['aggregate'][key] = {
            'mean': statistics.fmean(vals),
            'min': min(vals),
            'max': max(vals),
            'stdev': statistics.pstdev(vals),
        }
    for source_key, out_key in [
        ('rollout_species_mae_by_horizon', 'rollout_species_mae_h1000'),
        ('rollout_temperature_mae_by_horizon', 'rollout_temperature_mae_h1000'),
        ('rollout_element_mass_mae_by_horizon', 'rollout_element_mass_mae_h1000'),
    ]:
        vals = [m[source_key][-1] for m in metrics]
        out['aggregate'][out_key] = {
            'mean': statistics.fmean(vals),
            'min': min(vals),
            'max': max(vals),
            'stdev': statistics.pstdev(vals),
        }
    return out



def main() -> None:
    dataset = np.load(DATASET)
    metadata = json.loads(METADATA.read_text())
    n_species = int(metadata['n_species'])

    summary = {
        'dataset': str(DATASET),
        'metadata': str(METADATA),
        'evaluation_contract': 'exported_deepflame_species_path_plus_enthalpy_temperature_reconstruction',
        'cases': {},
    }

    for case_name, ckpt_path in CASES.items():
        checkpoint = torch.load(ckpt_path, map_location='cpu')
        checkpoint['source_checkpoint'] = str(ckpt_path.resolve())
        exported = export_checkpoint(checkpoint, n_species)
        export_path = MODEL_DIR / f'{case_name}_deepflame.pt'
        torch.save(exported, export_path)
        validation = validate_export(
            checkpoint=checkpoint,
            exported=exported,
            dataset_path=str(DATASET),
            metadata_path=str(METADATA),
            n_species=n_species,
            max_samples=128,
        )

        replicate_metrics = []
        metrics = evaluate_exported(exported, dataset, metadata)
        metrics['source_checkpoint'] = str(ckpt_path.resolve())
        metrics['exported_checkpoint'] = str(export_path.resolve())
        metrics['export_validation'] = validation
        replicate_metrics.append(metrics)

        case_summary = summarize_case(replicate_metrics)
        case_summary['export_validation'] = validation
        summary['cases'][case_name] = case_summary

        (OUT_DIR / f'{case_name}_export_eval.json').write_text(json.dumps(metrics, indent=2), encoding='utf-8')

    summary['ranking_by_rollout_species_mae_h1000'] = sorted([
        {
            'name': name,
            'one_step_species_mae': payload['aggregate']['one_step_species_mae']['mean'],
            'one_step_temperature_mae': payload['aggregate']['one_step_temperature_mae']['mean'],
            'one_step_element_mass_mae': payload['aggregate']['one_step_element_mass_mae']['mean'],
            'rollout_species_mae_h1000': payload['aggregate']['rollout_species_mae_h1000']['mean'],
            'rollout_temperature_mae_h1000': payload['aggregate']['rollout_temperature_mae_h1000']['mean'],
            'rollout_element_mass_mae_h1000': payload['aggregate']['rollout_element_mass_mae_h1000']['mean'],
        }
        for name, payload in summary['cases'].items()
    ], key=lambda x: x['rollout_species_mae_h1000'])

    (OUT_DIR / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
