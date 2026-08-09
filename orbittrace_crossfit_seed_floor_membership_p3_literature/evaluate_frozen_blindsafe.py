#!/usr/bin/env python3
"""Provenance-only wrapper for the frozen P3 matched-literature evaluator.

The underlying exact-row runner historically carries the superseded HDBSCAN-2023
assignment digest.  The already-established blind-safe v8/P2 literature lineage
uses 35f629... instead.  This wrapper changes only that accepted provenance digest
at module-load time; it does not change P3, truth, metrics, denominators or gates.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

HERE=Path(__file__).resolve().parent
EXPECTED_BLINDSAFE_HDBSCAN_2023_SHA256='35f629b1dff4d04cdc13aa8224171ec1ab8e06b52836900d66ff978b5c235761'

spec=importlib.util.spec_from_file_location('p3_eval_base',HERE/'evaluate_frozen.py')
if spec is None or spec.loader is None:
    raise RuntimeError('cannot load frozen P3 evaluator')
base=importlib.util.module_from_spec(spec); spec.loader.exec_module(base)
_original_load_module=base.load_module


def load_module_blindsafe(path:Path,name:str)->Any:
    module=_original_load_module(path,name)
    if name=='p3_posttruth_exact':
        current=str(module.ASSIGNMENT_SHA256['hdbscan'][2023])
        if current not in {
            '7dbb920532f7dc429a6cd5961d80d480c5ff53c0122cf6e9ec04638c0730ed60',
            EXPECTED_BLINDSAFE_HDBSCAN_2023_SHA256,
        }:
            raise RuntimeError(f'unexpected HDBSCAN-2023 provenance in exact-row runner: {current}')
        module.ASSIGNMENT_SHA256['hdbscan'][2023]=EXPECTED_BLINDSAFE_HDBSCAN_2023_SHA256
    return module


base.load_module=load_module_blindsafe

if __name__=='__main__':
    raise SystemExit(base.main())
