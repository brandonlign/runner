#!/usr/bin/env python3
"""Probe target-blind HTTP-range cutout access on a 2025 PUNCH CTM file."""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import requests
from astropy.io import fits

ROOT="https://umbra.nascom.nasa.gov/punch/2/CTM/2025/09/21/"
FILE_RE=re.compile(r'href=["\'](PUNCH_L2_CTM_(20250921\d{6})_v0l\.fits)["\']',re.I)
OUT=Path("results/punch_kh_remote_cutout_probe");OUT.mkdir(parents=True,exist_ok=True)


def main():
    r=requests.get(ROOT,timeout=(10,30));r.raise_for_status()
    files=sorted({name for name,_ in FILE_RE.findall(r.text)})
    if not files: raise RuntimeError("no v0l controls")
    name=files[len(files)//2];url=ROOT+name
    with fits.open(url,use_fsspec=True,fsspec_kwargs={"block_size":1024*1024},memmap=False) as hdul:
        shape=tuple(hdul[1].shape)
        cy,cx=2048,2048+850
        y0,y1=cy-40,cy+41;x0,x1=cx-160,cx+161
        cut=np.asarray(hdul[1].section[y0:y1,x0:x1],float)
    report={"information_barrier":"single 2025-09-21 non-R3 CTM cutout only","file":name,"full_shape":shape,
            "cutout_shape":list(cut.shape),"finite_fraction":float(np.isfinite(cut).mean()),
            "median":float(np.nanmedian(cut)),"mad":float(np.nanmedian(np.abs(cut-np.nanmedian(cut))))}
    (OUT/"summary.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(report,indent=2,sort_keys=True));return 0

if __name__=="__main__":raise SystemExit(main())
