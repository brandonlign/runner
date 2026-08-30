#!/usr/bin/env python3
import json, urllib.request, io
from pathlib import Path
import numpy as np
from astropy.io import fits

FIELD='112053'; GROUP='112XXX'; CID='63050396111356292'
MJDS=['60334','60660','60665']
BASE='https://data.sdss.org/sas/dr20/spectro/boss/redux/v6_2_1/spectra/daily/full'
OUT=Path('results/sdss_dr20_postsurvivor_template_audit.json'); OUT.parent.mkdir(exist_ok=True)

def py(v):
    if isinstance(v, bytes): return v.decode(errors='replace').strip()
    if isinstance(v, np.ndarray): return [py(x) for x in v.tolist()]
    try: return v.item()
    except Exception: return str(v) if not isinstance(v,(str,int,float,bool,type(None))) else v

def pick(row,names):
    return {n:py(row[n]) for n in names if n in row.array.names}

def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':'ISEF-DR20-TemplateAudit/1.0'})
    with urllib.request.urlopen(req,timeout=180) as r:return r.read()

o={'status':'POSTSURVIVOR_TEMPLATE_SOLUTION_AUDIT','visits':[]}
try:
    for mjd in MJDS:
        fn=f'spec-{FIELD}-{mjd}-{CID}.fits'; url=f'{BASE}/{GROUP}/{FIELD}/{mjd}/{fn}'
        raw=get(url)
        with fits.open(io.BytesIO(raw),memmap=False) as h:
            sp=h['SPALL'].data[0]
            sp_names=['FIELD','MJD','SDSS_ID','GAIA_ID','CLASS','SUBCLASS','Z','Z_ERR','ZWARNING','RCHI2','RCHI2DIFF','TFILE','TCOLUMN','Z_NOQSO','Z_ERR_NOQSO','ZWARNING_NOQSO','CLASS_NOQSO','SUBCLASS_NOQSO','RCHI2DIFF_NOQSO','XCSAO_RV','XCSAO_ERV','XCSAO_RXC','XCSAO_TEFF','XCSAO_ETEFF','XCSAO_LOGG','XCSAO_ELOGG','XCSAO_FEH','XCSAO_EFEH','SN_MEDIAN_ALL']
            spall=pick(sp,sp_names)
            z=h['ZALL'].data
            rows=[]
            for r in z:
                d=pick(r,['CLASS','SUBCLASS','Z','Z_ERR','RCHI2','RCHI2DIFF','TFILE','TCOLUMN','ZWARNING','VDISP','VDISP_ERR'])
                try:d['_rchi2']=float(r['RCHI2'])
                except Exception:d['_rchi2']=float('inf')
                rows.append(d)
            rows.sort(key=lambda x:x['_rchi2'])
            for r in rows:r.pop('_rchi2',None)
            # summarize best solutions around stellar-like z ~0 and around XCSAO RV
            c=299792.458; xrv=float(sp['XCSAO_RV']); xz=xrv/c
            near_zero=sorted(rows,key=lambda r:abs(float(r.get('Z',999))))[:10]
            near_x=sorted(rows,key=lambda r:abs(float(r.get('Z',999))-xz))[:10]
            rec={'mjd':int(mjd),'url':url,'spall':spall,'best_zall_by_rchi2':rows[:15],'nearest_zall_to_zero':near_zero,'nearest_zall_to_xcsao_z':near_x,'zall_n':len(rows)}
            o['visits'].append(rec)
    o['success']=True
except Exception as e:
    o['success']=False;o['error']=type(e).__name__+': '+str(e)
OUT.write_text(json.dumps(o,indent=2,default=str)+'\n');print(json.dumps(o,indent=2,default=str))
