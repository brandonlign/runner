#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import runpy
import subprocess
import sys
from pathlib import Path

PARENT_PATH = Path('orbittrace_recurrent_eom_hdbscan_v1/run_development.py')
SUCCESSOR_PATH = Path('orbittrace_density_sync_global_whitened_geo6_v1/run_development.py')
PARENT_BLOB = 'fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c'
SUCCESSOR_BLOB = '786298ed3ae1768572bb355081fc49f10405a578'
SYNC_KERNEL_PATH = Path('orbittrace_density_synchronous_recurrent_eom_v1/density_synchronous_eom.py')
SYNC_KERNEL_BLOB = '587a304f451e41b9503272f1783a6c6ebb295000'


def blob(path: Path) -> str:
    return subprocess.check_output(['git', 'hash-object', str(path)], text=True).strip()


def main() -> int:
    if blob(PARENT_PATH) != PARENT_BLOB:
        raise RuntimeError('parent runner changed')
    if blob(SUCCESSOR_PATH) != SUCCESSOR_BLOB:
        raise RuntimeError('successor runner changed')
    if blob(SYNC_KERNEL_PATH) != SYNC_KERNEL_BLOB:
        raise RuntimeError('density-synchronous kernel changed')
    spec = importlib.util.spec_from_file_location('run_development', PARENT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError('cannot preload parent')
    module = importlib.util.module_from_spec(spec)
    sys.modules['run_development'] = module
    spec.loader.exec_module(module)
    if Path(module.__file__).resolve() != PARENT_PATH.resolve():
        raise RuntimeError('wrong parent module resolved')
    runpy.run_path(str(SUCCESSOR_PATH), run_name='__main__')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
