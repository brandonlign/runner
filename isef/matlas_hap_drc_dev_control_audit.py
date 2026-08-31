#!/usr/bin/env python3
"""Open only the three pre-frozen HAP/DRC development controls.

No stream detector is run. Record only product/header/footprint/noise diagnostics
needed to establish whether these excluded fields are suitable matched real
backgrounds. Published 74 targets and two frozen final-null controls are barred.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np, requests
from astropy.io import fits
from astroquery.mast import Observations
from scipy.ndimage import gaussian_filter

OUT=Path('results/matlas_hap_drc_dev_control_audit'); OUT.mkdir(parents=True,exist_ok=True)
DL=OUT/'download'; DL.mkdir(exist_ok=True)
PROGRAMS=('16257','16711','16082')
DEV=('MATLAS-991','MATLAS-40','MATLAS-332')
FINAL_NULL={'MATLAS-659','MATLAS-254'}
PUBLISHED=set('''MATLAS-42 MATLAS-49 MATLAS-138 MATLAS-141 MATLAS-149 MATLAS-177 MATLAS-203 MATLAS-207 MATLAS-262 MATLAS-290 MATLAS-342 MATLAS-347 MATLAS-365 MATLAS-368 MATLAS-401 MATLAS-405 MATLAS-478 MATLAS-524 MATLAS-585 MATLAS-627 MATLAS-658 MATLAS-682 MATLAS-787 MATLAS-791 MATLAS-799 MATLAS-898 MATLAS-976 MATLAS-984 MATLAS-987 MATLAS-1059 MATLAS-1154 MATLAS-1174 MATLAS-1216 MATLAS-1225 MATLAS-1262 MATLAS-1302 MATLAS-1321 MATLAS-1332 MATLAS-1400 MATLAS-1408 MATLAS-1412 MATLAS-1413 MATLAS-1437 MATLAS-1470 MATLAS-1485 MATLAS-1530 MATLAS-1534 MATLAS-1539 MATLAS-1545 MATLAS-1550 MATLAS-1558 MATLAS-1577 MATLAS-1589 MATLAS-1616 MATLAS-1618 MATLAS-1630 MATLAS-1647 MATLAS-1662 MATLAS-1667 MATLAS-1740 MATLAS-1779 MATLAS-1794 MATLAS-1801 MATLAS-1865 MATLAS-1888 MATLAS-1907 MATLAS-1938 MATLAS-1975 MATLAS-1985 MATLAS-2019 MATLAS-2021 MATLAS-2069 MATLAS-2176 MATLAS-2184'''.split())
assert len(PUBLISHED)==74 and not (set(DEV)&PUBLISHED) and not (set(DEV)&FINAL_NULL)

def rsig(a):
    a=np.asarray(a,float);a=a[np.isfinite(a)];m=np.median(a);return max(1.4826*np.median(np.abs(a-m)),1e-30)

def choose(target):
    rows=[]
    for program in PROGRAMS:
        obsall=Observations.query_criteria(obs_collection='HST',proposal_id=program,instrument_name='ACS/WFC')
        mask=np.array([(str(r['target_name'])==target and str(r['filters']).upper()=='F814W') for r in obsall],bool)
        obs=obsall[mask]
        if not len(obs):continue
        for r in obs:
            if str(r['target_name']) in PUBLISHED or str(r['target_name']) in FINAL_NULL: raise RuntimeError('BARRIER BREACH')
        prod=Observations.get_product_list(obs)
        for r in prod:
            fn=str(r['productFilename']) if 'productFilename' in prod.colnames else ''
            sub=str(r['productSubGroupDescription']) if 'productSubGroupDescription' in prod.colnames else ''
            if sub.upper()!='DRC' or not fn.endswith('_drc.fits') or not fn.startswith('hst_') or '_acs_wfc_f814w_' not in fn or 'skycell' in fn:continue
            rows.append({'program':program,'filename':fn,'dataURI':str(r['dataURI']),'size':int(r['size']) if r['size'] is not None else None})
    rows={x['filename']:x for x in rows}.values(); rows=sorted(rows,key=lambda x:(len(x['filename']),x['filename']))
    if not rows:raise RuntimeError(f'No HAP DRC for {target}')
    return rows[0],rows

def download(r):
    p=DL/r['filename']
    with requests.get('https://mast.stsci.edu/api/v0.1/Download/file',params={'uri':r['dataURI']},stream=True,timeout=(20,180)) as q:
        q.raise_for_status()
        with p.open('wb') as f:
            for c in q.iter_content(1024*1024):
                if c:f.write(c)
    return p

def audit(path):
    with fits.open(path,memmap=False) as h:
        idx=next((i for i,x in enumerate(h) if getattr(x,'data',None) is not None and np.ndim(x.data)==2),None)
        if idx is None:raise RuntimeError('no 2D science')
        a=np.asarray(h[idx].data,np.float32); hdr=h[idx].header; ph=h[0].header
    finite=np.isfinite(a)
    zero=(a==0)&finite
    valid=finite.copy()
    if zero.mean()>0.005:
        valid &= ~zero
    med=float(np.median(a[valid]));fill=np.where(valid,a,med).astype(np.float32);res=fill-gaussian_filter(fill,32,mode='nearest')
    return {'shape':list(a.shape),'science_hdu':idx,'exptime_s':hdr.get('EXPTIME',ph.get('EXPTIME')),'bunit':hdr.get('BUNIT',ph.get('BUNIT')),
            'finite_fraction':float(finite.mean()),'valid_fraction':float(valid.mean()),'raw_median':med,'broad32_residual_robust_sigma':float(rsig(res[valid]))}

def main():
    rep={'role':'development-control acquisition/noise audit only','published74_science_values_opened':False,'final_null_science_values_opened':False,'controls':[]}
    for t in DEV:
        print('CONTROL',t,flush=True); chosen,rows=choose(t); p=download(chosen); st=audit(p); p.unlink(missing_ok=True)
        rep['controls'].append({'target':t,'chosen':chosen,'candidates':[x['filename'] for x in rows],'stats':st})
    ex=[float(x['stats']['exptime_s']) for x in rep['controls']]
    rep['summary']={'n':len(rep['controls']),'exptime_min_s':min(ex),'exptime_max_s':max(ex),'valid_fraction_min':min(x['stats']['valid_fraction'] for x in rep['controls'])}
    (OUT/'report.json').write_text(json.dumps(rep,indent=2,sort_keys=True,default=str)+'\n');print(json.dumps(rep['summary'],indent=2,sort_keys=True))
if __name__=='__main__':main()
