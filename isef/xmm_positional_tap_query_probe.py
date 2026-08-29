#!/usr/bin/env python3
from pathlib import Path
import json,urllib.parse,urllib.request
OUT=Path('results/xmm_positional_tap_query_probe.json');OUT.parent.mkdir(parents=True,exist_ok=True)
E5='https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync';E4='https://sky.esa.int/esasky-tap/tap/sync'
queries={
 'dr15_min':"SELECT TOP 3 srcid,ra,dec,n_obs FROM xmmstack WHERE n_obs IS NOT NULL AND ra>=0 AND ra<30",
 'dr15_full':"SELECT TOP 3 srcid,ra,dec,radec_err,extent,sum_flag,stack_det_ml,n_obs FROM xmmstack WHERE n_obs IS NOT NULL AND ra>=0 AND ra<30 AND sum_flag=0 AND extent=0 AND stack_det_ml>=10",
 'dr14_min':"SELECT TOP 3 srcid,ra,dec,n_obs FROM catalogues.mv_xsa_epic_stack_cat_fdw WHERE n_obs IS NOT NULL AND ra>=0 AND ra<30",
 'dr14_full':"SELECT TOP 3 srcid,ra,dec,radec_err,n_obs FROM catalogues.mv_xsa_epic_stack_cat_fdw WHERE n_obs IS NOT NULL AND ra>=0 AND ra<30.02",
}
def run(ep,q):
 d=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','QUERY':q}).encode();req=urllib.request.Request(ep,data=d,headers={'Content-Type':'application/x-www-form-urlencoded','User-Agent':'ISEF-positional-query-probe/1.0'})
 try:
  with urllib.request.urlopen(req,timeout=120) as r:
   b=r.read();return {'http':r.status,'content_type':r.headers.get('Content-Type'),'bytes':len(b),'head':b[:5000].decode('utf-8','replace')}
 except Exception as e:
  body=''
  try:body=e.read(5000).decode('utf-8','replace')
  except:pass
  return {'error':f'{type(e).__name__}: {e}','head':body}
def main():
 out={}
 for name,q in queries.items():out[name]={'query':q,'response':run(E5 if name.startswith('dr15') else E4,q)}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
