#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import run_with_parent_import as wrapper

EXPECTED_PARENT = Path('orbittrace_recurrent_eom_hdbscan_v1/run_development.py').resolve()
EXPECTED_SUCCESSOR = Path('orbittrace_density_synchronous_recurrent_eom_v1/run_development.py').resolve()


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def main() -> int:
    wrapper.verify_frozen_sources()
    parent = wrapper.preload_parent()
    req(Path(parent.__file__).resolve() == EXPECTED_PARENT, 'preloaded module is not exact promoted-parent runner')
    req(sys.modules.get('run_development') is parent, 'run_development module identity changed after preload')
    req(tuple(parent.YEARS) == (2022, 2023), f'parent YEARS changed: {parent.YEARS!r}')
    req(tuple(float(x) for x in parent.BLIND) == (20.0, 55.0), f'parent BLIND changed: {parent.BLIND!r}')
    req(int(parent.MIN_CLUSTER_SIZE) == 10, 'parent min_cluster_size changed')
    req(int(parent.MIN_SAMPLES) == 10, 'parent min_samples changed')

    # Import the unchanged successor under a non-__main__ probe name. This executes
    # only module-level definitions; its guarded main() is never entered.
    spec = importlib.util.spec_from_file_location('density_synchronous_successor_import_probe', EXPECTED_SUCCESSOR)
    req(spec is not None and spec.loader is not None, 'failed to construct successor import probe')
    successor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(successor)

    req(successor.parent_runner is parent, 'successor parent_runner did not bind to exact promoted-parent module')
    req(Path(successor.parent_runner.__file__).resolve() == EXPECTED_PARENT, 'successor parent_runner source path is wrong')
    req(tuple(successor.YEARS) == tuple(parent.YEARS), 'successor inherited YEARS differ from parent')
    req(tuple(float(x) for x in successor.BLIND) == tuple(float(x) for x in parent.BLIND), 'successor inherited BLIND differs from parent')
    req(int(successor.MIN_CLUSTER_SIZE) == int(parent.MIN_CLUSTER_SIZE), 'successor inherited min_cluster_size differs')
    req(int(successor.MIN_SAMPLES) == int(parent.MIN_SAMPLES), 'successor inherited min_samples differs')

    # The probe must not have entered main(); no output directory or result/prelabel
    # is created by this audit and no catalogue/network surface is invoked.
    req(successor.__name__ == 'density_synchronous_successor_import_probe', 'successor probe unexpectedly ran as __main__')

    result = {
        'verdict': 'PASS_DENSITY_SYNCHRONOUS_IMPORT_REPAIR_ZERO_DATA_AUDIT',
        'technical_no_result_run': 31852571788,
        'technical_no_result_artifact': 9237971344,
        'technical_no_result_artifact_digest': 'sha256:30ad75c1fde8e7345532557d53ca338035a2ef7948c002d5330dadd620121198',
        'parent_module_path': str(Path(parent.__file__).resolve()),
        'successor_probe_path': str(EXPECTED_SUCCESSOR),
        'parent_module_bound_exactly': True,
        'successor_parent_runner_identity_exact': True,
        'inherited_constants_exact': True,
        'scientific_runner_blob_unchanged': True,
        'scientific_kernel_blob_unchanged': True,
        'scientific_data_access': False,
        'gmn_access': False,
        'sonotaco_access': False,
        'efn_access': False,
        'asfn_access': False,
        'amos_access': False,
        'maarsy_scientific_access': False,
        'dms_scientific_access': False,
        'target_information_access': False,
        'target_region_events_accessed': False,
        'hdbscan_fit_executed': False,
        'hidden_truth_accessed': False,
        'prelabel_created': False,
        'scientific_result_created': False,
    }
    out = Path('output')
    out.mkdir(parents=True, exist_ok=True)
    (out / 'DENSITY_SYNCHRONOUS_IMPORT_REPAIR_ZERO_DATA_AUDIT.json').write_text(
        json.dumps(result, indent=2, sort_keys=True) + '\n'
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
