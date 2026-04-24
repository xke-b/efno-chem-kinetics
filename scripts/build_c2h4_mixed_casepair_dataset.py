#!/usr/bin/env python3
"""Build a mixed C2H4 case-pair dataset from multiple paired-state sources."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


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
    for label, dataset_path, meta_path in zip(args.labels, args.datasets, args.metadata_files):
        arr = np.load(dataset_path)
        meta = json.loads(Path(meta_path).read_text())
        arrays.append(arr)
        component_rows[label] = int(arr.shape[0])
        source_meta.append({
            'label': label,
            'dataset': str(Path(dataset_path).resolve()),
            'metadata': str(Path(meta_path).resolve()),
            'rows': int(arr.shape[0]),
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
        'note': 'Mixed C2H4 case-pair dataset assembled by concatenating multiple case-aligned paired-state sources.',
    }
    metadata_out = Path(args.metadata_out) if args.metadata_out else out_path.with_suffix('.json')
    metadata_out.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print(json.dumps(metadata, indent=2))


if __name__ == '__main__':
    main()
