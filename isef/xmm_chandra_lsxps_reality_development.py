#!/usr/bin/env python3
"""Pre-result-frozen development external-reality test for strict 5XMM recoveries.
Uses Chandra CSC 2.1.1 + contemporary Swift LSXPS real-vs-shift enrichment. Aggregate only."""
from pathlib import Path
from collections import defaultdict
import io,json,urllib.parse,urllib.request
import numpy as np
from scipy.stats import fisher_exact
from astropy.table import Table,vstack
from astropy.io import fits
from astropy.coordinates import SkyCoord
import astropy.units as u
EP='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync'; CAP=100000; PAD=.01; RCSC=5.; RSWIFT=10.
U4='https://heasarc.gsfc.nasa.gov/FTP/xmm/data/catalogues/4XMM_DR14cat_slim_v1.0.fits.gz'; U4OBS='http://xmmssc.irap.omp.eu/Catalogue/4XMM-DR14/4xmmdr14_obslist.fits'
P4=Path('/tmp/4XMM_DR14cat_slim_v1.0.fits.gz'); P4OBS=Path('/tmp/4xmmdr14_obslist.fits'); OUT=Path('results/xmm_chandra_lsxps_reality_development.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
BASE='s.sum_flag < 2 AND s.extent = 0 AND s.ep_det_ml >= 15'
def norm(x):
 if isinstance(x,(bytes,np.bytes_)): x=x.decode('utf-8','replace')
 return str(x).strip()
def tap(q,timeout=300):
 url=EP+'?'+urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':q}); req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-Chandra-LSXPS/1.0'})
 with urllib.request.urlopen(req,timeout=timeout) as r: raw=r.read()
 return Table.read(io.BytesIO(raw),format='votable')
def dl(url,p):
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-Chandra-LSXPS/1.0'})
 with urllib.request.urlopen(req,timeout=180) as r,p.open('wb') as f:
  while True:
   b=r.read(8*1024*1024)
   if not b: break
   f.write(b)
def refs():
 if not P4.exists(): dl(U4,P4)
 if not P4OBS.exists(): dl(U4OBS,P4OBS)
 with fits.open(P4,memmap=True) as h:
  d=max([x for x in h if isinstance(x,(fits.BinTableHDU,fits.TableHDU)) and x.data is not None],key=lambda x:len(x.data)).data; nm={x.upper():x for x in d.names}; ra=np.asarray(d[nm['SC_RA']],float).copy(); de=np.asarray(d[nm['SC_DEC']],float).copy()
 with fits.open(P4OBS,memmap=True) as h:
  d=max([x for x in h if isinstance(x,(fits.BinTableHDU,fits.TableHDU)) and x.data is not None],key=lambda x:len(x.data)).data; nm={x.upper():x for x in d.names}; old={norm(x) for x in d[nm['OBS_ID']] if norm(x)}
 ok=np.isfinite(ra)&np.isfinite(de); return SkyCoord(ra[ok]*u.deg,de[ok]*u.deg),old
def q5(lo,hi,depth=0):
 q=f'''SELECT TOP {CAP} s.srcid AS sid,s.ra AS sra,s.dec AS sdec,d.obsid AS dobsid FROM xmmssc AS s JOIN xmmstack AS d ON s.srcid=d.srcid WHERE {BASE} AND s.ra >= {lo:.8f} AND s.ra < {hi:.8f} AND d.pps_srcnum IS NOT NULL'''; t=tap(q)
 if len(t)>=CAP:
  if depth>=8: raise RuntimeError(f'5XMM cap persists {lo}-{hi}')
  m=(lo+hi)/2; return q5(lo,m,depth+1)+q5(m,hi,depth+1)
 return [t]
def qe0(tab,lo,hi,depth=0):
 q=f'''SELECT TOP {CAP} ra,dec FROM {tab} WHERE ra >= {lo:.8f} AND ra < {hi:.8f}'''; t=tap(q)
 if len(t)>=CAP:
  if depth>=8: raise RuntimeError(f'{tab} cap persists {lo}-{hi}')
  m=(lo+hi)/2; return qe0(tab,lo,m,depth+1)+qe0(tab,m,hi,depth+1)
 return [t]
