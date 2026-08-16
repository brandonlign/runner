#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

BASE=Path(__file__).with_name('generate_prelabel.py')
spec=importlib.util.spec_from_file_location('orbf_direct_base',BASE)
if spec is None or spec.loader is None:
    raise RuntimeError('cannot import frozen direct prelabel generator')
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
_original=mod.load_sparse_geometry

def load_sparse_geometry(manifest):
    events=_original(manifest)
    # The frozen recurrent-EOM/#1284 normalization consumes `sun_lon`, not raw
    # geocentric ecliptic longitude. The monthly catalogue provides LAMgeo and
    # solar longitude, so reconstruct the same Sun-centered coordinate exactly.
    for e in events:
        e['lon']=(float(e['lon'])-float(e['sol']))%360.0
    return events

mod.load_sparse_geometry=load_sparse_geometry

if __name__=='__main__':
    raise SystemExit(mod.main())
