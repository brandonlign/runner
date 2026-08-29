#!/usr/bin/env python3
"""5XMM-DR15 reprocessing-only novelty probe.

Goal: quantify sources recovered by the new DR15 spectrum-based processing from
observations already available to 4XMM-DR14, without looking up or emitting source
names. This is a feasibility/novelty gate, not a discovery run.
"""
from pathlib import Path
import json, urllib.request
import numpy as np
from astropy.io import fits
from astropy.coordinates import SkyCoord
from astropy.time import Time
import astropy.units as u

U5='https://heasarc.gsfc.nasa.gov/FTP/xmm/data/catalogues/5XMM_DR15cat_v1.0.fits.gz'
U4='https://heasarc.gsfc.nasa.gov/FTP/xmm/data/catalogues/4XMM_DR14cat_v1.0.fits.gz'
P5=Path('/tmp/5XMM_DR15cat_v1.0.fits.gz'); P4=Path('/tmp/4XMM_DR14cat_v1.0.fits.gz')
OUT=Path('results/xmm_dr15_reprocessing_probe.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
CUTOFF_MJD=float(Time('2023-12-31T23:59:59',scale='utc').mjd)

def save(x): OUT.write_text(json.dumps(x,indent=2,sort_keys=True,default=str)+'\n'); print(json.dumps(x,indent=2,sort_keys=True,default=str))
def dl(url,p):
    if p.exists() and p.stat().st_size>50_000_000:return
    req=urllib.request.Request(url,headers={'User-Agent':'ISEF-5XMM-reprocessing-probe/1.0'})
    with urllib.request.urlopen(req,timeout=180) as r,p.open('wb') as f:
        while True:
            b=r.read(8*1024*1024)
            if not b:break
            f.write(b)
def table(path):
    h=fits.open(path,memmap=True); tabs=[x for x in h if isinstance(x,(fits.BinTableHDU,fits.TableHDU)) and x.data is not None]; t=max(tabs,key=lambda x:len(x.data)); return h,t,t.data,list(t.data.names)
def pick(names,*opts):
    m={x.upper():x for x in names}
    for o in opts:
        if o.upper() in m:return m[o.upper()]
    return None
def farr(d,n): return np.asarray(d[n],dtype=float)
def end_mjd(a):
    a=np.asarray(a)
    if np.issubdtype(a.dtype,np.number):
        z=a.astype(float); med=float(np.nanmedian(z[np.isfinite(z)]))
        if 40000<med<100000:return z,'mjd'
        if 2.4e6<med<2.6e6:return z-2400000.5,'jd'
        return None,f'unrecognized_numeric_median_{med}'
    out=np.full(len(a),np.nan)
    for i,x in enumerate(a):
        try:
            s=x.decode(errors='replace').strip() if isinstance(x,(bytes,np.bytes_)) else str(x).strip()
            if s:out[i]=Time(s,scale='utc').mjd
        except:pass
    return out,'string_time'
def uniq4(d,names,ra,dec):
    sid=pick(names,'SRCID','SC_SRCID','IAUNAME')
    r=farr(d,ra); q=farr(d,dec); ok=np.isfinite(r)&np.isfinite(q)
    if sid:
        ids=np.asarray(d[sid]); _,idx=np.unique(ids[ok],return_index=True); base=np.where(ok)[0][idx]; return r[base],q[base],sid,len(base)
    return r[ok],q[ok],None,int(ok.sum())
def main():
    try:dl(U5,P5); dl(U4,P4)
    except Exception as e:return save({'success':False,'stage':'download','error':f'{type(e).__name__}: {e}'})
    h5=h4=None
    try:
        h5,t5,d5,n5=table(P5); h4,t4,d4,n4=table(P4)
        c5={
          'ra':pick(n5,'SC_RA','RA'), 'dec':pick(n5,'SC_DEC','DEC'), 'flag':pick(n5,'SC_SUM_FLAG','SUM_FLAG'),
          'extent':pick(n5,'SC_EXTENT','EXTENT'), 'end':pick(n5,'END_TIME'), 'detml':pick(n5,'SC_DET_ML','EP_DET_ML','DET_ML'),
          'hr1':pick(n5,'EP_HR1'), 'hr2':pick(n5,'EP_HR2'), 'hr3':pick(n5,'EP_HR3'), 'hr4':pick(n5,'EP_HR4'),
          'flux':pick(n5,'EP_FLUX','SC_EP_8_FLUX'), 'var':pick(n5,'APPROX_SOURCE_VAR'), 'classx_outlier':pick(n5,'CLASSX_OUTLIER')}
        r4=pick(n4,'SC_RA','RA'); q4=pick(n4,'SC_DEC','DEC')
        required=['ra','dec','flag','extent','end']
        if any(c5[x] is None for x in required) or r4 is None or q4 is None:
            return save({'success':False,'stage':'semantics','five_columns':n5,'four_columns':n4,'resolved5':c5,'resolved4':{'ra':r4,'dec':q4}})
        ra5=farr(d5,c5['ra']); de5=farr(d5,c5['dec']); flag=farr(d5,c5['flag']); ext=farr(d5,c5['extent'])
        emjd,emode=end_mjd(d5[c5['end']])
        if emjd is None:return save({'success':False,'stage':'time_semantics','end_column':c5['end'],'mode':emode})
        clean=np.isfinite(ra5)&np.isfinite(de5)&np.isfinite(flag)&(flag<3)&np.isfinite(ext)&(ext==0)&np.isfinite(emjd)&(emjd<=CUTOFF_MJD)
        if c5['detml']:
            ml=farr(d5,c5['detml']); clean &= np.isfinite(ml)&(ml>=15)
        idx5=np.where(clean)[0]
        ra4,de4,sid4,n4u=uniq4(d4,n4,r4,q4)
        sc4=SkyCoord(ra4*u.deg,de4*u.deg); sc5=SkyCoord(ra5[idx5]*u.deg,de5[idx5]*u.deg)
        _,sep,_=sc5.match_to_catalog_sky(sc4); sec=sep.arcsec
        counts={str(x):int(np.sum(sec>x)) for x in (2,3,5,7,10,15)}
        # Conservative reprocessing-only cohort uses no 4XMM source within 10 arcsec.
        orphan_idx=idx5[sec>10]
        out={'success':True,'decision':'REPROCESSING_COHORT_EXISTS' if len(orphan_idx)>=100 else 'REPROCESSING_COHORT_SMALL',
             'five_rows':len(d5),'four_rows':len(d4),'four_unique_sources':n4u,'old_epoch_clean_pointlike_5xmm':len(idx5),
             'unmatched_counts_by_radius_arcsec':counts,'conservative_unmatched_10arcsec':len(orphan_idx),
             'cutoff_mjd':CUTOFF_MJD,'end_time_mode':emode,'resolved5':c5,'four_id_column':sid4,
             'note':'No 5XMM source names or external identity services are emitted or queried.'}
        for key in ('hr1','hr2','hr3','hr4','flux','var','classx_outlier'):
            if c5[key]:
                z=farr(d5,c5[key])[orphan_idx]; z=z[np.isfinite(z)]
                if len(z):out[f'{key}_summary']={'n':len(z),'median':float(np.median(z)),'q05':float(np.quantile(z,.05)),'q95':float(np.quantile(z,.95)),'min':float(np.min(z)),'max':float(np.max(z))}
        # Anonymous deterministic high-information slices for later preregistration.
        anon=[]
        var=farr(d5,c5['var']) if c5['var'] else np.full(len(d5),np.nan)
        ol=farr(d5,c5['classx_outlier']) if c5['classx_outlier'] else np.full(len(d5),np.nan)
        hr1=farr(d5,c5['hr1']) if c5['hr1'] else np.full(len(d5),np.nan); hr4=farr(d5,c5['hr4']) if c5['hr4'] else np.full(len(d5),np.nan)
        score=np.nan_to_num(ol[orphan_idx],nan=0.0)+np.log10(np.maximum(np.nan_to_num(var[orphan_idx],nan=1.0),1.0))
        order=orphan_idx[np.argsort(score)[::-1]]
        for i in order[:100]:anon.append({'row_index':int(i),'classx_outlier':None if not np.isfinite(ol[i]) else float(ol[i]),'var':None if not np.isfinite(var[i]) else float(var[i]),'hr1':None if not np.isfinite(hr1[i]) else float(hr1[i]),'hr4':None if not np.isfinite(hr4[i]) else float(hr4[i])})
        out['anonymous_top_information_tail']=anon
        save(out)
    except Exception as e:save({'success':False,'stage':'analysis','error':f'{type(e).__name__}: {e}'})
    finally:
        try:
            if h5:h5.close()
            if h4:h4.close()
        except:pass
if __name__=='__main__':main()
