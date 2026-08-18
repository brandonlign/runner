#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
from pathlib import Path
from typing import Any


def _load_parent() -> Any:
    path=Path(__file__).resolve().parents[1]/'orbittrace_recurrent_eom_hdbscan_v1'/'run_development.py'
    spec=importlib.util.spec_from_file_location('dag_atom_repair01_exact_parent',path)
    if spec is None or spec.loader is None: raise RuntimeError(f'cannot import exact parent {path}')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

_PARENT=_load_parent()
normalize_event=_PARENT.normalize_event


def metrics(pooled:list[dict[str,Any]],hidden:dict[str,str],annual_ids:set[str])->dict[str,Any]:
    adapted=[]
    for row in pooled:
        if 'family_id' in row:
            adapted.append(row)
            continue
        if 'atom_hash' not in row: raise RuntimeError('missing family_id on non-atom candidate')
        x=dict(row);x['family_id']='DAGATOM1:'+str(row['atom_hash']);adapted.append(x)
    return _PARENT.metrics(adapted,hidden,annual_ids)
