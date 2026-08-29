#!/usr/bin/env python3
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
from astropy.io import fits

BASE = "https://irsa.ipac.caltech.edu/data/Euclid/q2/data"
FILE0 = "EUC_VIS_SWL-DET-067070-00-1__20250621T020155.487037Z_sci.fits"
URL = f"{BASE}/{FILE0}"
OUT = Path("results/euclid_remote_probe.json")


def main():
    t0=time.time(); out={"url":URL,"success":False}
    try:
        with fits.open(URL, mode="readonly", memmap=False, lazy_load_hdus=True,
                       use_fsspec=True,
                       fsspec_kwargs={"block_size": 1024*1024, "cache_type":"readahead"}) as hdul:
            out["hdu_count"]=len(hdul); out["hdus"]=[]; image_i=None
            for i,h in enumerate(hdul):
                shape=getattr(h,"shape",None)
                e={"index":i,"class":h.__class__.__name__,"shape":list(shape) if shape else None,
                   "extname":h.header.get("EXTNAME"),"naxis1":h.header.get("NAXIS1"),"naxis2":h.header.get("NAXIS2"),
                   "date_obs":h.header.get("DATE-OBS"),"mjd_obs":h.header.get("MJD-OBS"),"exptime":h.header.get("EXPTIME")}
                out["hdus"].append(e)
                if image_i is None and shape and len(shape)==2 and min(shape)>=64: image_i=i
            if image_i is None: raise RuntimeError("no image HDU")
            h=hdul[image_i]; ny,nx=h.shape; cy,cx=ny//2,nx//2
            a=np.asarray(h.section[cy-32:cy+32,cx-32:cx+32],dtype=float)
            out["sample"]={"hdu_index":image_i,"shape":list(a.shape),"finite_fraction":float(np.isfinite(a).mean()),
                           "median":float(np.nanmedian(a)),"mad":float(np.nanmedian(np.abs(a-np.nanmedian(a)))),
                           "min":float(np.nanmin(a)),"max":float(np.nanmax(a))}
            out["success"]=True
    except Exception as e:
        out["error"]=f"{type(e).__name__}: {e}"
        raise
    finally:
        out["elapsed_seconds"]=round(time.time()-t0,3); OUT.parent.mkdir(exist_ok=True)
        OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
        print(json.dumps(out,indent=2,sort_keys=True))

if __name__=='__main__': main()
