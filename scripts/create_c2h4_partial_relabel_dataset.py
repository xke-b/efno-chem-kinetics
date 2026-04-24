#!/usr/bin/env python3
"""Create a mixed C2H4 dataset by replacing a sampled subset of labels with relabeled targets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np



def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument('--base-dataset', required=True)
    p.add_argument('--base-metadata', required=True)
    p.add_argument('--relabel-dataset', required=True)
    p.add_argument('--relabel-metadata', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--metadata-out', default=None)
    return p.parse_args()



def main() -> None:
    args = parse_args()
    base = np.load(args.base_dataset)
    relabeled = np.load(args.relabel_dataset)
    base_meta = json.loads(Path(args.base_metadata).read_text())
    relabel_meta = json.loads(Path(args.relabel_metadata).read_text())

    if base.shape[1] != relabeled.shape[1]:
        raise ValueError(f'Column mismatch: {base.shape} vs {relabeled.shape}')

    selected = relabel_meta['selected_indices']
    count = int(selected['count'])
    max_samples = selected.get('max_samples')
    seed = int(selected.get('seed', 0))
    index_file = selected.get('index_file')
    if count != relabeled.shape[0]:
        raise ValueError('Relabeled row count does not match metadata count')

    if index_file:
        selection_payload = json.loads(Path(index_file).read_text())
        indices = np.asarray(selection_payload['indices'], dtype=int)
        if len(indices) != len(relabeled):
            raise ValueError('Explicit selection indices length does not match relabeled dataset length')
    else:
        rng = np.random.default_rng(seed)
        if max_samples is not None and len(base) > max_samples:
            indices = np.sort(rng.choice(len(base), size=max_samples, replace=False))
        else:
            indices = np.arange(len(base))
        if len(indices) != len(relabeled):
            raise ValueError('Selected indices length does not match relabeled dataset length')

    mixed = base.copy()
    n_species = len(base_meta['species_names'])
    next_offset = 2 + n_species
    mixed[indices, next_offset:] = relabeled[:, next_offset:]

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(out_path, mixed)

    meta = {
        'output': str(out_path.resolve()),
        'dataset_shape': list(mixed.shape),
        'base_dataset': str(Path(args.base_dataset).resolve()),
        'base_metadata': str(Path(args.base_metadata).resolve()),
        'relabel_dataset': str(Path(args.relabel_dataset).resolve()),
        'relabel_metadata': str(Path(args.relabel_metadata).resolve()),
        'replaced_rows': int(len(indices)),
        'replaced_fraction': float(len(indices) / len(base)),
        'selection_seed': seed,
        'selection_max_samples': max_samples,
        'selection_index_file': str(Path(index_file).resolve()) if index_file else None,
        'n_species': n_species,
        'species_names': base_meta['species_names'],
        'state_layout': base_meta['state_layout'],
        'note': 'Mixed C2H4 dataset with original current states and partial replacement of next-state labels by chemistry-proxy relabeling.',
    }
    metadata_out = Path(args.metadata_out) if args.metadata_out else out_path.with_suffix('.json')
    metadata_out.write_text(json.dumps(meta, indent=2), encoding='utf-8')
    print(json.dumps(meta, indent=2))


if __name__ == '__main__':
    main()
