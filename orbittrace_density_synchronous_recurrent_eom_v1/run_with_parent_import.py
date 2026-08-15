#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import runpy
import subprocess
import sys
from pathlib import Path
from types import ModuleType

PARENT_PATH = Path('orbittrace_recurrent_eom_hdbscan_v1/run_development.py')
SUCCESSOR_PATH = Path('orbittrace_density_synchronous_recurrent_eom_v1/run_development.py')
PARENT_BLOB = 'fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c'
SUCCESSOR_BLOB = '157813ca331165180a6d20aa71bfc78d5984396f'
KERNEL_PATH = Path('orbittrace_density_synchronous_recurrent_eom_v1/density_synchronous_eom.py')
KERNEL_BLOB = '587a304f451e41b9503272f1783a6c6ebb295000'


def git_blob(path: Path) -> str:
    return subprocess.check_output(['git', 'hash-object', str(path)], text=True).strip()


def verify_frozen_sources() -> None:
    if git_blob(PARENT_PATH) != PARENT_BLOB:
        raise RuntimeError('promoted-parent runner blob changed')
    if git_blob(SUCCESSOR_PATH) != SUCCESSOR_BLOB:
        raise RuntimeError('density-synchronous scientific runner blob changed')
    if git_blob(KERNEL_PATH) != KERNEL_BLOB:
        raise RuntimeError('density-synchronous kernel blob changed')


def preload_parent() -> ModuleType:
    verify_frozen_sources()
    spec = importlib.util.spec_from_file_location('run_development', PARENT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError('failed to construct explicit promoted-parent module spec')
    module = importlib.util.module_from_spec(spec)
    sys.modules['run_development'] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        if sys.modules.get('run_development') is module:
            del sys.modules['run_development']
        raise
    resolved = Path(module.__file__).resolve()
    expected = PARENT_PATH.resolve()
    if resolved != expected:
        raise RuntimeError(f'run_development resolved to wrong source: {resolved} != {expected}')
    if sys.modules.get('run_development') is not module:
        raise RuntimeError('explicit promoted-parent module was replaced during preload')
    return module


def main() -> int:
    parent = preload_parent()
    # Required inherited constants are checked before entering the unchanged successor runner.
    if tuple(parent.YEARS) != (2022, 2023):
        raise RuntimeError(f'promoted-parent YEARS changed: {parent.YEARS!r}')
    if tuple(float(x) for x in parent.BLIND) != (20.0, 55.0):
        raise RuntimeError(f'promoted-parent BLIND changed: {parent.BLIND!r}')
    if int(parent.MIN_CLUSTER_SIZE) != 10 or int(parent.MIN_SAMPLES) != 10:
        raise RuntimeError('promoted-parent HDBSCAN size constants changed')
    runpy.run_path(str(SUCCESSOR_PATH), run_name='__main__')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
