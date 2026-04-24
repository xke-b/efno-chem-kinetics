#!/usr/bin/env python3
"""Build a repeated-mix C2H4 dataset by concatenating a base dataset with repeated add-on data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument('--base', required=True)
    p.add_argument('--base-label', default='base')
    p.add_argument('--addon', required=True)
    p.add_argument('--addon-label', default='addon')
    p.add_argument('--addon-repeats', type=int, required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--metadata-out', default=None)
    p.add_argument('--note', default='')
    return p.parse_args()



def main() -> None:
    args = parse_args()
    base = np.load(args.base)
    addon = np.load(args.addon)
    mixed = np.concatenate([base] + [addon] * args.addon_repeats, axis=0)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(out_path, mixed)

    ratio = float((addon.shape[0] * args.addon_repeats) / base.shape[0])
    metadata = {
        'output': str(out_path.resolve()),
        'dataset_shape': list(mixed.shape),
        'components': [
            {
                'label': args.base_label,
                'dataset': str(Path(args.base).resolve()),
                'rows': int(base.shape[0]),
            },
            {
                'label': args.addon_label,
                'dataset': str(Path(args.addon).resolve()),
                'rows_per_copy': int(addon.shape[0]),
                'copies': int(args.addon_repeats),
                'effective_rows': int(addon.shape[0] * args.addon_repeats),
            },
        ],
        'component_rows': {
            args.base_label: int(base.shape[0]),
            args.addon_label: int(addon.shape[0] * args.addon_repeats),
        },
        'effective_addon_to_base_ratio': ratio,
        'note': args.note,
    }
    metadata_out = Path(args.metadata_out) if args.metadata_out else out_path.with_suffix('.json')
    metadata_out.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print(json.dumps(metadata, indent=2))


if __name__ == '__main__':
    main()
