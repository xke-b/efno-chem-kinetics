#!/usr/bin/env python3
"""Build a mixed C2H4 case-pair dataset from multiple paired-state sources."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def reorder_paired_dataset(arr: np.ndarray, source_species: list[str], target_species: list[str]) -> np.ndarray:
    if source_species == target_species:
        return arr
    if set(source_species) != set(target_species):
        raise ValueError('Source and target species sets differ; cannot reorder paired dataset safely')
    width = 2 + len(source_species)
    if arr.shape[1] != 2 * width:
        raise ValueError(f'Expected paired dataset width {2 * width}, got {arr.shape[1]}')
    src_index = {name: i for i, name in enumerate(source_species)}
    tgt_positions = [src_index[name] for name in target_species]
    current = arr[:, :width]
    nxt = arr[:, width:]
    reordered_current = np.column_stack([current[:, :2], current[:, 2:][:, tgt_positions]])
    reordered_next = np.column_stack([nxt[:, :2], nxt[:, 2:][:, tgt_positions]])
    return np.hstack([reordered_current, reordered_next])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--datasets', nargs='+', required=True)
    parser.add_argument('--metadata-files', nargs='+', required=True)
    parser.add_argument('--labels', nargs='+', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--metadata-out', default=None)
    return parser.parse_args()



def main() -> None:
    args = parse_args()
    if not (len(args.datasets) == len(args.metadata_files) == len(args.labels)):
        raise ValueError('datasets, metadata-files, and labels must have equal length')

    arrays = []
    component_rows = {}
    source_meta = []
    target_species_names = None
    for label, dataset_path, meta_path in zip(args.labels, args.datasets, args.metadata_files):
        arr = np.load(dataset_path)
        meta = json.loads(Path(meta_path).read_text())
        species_names = meta.get('species_names')
        if species_names is None:
            raise ValueError(f'Metadata for {dataset_path} is missing species_names')
        if target_species_names is None:
            target_species_names = list(species_names)
        arr = reorder_paired_dataset(arr, list(species_names), target_species_names)
        arrays.append(arr)
        component_rows[label] = int(arr.shape[0])
        source_meta.append({
            'label': label,
            'dataset': str(Path(dataset_path).resolve()),
            'metadata': str(Path(meta_path).resolve()),
            'rows': int(arr.shape[0]),
            'source_species_names': list(species_names),
            'target_species_names': list(target_species_names),
            'reordered_to_target': bool(list(species_names) != list(target_species_names)),
        })

    dataset = np.concatenate(arrays, axis=0)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(out_path, dataset)

    metadata = {
        'output': str(out_path.resolve()),
        'dataset_shape': list(dataset.shape),
        'components': source_meta,
        'component_rows': component_rows,
        'species_names': target_species_names,
        'state_layout': ['T', 'P', *target_species_names, 'T_next', 'P_next', *[f'{s}_next' for s in target_species_names]],
        'note': 'Mixed C2H4 paired dataset assembled by concatenating multiple sources after reordering each component into a common species layout taken from the first dataset metadata.',
    }
    metadata_out = Path(args.metadata_out) if args.metadata_out else out_path.with_suffix('.json')
    metadata_out.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print(json.dumps(metadata, indent=2))


if __name__ == '__main__':
    main()
