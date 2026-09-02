#!/usr/bin/env python3
"""Frozen R3 external-reality test for the clean single-observation 5XMM rebuild.
Do not execute unless frozen R2 passes. Aggregate output only.
"""
from pathlib import Path
from collections import defaultdict
import gzip,shutil,io,json,urllib.parse,urllib.request
import numpy as np
from scipy.stats import fisher_exact
from astropy.table import Table,vstack
from astropy.io import fits
from astropy.coordinates import SkyCoord
import astropy.units as u
EP='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync';CAP=100000;PAD=.03;RCSC=5.;RLS=10.
U4='https://heasarc.gsfc.nasa.gov/FTP/xmm/data/catalogues/4XMM_DR14cat_slim_v1.0.fits.gz';U4O='http://xmmssc.irap.omp.eu/Catalogue/4XMM-DR14/4xmmdr14_obslist.fits';U4S='https://xmmssc.aip.de/files/dr14s/xmmstack_v3.2_4xmmdr14s.fits.gz'
P4=Path('/tmp/4main.fits.gz');P4O=Path('/tmp/4main_obs.fits');P4SG=Path('/tmp/4stack.fits.gz');P4S=Path('/tmp/4stack.fits');OUT=Path('results/xmm_clean_single_obs_r3_external_reality.json');OUT.parent.mkdir(parents=True,exist_ok=True)
BASE='s.sum_flag < 2 AND s.extent=0 AND s.ep_det_ml>=15'
def norm(x):
 if isinstance(x,(bytes,np.bytes_)):x=x.decode('utf-8','replace')
 return str(x).strip()
def tap(q,timeout=300):
 url=EP+'?'+urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':q});req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-clean-R3/1.0'})
 with urllib.request.urlopen(req,timeout=timeout) as r:return Table.read(io.BytesIO(r.read()),format='votable')
def dl(url,p,timeout=1200):
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-clean-R3/1.0'})
 with urllib.request.urlopen(req,timeout=timeout) as r,p.open('wb') as g:
  while True:
   b=r.read(16*1024*1024)
   if not b:break
   g.write(b)
def catcoords(path):
 with fits.open(path,memmap=True) as h:
  d=max([x for x in h if isinstance(x,(fits.BinTableHDU,fits.TableHDU)) and x.data is not None],key=lambda x:len(x.data)).data;nm={x.upper():x for x in d.names}
  for a,b in [('SC_RA','SC_DEC'),('RA','DEC'),('SRC_RA','SRC_DEC'),('SOURCE_RA','SOURCE_DEC')]:
   if a in nm and b in nm:
    ra=np.asarray(d[nm[a]],float).copy();de=np.asarray(d[nm[b]],float).copy();ok=np.isfinite(ra)&np.isfinite(de);return SkyCoord(ra[ok]*u.deg,de[ok]*u.deg)
 raise RuntimeError('no coordinate columns')
def obsids(path):
 with fits.open(path,memmap=False) as h:
  d=max([x for x in h if isinstance(x,(fits.BinTableHDU,fits.TableHDU)) and x.data is not None],key=lambda x:len(x.data)).data;nm={x.upper():x for x in d.names};c=nm.get('OBS_ID') or nm.get('OBSID');return {norm(x) for x in d[c] if norm(x)}
def refs():
 if not P4.exists():dl(U4,P4,300)
 if not P4O.exists():dl(U4O,P4O,300)
 if not P4SG.exists():dl(U4S,P4SG,1200)
 if not P4S.exists():
  with gzip.open(P4SG,'rb') as src,P4S.open('wb') as dst:shutil.copyfileobj(src,dst,length=32*1024*1024)
 return catcoords(P4),catcoords(P4S),obsids(P4O)
def q5(lo,hi,dep=0):
 q=f'''SELECT TOP {CAP} s.srcid sid,s.ra sra,s.dec sdec,s.n_contrib nc,d.obsid obsid FROM xmmssc s JOIN xmmstack d ON s.srcid=d.srcid WHERE {BASE} AND s.ra>={lo:.8f} AND s.ra<{hi:.8f} AND d.pps_srcnum IS NOT NULL''';t=tap(q)
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
def vcat(a):return vstack(a,metadata_conflicts='silent') if len(a)>1 else (a[0] if a else Table())
def sky(t):
 if not len(t):return None
 ra=np.asarray(t['ra'],float);de=np.asarray(t['dec'],float);ok=np.isfinite(ra)&np.isfinite(de);return SkyCoord(ra[ok]*u.deg,de[ok]*u.deg) if np.any(ok) else None
