#!/usr/bin/env python3
"""Uniform native-DRZ audit of all 13 prospectively excluded controls.

Product inventory established that all 13 have exactly one native F814W DRZ.
This script opens only those excluded fields. Published Table-A.1 targets remain
forbidden. No stream detection is performed: only exposure, footprint and
fixed broad-background residual diagnostics are recorded.
"""
from pathlib import Path
import numpy as np
from astroquery.mast import Observations
import matlas_excluded_f814w_background_audit as p


def choose_native_drz(target):
    rows=[]
    for program in p.PROGRAMS:
        allobs=Observations.query_criteria(obs_collection='HST',proposal_id=program,instrument_name='ACS/WFC')
        if not len(allobs):continue
        mask=np.array([(str(r['target_name'])==target and str(r['filters']).upper()=='F814W') for r in allobs],bool)
        obs=allobs[mask]
        if not len(obs):continue
        for r in obs:
            literal=str(r['target_name'])
            if literal in p.PUBLISHED or literal=='MATLAS2019':raise RuntimeError(f'BARRIER BREACH {literal}')
        prod=Observations.get_product_list(obs)
        for r in prod:
            fn=str(r['productFilename']) if 'productFilename' in prod.colnames else ''
            sub=str(r['productSubGroupDescription']) if 'productSubGroupDescription' in prod.colnames else ''
            if sub.upper()=='DRZ' and fn.endswith('_drz.fits') and not fn.startswith('hst_') and 'skycell' not in fn:
                rows.append({'program':program,'filename':fn,'dataURI':str(r['dataURI']),
                    'size':int(r['size']) if 'size' in prod.colnames and r['size'] is not None else None})
    uniq={r['filename']:r for r in rows}
    if len(uniq)!=1:raise RuntimeError(f'Expected exactly one native F814W DRZ for {target}, got {sorted(uniq)}')
    x=next(iter(uniq.values()));return x,[x]

if __name__=='__main__':
    p.OUT=Path('results/matlas_excluded_native_drz_background_audit');p.OUT.mkdir(parents=True,exist_ok=True)
    p.DL=p.OUT/'download';p.DL.mkdir(exist_ok=True)
    p.choose_product=choose_native_drz
    p.main()
