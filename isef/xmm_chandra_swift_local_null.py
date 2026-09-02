#!/usr/bin/env python3
"""Frozen local-null robustness for strict 5XMM Chandra/2SXPS external reality. Aggregate only."""
from pathlib import Path
from collections import defaultdict
import io,json,urllib.parse,urllib.request
import numpy as np
from scipy.stats import fisher_exact
from astropy.table import Table,vstack
from astropy.io import fits
from astropy.coordinates import SkyCoord
import astropy.units as u
EP='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync';CAP=100000;PAD=.03;RCSC=5.;RSWIFT=10.
U4='https://heasarc.gsfc.nasa.gov/FTP/xmm/data/catalogues/4XMM_DR14cat_slim_v1.0.fits.gz';U4O='http://xmmssc.irap.omp.eu/Catalogue/4XMM-DR14/4xmmdr14_obslist.fits';P4=Path('/tmp/4main.fits.gz');P4O=Path('/tmp/4mainobs.fits');OUT=Path('results/xmm_chandra_swift_local_null.json');OUT.parent.mkdir(parents=True,exist_ok=True);BASE='s.sum_flag<2 AND s.extent=0 AND s.ep_det_ml>=15'
def norm(x):
 if isinstance(x,(bytes,np.bytes_)):x=x.decode('utf-8','replace')
 return str(x).strip()
def tap(q):
 url=EP+'?'+urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':q});req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-local-null/1.0'})
 with urllib.request.urlopen(req,timeout=300) as r:return Table.read(io.BytesIO(r.read()),format='votable')
def dl(url,p):
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-local-null/1.0'})
 with urllib.request.urlopen(req,timeout=180) as r,p.open('wb') as g:
  while 1:
   b=r.read(8388608)
   if not b:break
   g.write(b)
def refs():
 if not P4.exists():dl(U4,P4)
 if not P4O.exists():dl(U4O,P4O)
 with fits.open(P4,memmap=True) as h:
  d=max([x for x in h if isinstance(x,(fits.BinTableHDU,fits.TableHDU)) and x.data is not None],key=lambda x:len(x.data)).data;nm={x.upper():x for x in d.names};ra=np.asarray(d[nm['SC_RA']],float);de=np.asarray(d[nm['SC_DEC']],float);ok=np.isfinite(ra)&np.isfinite(de);c=SkyCoord(ra[ok]*u.deg,de[ok]*u.deg)
 with fits.open(P4O,memmap=False) as h:
  d=max([x for x in h if isinstance(x,(fits.BinTableHDU,fits.TableHDU)) and x.data is not None],key=lambda x:len(x.data)).data;nm={x.upper():x for x in d.names};old={norm(x) for x in d[nm['OBS_ID']] if norm(x)}
 return c,old
def q5(lo,hi,dep=0):
 q=f'''SELECT TOP {CAP} s.srcid sid,s.ra sra,s.dec sdec,d.obsid obsid FROM xmmssc s JOIN xmmstack d ON s.srcid=d.srcid WHERE {BASE} AND s.ra>={lo:.8f} AND s.ra<{hi:.8f} AND d.pps_srcnum IS NOT NULL''';t=tap(q)
 if len(t)>=CAP:
  if dep>=8:raise RuntimeError('5x cap')
  m=(lo+hi)/2;return q5(lo,m,dep+1)+q5(m,hi,dep+1)
 return [t]
def qe0(tab,lo,hi,dep=0):
 q=f'''SELECT TOP {CAP} ra,dec FROM {tab} WHERE ra>={lo:.8f} AND ra<{hi:.8f}''';t=tap(q)
 if len(t)>=CAP:
  if dep>=8:raise RuntimeError(tab+' cap')
  m=(lo+hi)/2;return qe0(tab,lo,m,dep+1)+qe0(tab,m,hi,dep+1)
 return [t]
def qe(tab,lo,hi):
 a=[]
 if lo<0:a+=qe0(tab,360+lo,360);lo=0
 if hi>360:a+=qe0(tab,0,hi-360);hi=360
 if hi>lo:a+=qe0(tab,lo,hi)
 return a
