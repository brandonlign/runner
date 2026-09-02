#!/usr/bin/env python3
"""Critical frozen validity test: exclude strict 5XMM recoveries already present in 4XMM-DR14s.
Aggregate output only."""
from pathlib import Path
from collections import defaultdict
import gzip,shutil,io,json,urllib.parse,urllib.request
import numpy as np
from astropy.table import Table,vstack
from astropy.io import fits
from astropy.coordinates import SkyCoord
import astropy.units as u
EP='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync'; CAP=100000
U4='https://heasarc.gsfc.nasa.gov/FTP/xmm/data/catalogues/4XMM_DR14cat_slim_v1.0.fits.gz'; U4O='http://xmmssc.irap.omp.eu/Catalogue/4XMM-DR14/4xmmdr14_obslist.fits'
U4S='https://xmmssc.aip.de/files/dr14s/xmmstack_v3.2_4xmmdr14s.fits.gz'; U4SO='https://xmmssc.aip.de/files/dr14s/xmmstack_v3.2_4xmmdr14s_obslist.fits.gz'
P4=Path('/tmp/4main.fits.gz'); P4O=Path('/tmp/4main_obs.fits'); P4SG=Path('/tmp/4stack.fits.gz'); P4S=Path('/tmp/4stack.fits'); P4SO=Path('/tmp/4stack_obs.fits.gz'); OUT=Path('results/xmm_prior_stacked_exclusion.json'); OUT.parent.mkdir(parents=True,exist_ok=True)
BASE='s.sum_flag < 2 AND s.extent=0 AND s.ep_det_ml>=15'
def norm(x):
 if isinstance(x,(bytes,np.bytes_)): x=x.decode('utf-8','replace')
 return str(x).strip()
def tap(q,timeout=300):
 url=EP+'?'+urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':q}); req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-prior-stack/1.0'})
 with urllib.request.urlopen(req,timeout=timeout) as r:return Table.read(io.BytesIO(r.read()),format='votable')
def dl(url,p,timeout=900):
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-XMM-prior-stack/1.0'})
 with urllib.request.urlopen(req,timeout=timeout) as r,p.open('wb') as f:
  while True:
   b=r.read(8*1024*1024)
   if not b: break
   f.write(b)
def largest_table(path):
 h=fits.open(path,memmap=True); tabs=[x for x in h if isinstance(x,(fits.BinTableHDU,fits.TableHDU)) and x.data is not None]; z=max(tabs,key=lambda x:len(x.data)); return h,z.data
def coords_from(data):
 nm={x.upper():x for x in data.names}; pairs=[('SC_RA','SC_DEC'),('RA','DEC'),('SRC_RA','SRC_DEC'),('SOURCE_RA','SOURCE_DEC')]
 for a,b in pairs:
  if a in nm and b in nm:
   ra=np.asarray(data[nm[a]],float).copy(); de=np.asarray(data[nm[b]],float).copy(); ok=np.isfinite(ra)&np.isfinite(de); return SkyCoord(ra[ok]*u.deg,de[ok]*u.deg),a+'/'+b,int(np.sum(ok))
 raise RuntimeError('no RA/DEC columns among '+','.join(data.names[:40]))
def obsids_from(path):
 with fits.open(path,memmap=False) as h:
  tabs=[x for x in h if isinstance(x,(fits.BinTableHDU,fits.TableHDU)) and x.data is not None]; d=max(tabs,key=lambda x:len(x.data)).data; nm={x.upper():x for x in d.names}; col=nm.get('OBS_ID') or nm.get('OBSID')
  if not col: raise RuntimeError('no obsid column')
  return {norm(x) for x in d[col] if norm(x)}
