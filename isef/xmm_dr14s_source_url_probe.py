#!/usr/bin/env python3
"""Probe plausible ESA catalogue filenames for the historical 4XMM-DR14s source-only file.
Infrastructure only; no catalogue content is downloaded beyond response headers."""
from pathlib import Path
import json,urllib.request,urllib.error
OUT=Path('results/xmm_dr14s_source_url_probe.json');OUT.parent.mkdir(parents=True,exist_ok=True)
BASE='https://nxsa.esac.esa.int/catalogues/'
NAMES=[
 '4XMM_DR14s.fits.gz','4XMM_DR14s_source.fits.gz','4XMM_DR14s_sources.fits.gz','4XMM_DR14s_src.fits.gz',
 '4XMM_DR14s_cat_source.fits.gz','4XMM_DR14s_cat_sources.fits.gz','4XMM_DR14scat_source.fits.gz',
 '4XMM_DR14scat_sources.fits.gz','4XMM_DR14scat_v1.0.fits.gz','4XMM_DR14scat_source_v1.0.fits.gz',
 '4XMM_DR14s_cat_v1.0.fits.gz','4XMM_DR14s_cat_source_v1.0.fits.gz','4XMM_DR14s_source_v1.0.fits.gz',
 '4XMM_DR14s_sources_v1.0.fits.gz','4XMM_DR14s_Stacked.fits.gz','4XMM_DR14s_Stacked_source.fits.gz',
 '4XMM_DR14s_stacked_sources.fits.gz','4xmmdr14s_sources.fits.gz','4xmmdr14s_source.fits.gz',
 'xmmstack_v3.2_4xmmdr14s_source.fits.gz','xmmstack_v3.2_4xmmdr14s_sources.fits.gz',
 'xmmstack_v3.2_4xmmdr14s_src.fits.gz','xmmstack_v3.2_4xmmdr14s.fits.gz',
 'xmmstack_v3.2_4xmmdr14s_source_only.fits.gz','4XMM_DR14s_source_only.fits.gz',
]
def main():
 hits=[];allr=[]
 for n in NAMES:
  u=BASE+n
  try:
   req=urllib.request.Request(u,method='HEAD',headers={'User-Agent':'ISEF-XMM-DR14s-url-probe/1.0'})
   with urllib.request.urlopen(req,timeout=20) as r:
    rec={'name':n,'url':u,'status':r.status,'length':r.headers.get('Content-Length'),'type':r.headers.get('Content-Type'),'final':r.geturl()}
    allr.append(rec)
    if r.status<400:hits.append(rec)
  except urllib.error.HTTPError as e:allr.append({'name':n,'url':u,'status':e.code})
  except Exception as e:allr.append({'name':n,'url':u,'error':f'{type(e).__name__}: {e}'})
 out={'success':True,'hits':hits,'attempted':len(allr),'results':allr,'decision':'FOUND' if hits else 'NOT_FOUND'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