def cat(a):return vstack(a,metadata_conflicts='silent') if len(a)>1 else (a[0] if a else Table())
def coords(t):
 if not len(t):return None
 ra=np.asarray(t['ra'],float);de=np.asarray(t['dec'],float);ok=np.isfinite(ra)&np.isfinite(de);return SkyCoord(ra[ok]*u.deg,de[ok]*u.deg) if np.any(ok) else None
def hit(p,c,r):
 if c is None:return False
 _,s,_=p.match_to_catalog_sky(c);return bool(s.arcsec<=r)
def nulls(ra,de):
 cd=max(abs(np.cos(np.deg2rad(de))),1e-6);dra=(60/3600)/cd;return [SkyCoord(((ra+dra)%360)*u.deg,de*u.deg),SkyCoord(((ra-dra)%360)*u.deg,de*u.deg),SkyCoord(ra*u.deg,min(89.999999,de+60/3600)*u.deg),SkyCoord(ra*u.deg,max(-89.999999,de-60/3600)*u.deg)]
def hemi(lo,hi,c4,old):
 tot={'cases':0,'real_union':0,'local_null_union_trials':0,'local_null_trials':0,'real_csc':0,'real_swift':0}
 for b in range(lo,hi,5):
  t=cat(q5(b,b+5));by={};obs=defaultdict(set)
  for sid,ra,de,ob in zip(t['sid'],t['sra'],t['sdec'],t['obsid']):
   s=norm(sid);by.setdefault(s,(float(ra),float(de)));o=norm(ob)
   if o:obs[s].add(o)
  ids=list(by)
  if not ids:continue
  c=SkyCoord([by[s][0] for s in ids]*u.deg,[by[s][1] for s in ids]*u.deg);_,sep,_=c.match_to_catalog_sky(c4);cases=[ids[i] for i in range(len(ids)) if sep.arcsec[i]>20 and any(o in old for o in obs[ids[i]])];cc=coords(cat(qe('csc',b-PAD,b+5+PAD)));sc=coords(cat(qe('swift2sxps',b-PAD,b+5+PAD)));tot['cases']+=len(cases)
  for s in cases:
   ra,de=by[s];p=SkyCoord(ra*u.deg,de*u.deg);rc=hit(p,cc,RCSC);rs=hit(p,sc,RSWIFT);tot['real_csc']+=rc;tot['real_swift']+=rs;tot['real_union']+=int(rc or rs)
   for z in nulls(ra,de):tot['local_null_trials']+=1;tot['local_null_union_trials']+=int(hit(z,cc,RCSC) or hit(z,sc,RSWIFT))
 case_n=tot['cases'];real_m=tot['real_union'];null_m=tot['local_null_union_trials'];null_n=tot['local_null_trials'];od,p=fisher_exact([[real_m,case_n-real_m],[null_m,null_n-null_m]],alternative='greater');rr=real_m/case_n if case_n else None;nr=null_m/null_n if null_n else None;g={'g1_real_ge25':real_m>=25,'g2_real_rate_ge3x_null':nr==0 and real_m>0 or (nr>0 and rr>=3*nr),'g3_fisher_p_le0p001':p<=.001};return {**tot,'real_rate':rr,'local_null_rate':nr,'rate_ratio':rr/nr if nr else None,'fisher_odds':float(od),'fisher_p':float(p),'gates':g,'pass':all(g.values())}
def main():
 try:
  c,o=refs();d=hemi(0,180,c,o);v=hemi(180,360,c,o);out={'success':True,'science_status':'PASS' if d['pass'] and v['pass'] else 'FAIL','development':d,'validation':v,'null_offset_arcsec':60,'privacy':'Aggregate only.'}
 except Exception as e:out={'success':False,'science_status':'INFRASTRUCTURE_FAILURE','error':f'{type(e).__name__}: {e}'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True),flush=True)
if __name__=='__main__':main()
