#!/usr/bin/env python3
"""Create a staged DeepFlame C2H4 case that switches models at a chosen restart time.

This packages the manual staged-switch workflow used for C2H4 deployment-facing
experiments:
- start from an already-run source case
- restart from a written switch time
- replace the inference bundle for the continuation segment
- remove later written times/logs so the continuation is reproducible
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-case', default=None)
    parser.add_argument('--switch-bundle-dir', default=None)
    parser.add_argument('--switch-time', default=None)
    parser.add_argument('--end-time', default=None)
    parser.add_argument('--schedule-config', default=None)
    parser.add_argument('--out-case', required=True)
    parser.add_argument('--metadata-out', default=None)
    return parser.parse_args()



def replace_line(pattern: str, replacement: str, text: str) -> str:
    import re
    new_text, count = re.subn(pattern, replacement, text)
    if count == 0:
        raise ValueError(f'Pattern not found: {pattern!r}')
    return new_text



def parse_time_value(name: str) -> float | None:
    try:
        return float(name)
    except ValueError:
        return None



def _load_schedule_config(path: str | None) -> dict:
    if path is None:
        return {}
    return json.loads(Path(path).read_text())



def _require_value(name: str, explicit: str | None, config: dict, *, default: str | None = None) -> str:
    value = explicit if explicit is not None else config.get(name, default)
    if value is None:
        raise ValueError(f'Missing required value for {name!r}')
    return str(value)



def _available_written_times(source_case: Path) -> list[float]:
    processor0 = source_case / 'processor0'
    if not processor0.exists():
        return []
    values: list[float] = []
    for path in processor0.iterdir():
        if not path.is_dir():
            continue
        time_value = parse_time_value(path.name)
        if time_value is not None:
            values.append(time_value)
    return sorted(set(values))



def main() -> None:
    args = parse_args()
    schedule_config = _load_schedule_config(args.schedule_config)
    source_case = Path(_require_value('source_case', args.source_case, schedule_config))
    bundle_dir = Path(_require_value('switch_bundle_dir', args.switch_bundle_dir, schedule_config))
    out_case = Path(args.out_case)
    switch_time = _require_value('switch_time', args.switch_time, schedule_config)
    end_time = _require_value('end_time', args.end_time, schedule_config, default='5e-6')

    written_times = _available_written_times(source_case)
    switch_value = float(switch_time)
    if written_times and switch_value not in written_times:
        nearest = min(written_times, key=lambda value: abs(value - switch_value))
        raise ValueError(
            f'switch_time {switch_time} is not a written restart time in {source_case}. '
            f'Nearest available written time is {nearest:g}. '
            f'Available times: {", ".join(f"{value:g}" for value in written_times)}'
        )

    if out_case.exists():
        shutil.rmtree(out_case)
    shutil.copytree(source_case, out_case)

    inference_src = bundle_dir / 'inference.py'
    model_src = bundle_dir / 'DNN_model_fno.pt'
    if not inference_src.exists() or not model_src.exists():
        raise FileNotFoundError('switch bundle must contain inference.py and DNN_model_fno.pt')

    shutil.copy2(inference_src, out_case / 'inference.py')
    shutil.copy2(model_src, out_case / 'DNN_model_fno.pt')

    ctp_path = out_case / 'constant' / 'CanteraTorchProperties'
    ctp_text = ctp_path.read_text()
    ctp_text = replace_line(r'torchModel\s+"[^"]+";', 'torchModel        "DNN_model_fno.pt";', ctp_text)
    ctp_path.write_text(ctp_text)

    control_path = out_case / 'system' / 'controlDict'
    control_text = control_path.read_text()
    control_text = replace_line(r'startFrom\s+\w+;', 'startFrom       startTime;', control_text)
    control_text = replace_line(r'startTime\s+[0-9.eE+-]+;', f'startTime       {switch_time};', control_text)
    control_text = replace_line(r'endTime\s+[0-9.eE+-]+;', f'endTime         {end_time};', control_text)
    control_path.write_text(control_text)

    switch_value = float(switch_time)
    end_value = float(end_time)
    removed_times: list[str] = []
    for path in out_case.rglob('*'):
        if not path.is_dir():
            continue
        time_value = parse_time_value(path.name)
        if time_value is None:
            continue
        if time_value > switch_value + 1e-15:
            shutil.rmtree(path)
            removed_times.append(str(path.relative_to(out_case)))

    for log_name in ['run.log', 'solver.err', 'mpirun.pid']:
        log_path = out_case / log_name
        if log_path.exists():
            log_path.unlink()

    metadata = {
        'source_case': str(source_case.resolve()),
        'switch_bundle_dir': str(bundle_dir.resolve()),
        'switch_time': switch_time,
        'end_time': end_time,
        'out_case': str(out_case.resolve()),
        'removed_time_dirs_count': len(removed_times),
        'schedule_config': str(Path(args.schedule_config).resolve()) if args.schedule_config else None,
        'note': 'Staged DeepFlame C2H4 case generated by copying a completed source case, restarting from switch_time, and swapping to a new inference bundle for the continuation segment.',
    }
    metadata_path = Path(args.metadata_out) if args.metadata_out else out_case / 'scheduled_switch_metadata.json'
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print(json.dumps(metadata, indent=2))


if __name__ == '__main__':
    main()
