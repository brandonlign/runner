#!/usr/bin/env python3
"""Fast catalog-only Stage 0 for 5XMM-DR15 using HEASARC TAP.

This replaces the failed full 2.4-GB FITS download. It retrieves only the
source-level rows with significant published long-term variability, then applies
predeclared quality cuts locally. It intentionally does not emit source names or
perform external identity/literature lookups.
"""
from __future__ import annotations
import io, json, math, urllib.parse, urllib.request
from pathlib import Path
import numpy as np
from astropy.table import Table

TAP='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync'
OUT=Path('results/xmm_dr15_stage0_tap.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
QUERY='''SELECT ra,dec,approx_source_var,sum_flag,n_contrib,n_obs,extent,stack_det_ml,stack_flux,stack_gamma,stack_nh FROM xmmssc WHERE approx_source_var >= 5 AND n_contrib >= 2'''

def post_adql(q:str):
    data=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','QUERY':q}).encode()
    req=urllib.request.Request(TAP,data=data,headers={'Content-Type':'application/x-www-form-urlencoded','User-Agent':'ISEF-5XMM-DR15-stage0-tap/1.1'})
    with urllib.request.urlopen(req,timeout=180) as r: raw=r.read()
    text=raw.decode('utf-8','replace')
    if 'QUERY_STATUS' in text[:6000] and 'value="ERROR"' in text[:6000]: raise RuntimeError(text[:6000])
    tab=Table.read(io.BytesIO(raw),format='votable')
    rows=[]
    for rr in tab:
        z={str(n).lower():('' if np.ma.is_masked(rr[n]) else rr[n]) for n in tab.colnames}
        rows.append(z)
    return rows

def f(x):
    try:
        y=float(x)
        return y if math.isfinite(y) else None
    except Exception:return None

def quantile(a,p):
    if not a:return None
    b=sorted(a); k=(len(b)-1)*p; lo=int(math.floor(k)); hi=int(math.ceil(k))
    if lo==hi:return b[lo]
    return b[lo]*(hi-k)+b[hi]*(k-lo)

def save(o):
    OUT.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
    print(json.dumps(o,indent=2,sort_keys=True))

def main():
    try:rows=post_adql(QUERY)
    except Exception as e:return save({'success':False,'stage':'tap','error':f'{type(e).__name__}: {e}','query':QUERY})
    parsed=[]
    for z in rows:
        v=f(z.get('approx_source_var')); flag=f(z.get('sum_flag')); nc=f(z.get('n_contrib')); ext=f(z.get('extent'))
        if None in (v,flag,nc,ext):continue
        parsed.append({'v':v,'flag':flag,'nc':nc,'ext':ext,'ra':f(z.get('ra')),'dec':f(z.get('dec')),
                       'nobs':f(z.get('n_obs')),'ml':f(z.get('stack_det_ml')),'flux':f(z.get('stack_flux')),
                       'gamma':f(z.get('stack_gamma')),'nh':f(z.get('stack_nh'))})
    clean=[r for r in parsed if r['flag']<3 and r['nc']>=2 and r['ext']==0]
    veryclean=[r for r in clean if r['flag']==0]
    thresholds=(5,10,20,30,50,100,300,1000,3000,10000)
    counts={str(t):sum(r['v']>=t for r in clean) for t in thresholds}
    counts0={str(t):sum(r['v']>=t for r in veryclean) for t in thresholds}
    vals=[r['v'] for r in clean]
    top=[]
    for r in sorted(clean,key=lambda x:x['v'],reverse=True)[:100]:
        top.append({'var':r['v'],'sum_flag':r['flag'],'n_contrib':r['nc'],'n_obs':r['nobs'],'stack_det_ml':r['ml'],
                    'stack_flux':r['flux'],'stack_gamma':r['gamma'],'stack_nh':r['nh'],
                    'ra_bin_0p1deg':None if r['ra'] is None else round(r['ra'],1),
                    'dec_bin_0p1deg':None if r['dec'] is None else round(r['dec'],1)})
    out={'success':True,'tap':TAP,'query':QUERY,'tap_rows':len(rows),'parsed_rows':len(parsed),
         'clean_point_sources':len(clean),'veryclean_point_sources':len(veryclean),
         'threshold_counts_sumflag_lt3':counts,'threshold_counts_sumflag_eq0':counts0,
         'variability_quantiles':{str(q):quantile(vals,q) for q in (0.5,0.9,0.95,0.99,0.995,0.999)},
         'top_tail_anonymous':top,
         'decision':'TAIL_EXISTS' if counts['30']>=20 and counts['100']>=3 else 'TAIL_TOO_SMALL',
         'note':'No source names or external identity services were used; coordinates are coarsened in emitted diagnostics.'}
    save(out)
if __name__=='__main__':main()