def hit(p,c,r):
 if c is None:return False
 _,s,_=p.match_to_catalog_sky(c);return bool(s.arcsec<=r)
def nulls(ra,de):
 cd=max(abs(np.cos(np.deg2rad(de))),1e-6);dra=(60/3600)/cd
 return [SkyCoord(((ra+dra)%360)*u.deg,de*u.deg),SkyCoord(((ra-dra)%360)*u.deg,de*u.deg),SkyCoord(ra*u.deg,min(89.999999,de+60/3600)*u.deg),SkyCoord(ra*u.deg,max(-89.999999,de-60/3600)*u.deg)]
def hemi(lo,hi,cmain,cstack,old):
 tot={'cases':0,'real_union':0,'local_null_union_trials':0,'local_null_trials':0,'real_csc':0,'real_lsxps':0}
 for b in range(lo,hi,5):
  t=vcat(q5(float(b),float(b+5)));by={};obs=defaultdict(set);nc={}
  for sid,ra,de,ncon,ob in zip(t['sid'],t['sra'],t['sdec'],t['nc'],t['obsid']):
   s=norm(sid);by.setdefault(s,(float(ra),float(de)));nc.setdefault(s,float(ncon));o=norm(ob)
   if o in old:obs[s].add(o)
  ids=[s for s in by if obs[s]]
  if not ids:continue
  c=SkyCoord([by[s][0] for s in ids]*u.deg,[by[s][1] for s in ids]*u.deg);_,sm,_=c.match_to_catalog_sky(cmain);mainclean=[ids[i] for i in range(len(ids)) if sm.arcsec[i]>20]
  if not mainclean:continue
  cc=SkyCoord([by[s][0] for s in mainclean]*u.deg,[by[s][1] for s in mainclean]*u.deg);_,ss,_=cc.match_to_catalog_sky(cstack);cases=[mainclean[i] for i in range(len(mainclean)) if ss.arcsec[i]>20 and nc.get(mainclean[i])==1]
  ec=sky(vcat(qe('csc',b-PAD,b+5+PAD)));es=sky(vcat(qe('swiftlsxc',b-PAD,b+5+PAD)))
  tot['cases']+=len(cases)
  for s in cases:
   ra,de=by[s];p=SkyCoord(ra*u.deg,de*u.deg);rc=hit(p,ec,RCSC);rs=hit(p,es,RLS);tot['real_csc']+=int(rc);tot['real_lsxps']+=int(rs);tot['real_union']+=int(rc or rs)
   for z in nulls(ra,de):tot['local_null_trials']+=1;tot['local_null_union_trials']+=int(hit(z,ec,RCSC) or hit(z,es,RLS))
 n=tot['cases'];rm=tot['real_union'];nm=tot['local_null_union_trials'];nn=tot['local_null_trials'];rr=rm/n if n else 0.;nr=nm/nn if nn else 0.;od,p=fisher_exact([[rm,n-rm],[nm,nn-nm]],alternative='greater')
 g={'real_ge25':bool(rm>=25),'real_rate_ge3x_local':bool((nr==0 and rm>0) or (nr>0 and rr>=3*nr)),'fisher_p_le0p001':bool(p<=.001)}
 return {**tot,'real_rate':float(rr),'local_null_rate':float(nr),'rate_ratio':float(rr/nr) if nr else None,'fisher_odds':float(od),'fisher_p':float(p),'gates':g,'pass':bool(all(g.values()))}
def main():
 try:
  cm,cs,o=refs();d=hemi(0,180,cm,cs,o);v=hemi(180,360,cm,cs,o);out={'success':True,'science_status':'PASS' if d['pass'] and v['pass'] else 'FAIL','development':d,'validation':v,'null_offset_arcsec':60,'privacy':'Aggregate only; no identities or coordinates emitted.'}
 except Exception as e:out={'success':False,'science_status':'INFRASTRUCTURE_FAILURE','error':f'{type(e).__name__}: {e}'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True),flush=True)
if __name__=='__main__':main()
