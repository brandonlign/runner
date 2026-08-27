#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('p13_p12_transport_v1',HERE/'apply_p12_matched_transport_patch.py')
if spec is None or spec.loader is None:
    raise RuntimeError('cannot load P13 P12 transport v1')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
_original_replace_span=m.replace_span


def replace_span_v2(text:str,start:str,end:str,replacement:str,label:str)->str:
    if label=='panel universe replacement':
        anchor='    orbit_by_id = {str(k):v for k,v in panel_input["orbit_by_id"].items()}\n'
        require_count=replacement.count(anchor)
        if require_count!=1:
            raise RuntimeError(f'P13 P12 transport v2 orbit anchor count={require_count}')
        replacement=replacement.replace(
            anchor,
            anchor+'    event_lookup_by_year = {year:{str(e["id"]):e for e in scan_by_year[year]} for year in YEARS}\n',
            1,
        )
    return _original_replace_span(text,start,end,replacement,label)

m.replace_span=replace_span_v2


def main()->int:
    old=sys.argv
    sys.argv=[str(HERE/'apply_p12_matched_transport_patch.py'),*old[1:]]
    try:
        return int(m.main())
    finally:
        sys.argv=old


if __name__=='__main__':
    raise SystemExit(main())
