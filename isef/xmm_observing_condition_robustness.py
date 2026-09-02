#!/usr/bin/env python3
"""Frozen observing-condition robustness test for 5XMM archival recoveries.
Implements research/XMM_DR15_OBSERVING_CONDITION_ROBUSTNESS_PREREG_2026-09-01.md.
Aggregate output only; no source identities or coordinates emitted.
"""
from pathlib import Path
from collections import defaultdict
import io,json,urllib.parse,urllib.request,hashlib
import numpy as np
from scipy.stats import mannwhitneyu
from astropy.table import Table,vstack
from astropy.io import fits
from astropy.coordinates import SkyCoord
import astropy.units as u

EP='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync'; CAP=100000
U4='https://heasarc.gsfc.nasa.gov/FTP/xmm/data/catalogues/4XMM_DR14cat_slim_v1.0.fits.gz'
U4OBS='http://xmmssc.irap.omp.eu/Catalogue/4XMM-DR14/4xmmdr14_obslist.fits'
P4=Path('/tmp/4XMM_DR14cat_slim_v1.0.fits.gz'); PO=Path('/tmp/4xmmdr14_obslist.fits')
OUT=Path('results/xmm_observing_condition_robustness.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
BASE='s.sum_flag < 3 AND s.extent=0 AND s.ep_det_ml>=15'

def norm(x):
    if isinstance(x,(bytes,np.bytes_)): x=x.decode('utf-8','replace')
    return str(x).strip()
def fnum(x):
    try:
        v=float(x); return v if np.isfinite(v) else np.nan
    except: return np.nan
def tap(q,timeout=300):
    url=EP+'?'+urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':q})
    req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-condition-robustness/1.0'})
    with urllib.request.urlopen(req,timeout=timeout) as r: raw=r.read()
    return Table.read(io.BytesIO(raw),format='votable')
def dl(url,p):
    req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-condition-robustness/1.0'})
    with urllib.request.urlopen(req,timeout=180) as r,p.open('wb') as f:
        while True:
            b=r.read(8*1024*1024)
            if not b: break
            f.write(b)
def refs():
    if not P4.exists(): dl(U4,P4)
    if not PO.exists(): dl(U4OBS,PO)
    with fits.open(P4,memmap=True) as h:
        d=max([x for x in h if isinstance(x,(fits.BinTableHDU,fits.TableHDU)) and x.data is not None],key=lambda x:len(x.data)).data
        nm={x.upper():x for x in d.names}; ra=np.asarray(d[nm['SC_RA']],float).copy(); de=np.asarray(d[nm['SC_DEC']],float).copy()
    with fits.open(PO,memmap=True) as h:
        d=max([x for x in h if isinstance(x,(fits.BinTableHDU,fits.TableHDU)) and x.data is not None],key=lambda x:len(x.data)).data
        nm={x.upper():x for x in d.names}; old={norm(x) for x in d[nm['OBS_ID']] if norm(x)}
    ok=np.isfinite(ra)&np.isfinite(de); return SkyCoord(ra[ok]*u.deg,de[ok]*u.deg),old

def qbin(lo,hi,depth=0):
    q=f'''SELECT TOP {CAP}
 s.srcid AS sid,s.ra AS sra,s.dec AS sdec,s.ep_flux AS flux,s.ep_det_ml AS detml,
 d.obsid AS dobsid,d.pps_srcnum AS pps,d.ep_offax AS offax,d.ep_ontime AS ontime,
 d.pn_maskfrac AS pnmask,d.m1_maskfrac AS m1mask,d.m2_maskfrac AS m2mask,
 d.pn_bg AS pnbg,d.m1_bg AS m1bg,d.m2_bg AS m2bg
FROM xmmssc AS s JOIN xmmstack AS d ON s.srcid=d.srcid
WHERE {BASE} AND s.ra>={lo:.8f} AND s.ra<{hi:.8f} AND d.pps_srcnum IS NOT NULL'''
    t=tap(q)
    if len(t)>=CAP:
        if depth>=8: raise RuntimeError(f'row cap persists {lo}-{hi}')
        m=(lo+hi)/2; return qbin(lo,m,depth+1)+qbin(m,hi,depth+1)
    return [t]

def condition(row):
    masks=[fnum(row[k]) for k in ('pnmask','m1mask','m2mask')]; masks=[x for x in masks if np.isfinite(x)]
    bgs=[fnum(row[k]) for k in ('pnbg','m1bg','m2bg')]; bgs=[x for x in bgs if np.isfinite(x) and x>0]
    return {'offax':fnum(row['offax']),'ontime':fnum(row['ontime']),
            'mask':max(masks) if masks else np.nan,'bg':float(np.median(bgs)) if bgs else np.nan}
def compatible(a,b):
    if not (np.isfinite(a['offax']) and np.isfinite(b['offax']) and abs(a['offax']-b['offax'])<=2.0): return False
    if not (np.isfinite(a['ontime']) and np.isfinite(b['ontime']) and a['ontime']>0 and b['ontime']>0): return False
    r=b['ontime']/a['ontime']
    if r<0.8 or r>1.25: return False
    if np.isfinite(a['mask']) and np.isfinite(b['mask']) and abs(a['mask']-b['mask'])>0.10: return False
    if np.isfinite(a['bg']) and np.isfinite(b['bg']) and a['bg']>0 and b['bg']>0:
        r=b['bg']/a['bg']
        if r<0.5 or r>2.0: return False
    return True

def summ(v):
    a=np.asarray(v,float); a=a[np.isfinite(a)]
    return {'n':int(len(a)),'median':float(np.median(a)) if len(a) else None,'q25':float(np.quantile(a,.25)) if len(a) else None,'q75':float(np.quantile(a,.75)) if len(a) else None}
def analyze_hemi(c4,old,a,b):
    tabs=[]
    for lo in range(a,b,10):
        tabs.extend(qbin(float(lo),float(lo+10))); print(json.dumps({'query_progress':f'{lo}-{lo+10}'}),flush=True)
    t=vstack(tabs,metadata_conflicts='silent') if len(tabs)>1 else tabs[0]
    props={}; rows=defaultdict(dict); obs=defaultdict(set)
    for row in t:
        s=norm(row['sid']); o=norm(row['dobsid'])
        if s not in props: props[s]={'ra':fnum(row['sra']),'dec':fnum(row['sdec']),'flux':fnum(row['flux']),'detml':fnum(row['detml'])}
        if o and o not in ('--','None','nan'):
            obs[s].add(o)
            # one XMMSTACK row per source/observation is expected; deterministic first row otherwise
            if o not in rows[s]: rows[s][o]=condition(row)
    ids=list(props)
    c=SkyCoord([props[s]['ra'] for s in ids]*u.deg,[props[s]['dec'] for s in ids]*u.deg); _,sep,_=c.match_to_catalog_sky(c4)
    cases=[ids[i] for i in range(len(ids)) if sep.arcsec[i]>20 and any(o in old for o in obs[ids[i]])]
    controls=[ids[i] for i in range(len(ids)) if sep.arcsec[i]<=20 and any(o in old for o in obs[ids[i]])]
    om=defaultdict(list)
    for s in controls:
        for o in obs[s]&old: om[o].append(s)
    baseline_pairs=[]; condition_pairs=[]; used_base=set(); used_cond=set()
    for s in sorted(cases,key=lambda x:hashlib.sha256(x.encode()).hexdigest()):
        cand=set()
        for o in obs[s]&old: cand.update(om.get(o,[]))
        order=sorted(cand,key=lambda x:hashlib.sha256((s+'|'+x).encode()).hexdigest())
        for x in order:
            if x in used_base: continue
            shared=sorted((obs[s]&obs[x]&old))
            if not shared: continue
            o=shared[0]; baseline_pairs.append((s,x,o)); used_base.add(x); break
        for x in order:
            if x in used_cond: continue
            shared=sorted((obs[s]&obs[x]&old))
            if not shared: continue
            o=shared[0]
            ca=rows[s].get(o); cb=rows[x].get(o)
            if ca is None or cb is None: continue
            if compatible(ca,cb): condition_pairs.append((s,x,o)); used_cond.add(x); break
    cond_desc={k:{'case':summ([rows[s][o][k] for s,x,o in baseline_pairs]),'control':summ([rows[x][o][k] for s,x,o in baseline_pairs])} for k in ('offax','ontime','mask','bg')}
    tests={}
    for name,f in [('brightness','flux'),('detection_strength','detml')]:
        aa=np.array([props[s][f] for s,x,o in condition_pairs],float); bb=np.array([props[x][f] for s,x,o in condition_pairs],float)
        ok=np.isfinite(aa)&np.isfinite(bb)&(aa>0)&(bb>0); aa=np.log10(aa[ok]); bb=np.log10(bb[ok])
        p=float(mannwhitneyu(aa,bb,alternative='two-sided').pvalue) if len(aa) else None
        tests[name]={'n_pairs':int(len(aa)),'case_median_log10':float(np.median(aa)) if len(aa) else None,'control_median_log10':float(np.median(bb)) if len(bb) else None,'median_difference':float(np.median(aa)-np.median(bb)) if len(aa) else None,'raw_p':p}
    return {'recoveries':len(cases),'baseline_pairs':len(baseline_pairs),'condition_compatible_pairs':len(condition_pairs),'baseline_condition_distributions':cond_desc,'tests':tests}
def main():
    try:
        c4,old=refs(); d=analyze_hemi(c4,old,0,180); v=analyze_hemi(c4,old,180,360)
        ps=[]; dirs=[]; enough=d['condition_compatible_pairs']>=250 and v['condition_compatible_pairs']>=250
        if enough:
            for r in (d,v):
                for k in ('brightness','detection_strength'):
                    ps.append(r['tests'][k]['raw_p']); dirs.append(r['tests'][k]['median_difference']<0)
        adj=[min(1.0,p*4) for p in ps]
        out={'success':True,'development':d,'validation':v,'bonferroni_four_tests':adj,
             'observing_condition_robust':bool(enough and all(dirs) and all(p<=0.01 for p in adj)),
             'privacy':'Aggregate statistics only; no source identities or coordinates emitted.'}
    except Exception as e: out={'success':False,'error':f'{type(e).__name__}: {e}'}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2,sort_keys=True),flush=True)
if __name__=='__main__': main()