def refs():
 if not P4.exists():dl(U4,P4,300)
 if not P4O.exists():dl(U4O,P4O,300)
 with fits.open(P4,memmap=True) as h:
  tabs=[x for x in h if isinstance(x,(fits.BinTableHDU,fits.TableHDU)) and x.data is not None]; d=max(tabs,key=lambda x:len(x.data)).data; cmain,cols,n=coords_from(d)
 oldmain=obsids_from(P4O)
 if not P4SG.exists():dl(U4S,P4SG,1200)
 if not P4S.exists():
  with gzip.open(P4SG,'rb') as src,P4S.open('wb') as dst: shutil.copyfileobj(src,dst,length=16*1024*1024)
 h,d=largest_table(P4S); cstack,stackcols,ns=coords_from(d); h.close()
 if not P4SO.exists():dl(U4SO,P4SO,300)
 stackobs=obsids_from(P4SO)
 return cmain,cstack,oldmain,stackobs,{'main_positions':n,'stack_positions':ns,'stack_coordinate_columns':stackcols,'stack_obsids':len(stackobs)}
def qb(lo,hi,depth=0):
 q=f'''SELECT TOP {CAP} s.srcid sid,s.ra sra,s.dec sdec,d.obsid obsid FROM xmmssc s JOIN xmmstack d ON s.srcid=d.srcid WHERE {BASE} AND s.ra>={lo:.8f} AND s.ra<{hi:.8f} AND d.pps_srcnum IS NOT NULL'''; t=tap(q)
 if len(t)>=CAP:
  if depth>=8:raise RuntimeError(f'cap {lo}-{hi}')
  m=(lo+hi)/2; return qb(lo,m,depth+1)+qb(m,hi,depth+1)
 return [t]
def hemi(lo,hi,cmain,cstack,oldmain,stackobs):
 by={};obs=defaultdict(set)
 for b in range(lo,hi,5):
  ts=qb(float(b),float(b+5));t=vstack(ts,metadata_conflicts='silent') if len(ts)>1 else ts[0]
  for sid,ra,de,ob in zip(t['sid'],t['sra'],t['sdec'],t['obsid']):
   s=norm(sid);by.setdefault(s,(float(ra),float(de)));o=norm(ob)
   if o in oldmain:obs[s].add(o)
 ids=list(by); c=SkyCoord([by[s][0] for s in ids]*u.deg,[by[s][1] for s in ids]*u.deg);_,sm,_=c.match_to_catalog_sky(cmain); oldrec=[ids[i] for i in range(len(ids)) if sm.arcsec[i]>20 and obs[ids[i]]]
 rc=SkyCoord([by[s][0] for s in oldrec]*u.deg,[by[s][1] for s in oldrec]*u.deg);_,ss,_=rc.match_to_catalog_sky(cstack); matched=ss.arcsec<=20; clean=int(np.sum(~matched)); base=len(oldrec); covered=np.array([bool(obs[s]&stackobs) for s in oldrec]); covn=int(np.sum(covered)); covmatch=int(np.sum(matched&covered)); covclean=int(np.sum((~matched)&covered)); frac=clean/base if base else None
 return {'existing_strict_main_only_recoveries':base,'matched_prior_4xmmdr14s_le20arcsec':int(np.sum(matched)),'prior_catalogue_clean_recoveries':clean,'retention_fraction':frac,'with_old_obsid_in_4xmmdr14s_obslist':covn,'covered_matched_prior_stack':covmatch,'covered_unmatched_prior_stack':covclean,'gate_count_ge300':clean>=300,'gate_retention_ge0p60':frac is not None and frac>=.60}
def main():
 try:
  cmain,cstack,oldmain,stackobs,meta=refs(); dev=hemi(0,180,cmain,cstack,oldmain,stackobs);val=hemi(180,360,cmain,cstack,oldmain,stackobs);passed=dev['gate_count_ge300'] and dev['gate_retention_ge0p60'] and val['gate_count_ge300'] and val['gate_retention_ge0p60'];out={'success':True,'science_status':'PASS' if passed else 'FAIL','development':dev,'validation':val,'prior_stack_meta':meta,'exclusion_radius_arcsec':20,'privacy':'Aggregate counts only; no identities or coordinates emitted.'}
 except Exception as e:out={'success':False,'science_status':'INFRASTRUCTURE_FAILURE','error':f'{type(e).__name__}: {e}'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True),flush=True)
if __name__=='__main__':main()