def qe(tab,lo,hi):
 a=[]
 if lo<0: a+=qe0(tab,360+lo,360); lo=0
 if hi>360: a+=qe0(tab,0,hi-360); hi=360
 if hi>lo: a+=qe0(tab,lo,hi)
 return a
def cat(a):
 if not a: return Table()
 return vstack(a,metadata_conflicts='silent') if len(a)>1 else a[0]
def coords(t):
 if not len(t): return None
 ra=np.asarray(t['ra'],float); de=np.asarray(t['dec'],float); ok=np.isfinite(ra)&np.isfinite(de); return SkyCoord(ra[ok]*u.deg,de[ok]*u.deg) if np.any(ok) else None
def hit(p,c,r):
 if c is None:return False
 _,s,_=p.match_to_catalog_sky(c); return bool(s.arcsec<=r)
def main():
 try:
  c4,old=refs(); keys=['cases','real_union','shift_union','real_csc','shift_csc','real_lsxps','shift_lsxps','both_real_catalogs']; tot={k:0 for k in keys}; bins=[]
  for lo in range(0,180,5):
   t=cat(q5(lo,lo+5)); by={}; obs=defaultdict(set)
   for sid,ra,de,ob in zip(t['sid'],t['sra'],t['sdec'],t['dobsid']):
    s=norm(sid); by.setdefault(s,(float(ra),float(de))); o=norm(ob)
    if o and o not in ('--','None','nan'): obs[s].add(o)
   ids=list(by)
   if not ids: continue
   c=SkyCoord([by[s][0] for s in ids]*u.deg,[by[s][1] for s in ids]*u.deg); _,sep,_=c.match_to_catalog_sky(c4); cases=[ids[i] for i in range(len(ids)) if sep.arcsec[i]>20 and any(o in old for o in obs[ids[i]])]
   cc=coords(cat(qe('csc',lo-PAD,lo+6+PAD))); sc=coords(cat(qe('swiftlsxps',lo-PAD,lo+6+PAD))); br={k:0 for k in keys}; br['cases']=len(cases)
   for s in cases:
    ra,de=by[s]; p=SkyCoord(ra*u.deg,de*u.deg); ps=SkyCoord(((ra+1)%360)*u.deg,de*u.deg); rc=hit(p,cc,RCSC); rs=hit(p,sc,RSWIFT); xc=hit(ps,cc,RCSC); xs=hit(ps,sc,RSWIFT)
    br['real_csc']+=int(rc); br['shift_csc']+=int(xc); br['real_lsxps']+=int(rs); br['shift_lsxps']+=int(xs); br['real_union']+=int(rc or rs); br['shift_union']+=int(xc or xs); br['both_real_catalogs']+=int(rc and rs)
   for k in keys: tot[k]+=br[k]
   bins.append({'ra_lo':lo,'ra_hi':lo+5,**br}); print(json.dumps({'bin':f'{lo}-{lo+5}',**br}),flush=True)
  n=tot['cases']; rm=tot['real_union']; sm=tot['shift_union']; odds,p=fisher_exact([[rm,n-rm],[sm,n-sm]],alternative='greater'); gates={'g1_real_union_ge_25':bool(rm>=25),'g2_real_shift_ratio_ge_5':bool(sm==0 or rm>=5*sm),'g3_fisher_p_le_0p001':bool(p<=.001)}
  out={'success':True,'science_status':'PASS' if all(gates.values()) else 'FAIL','hemisphere':'development','population':'SUM_FLAG<2 detection-confirmed reprocessing recoveries','catalogues':['CSC2.1.1','Swift LSXPS HEASARC current release'],'radii_arcsec':{'csc':RCSC,'swiftlsxps':RSWIFT},'shift_ra_deg':1.,'totals':tot,'real_union_fraction':rm/n if n else None,'shift_union_fraction':sm/n if n else None,'real_to_shift_ratio':rm/sm if sm else None,'fisher_odds_ratio':float(odds),'fisher_one_sided_p':float(p),'frozen_gates':gates,'bins':bins,'privacy':'Aggregate counts only; no source identities or coordinates emitted.'}
 except Exception as e: out={'success':False,'science_status':'INFRASTRUCTURE_FAILURE','error':f'{type(e).__name__}: {e}'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2,sort_keys=True),flush=True)
if __name__=='__main__':main()
