#!/usr/bin/env python3
"""Catalog-only Stage 0 for the ISEF 5XMM-DR15 extreme-variable project.

No SIMBAD/NED/literature lookup of ranked survivors is permitted here. The goal is
only to establish whether a clean, statistically usable extreme-variability tail
exists and whether catalog semantics support a prospective discovery experiment.
"""
from pathlib import Path
import json, urllib.request
import numpy as np
from astropy.io import fits

URL='https://heasarc.gsfc.nasa.gov/FTP/xmm/data/catalogues/5XMM_DR15cat_v1.0.fits.gz'
OUT=Path('results/xmm_dr15_stage0.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
CACHE=Path('/tmp/5XMM_DR15cat_v1.0.fits.gz')

def save(x):
    OUT.write_text(json.dumps(x,indent=2,sort_keys=True,default=str)+'\n')
    print(json.dumps(x,indent=2,sort_keys=True,default=str))

def download():
    if CACHE.exists() and CACHE.stat().st_size>100_000_000:return
    req=urllib.request.Request(URL,headers={'User-Agent':'ISEF-5XMM-DR15-stage0/1.0'})
    with urllib.request.urlopen(req,timeout=120) as r, CACHE.open('wb') as f:
        while True:
            b=r.read(8*1024*1024)
            if not b:break
            f.write(b)

def col(names,*opts):
    m={n.upper():n for n in names}
    for o in opts:
        if o.upper() in m:return m[o.upper()]
    return None

def arr(d,n): return np.asarray(d[n])

def main():
    try:download()
    except Exception as e:return save({'success':False,'stage':'download','error':f'{type(e).__name__}: {e}','url':URL})
    try:
        with fits.open(CACHE,memmap=True) as h:
            # Find the largest binary table, expected to be the source-level catalog.
            tabs=[x for x in h if isinstance(x,(fits.BinTableHDU,fits.TableHDU)) and x.data is not None]
            t=max(tabs,key=lambda x:len(x.data)); d=t.data; names=list(d.names)
            found={
              'iauname':col(names,'IAUNAME'), 'srcid':col(names,'SRCID'),
              'sum_flag':col(names,'SC_SUM_FLAG','SUM_FLAG'),
              'extent':col(names,'SC_EXTENT','EXTENT'),
              'n_contrib':col(names,'N_CONTRIB','N_DETECTIONS'),
              'n_obs':col(names,'N_OBS'),
              'var':col(names,'APPROX_SOURCE_VAR','SC_VAR_FLAG','VAR_FACTOR','VAR_RATIO'),
              'flux':col(names,'EP_FLUX','SC_EP_8_FLUX','SC_EP_FLUX'),
              'det_ml':col(names,'SC_DET_ML','DET_ML'),
              'classx':col(names,'CLASSX_CLASS'),
              'classx_outlier':col(names,'CLASSX_OUTLIER'),
            }
            summary={'success':True,'url':URL,'hdu':t.name,'rows':len(d),'columns':names,'resolved_columns':found}
            required=['sum_flag','n_contrib','var']
            if any(found[k] is None for k in required):
                summary['decision']='SEMANTICS_BLOCKED'
                summary['missing_required']=[k for k in required if found[k] is None]
                return save(summary)
            flag=arr(d,found['sum_flag']).astype(float); nc=arr(d,found['n_contrib']).astype(float); v=arr(d,found['var']).astype(float)
            clean=np.isfinite(flag)&(flag<3)&np.isfinite(nc)&(nc>=2)&np.isfinite(v)&(v>0)
            if found['extent']:
                ext=arr(d,found['extent']).astype(float); clean &= np.isfinite(ext)&(ext==0)
            counts={}
            for th in (5,10,20,30,50,100,300,1000): counts[str(th)]=int(np.sum(clean&(v>=th)))
            vals=v[clean]
            summary['clean_multiply_observed_count']=int(clean.sum())
            summary['variability_threshold_counts']=counts
            summary['variability_quantiles']={str(q):float(np.nanquantile(vals,q)) for q in (0.5,0.9,0.95,0.99,0.995,0.999)} if len(vals) else {}
            # Catalog-only top tail for later blinded routing; names are intentionally not emitted.
            idx=np.where(clean)[0]; order=idx[np.argsort(v[idx])[::-1]]
            top=[]
            for i in order[:100]:
                r={'row_index':int(i),'var':float(v[i]),'sum_flag':float(flag[i]),'n_contrib':float(nc[i])}
                for k in ('flux','det_ml','classx_outlier'):
                    if found[k]:
                        try:r[k]=float(d[found[k]][i])
                        except:pass
                if found['classx']:
                    x=d[found['classx']][i]; r['classx']=x.decode(errors='replace').strip() if isinstance(x,(bytes,np.bytes_)) else str(x).strip()
                top.append(r)
            summary['top_tail_anonymous']=top
            summary['decision']='TAIL_EXISTS' if counts['30']>=20 and counts['100']>=3 else 'TAIL_TOO_SMALL'
            summary['note']='No source names or external identity services were used to choose the tail.'
            save(summary)
    except Exception as e:save({'success':False,'stage':'fits','error':f'{type(e).__name__}: {e}'})

if __name__=='__main__':main()
