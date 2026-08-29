#!/usr/bin/env python3
"""Resolve the registered 4XMM-DR14 TAP service and inspect its actual tables.
No astronomical source rows are emitted."""
from pathlib import Path
import json
import pyvo
OUT=Path('results/xmm_dr14_registry_resolve.json');OUT.parent.mkdir(parents=True,exist_ok=True)
IVOID='ivo://xcatdb/4xmm/tap'
def main():
 out={'success':False,'ivoid':IVOID}
 try:
  rs=pyvo.registry.search(ivoid=IVOID)
  out['registry_matches']=len(rs)
  if not len(rs):raise RuntimeError('registered service not found')
  r=rs[0]
  out['title']=str(r.res_title);out['access_url']=str(r.access_url);out['interfaces']=[str(x) for x in r.access_modes()]
  svc=r.get_service(service_type='tap')
  out['service_baseurl']=str(svc.baseurl)
  tables=svc.tables
  out['tables']=[]
  for name,t in tables.items():
   cols=[]
   for c in t.columns:
    n=str(c.name)
    if n.lower() in ('obs_id','obsid','srcid','detid','ra','dec','sc_ra','sc_dec','mjd_start','mjd_stop'):
     cols.append({'name':n,'datatype':str(c.datatype),'description':str(c.description)})
   out['tables'].append({'name':str(name),'description':str(t.description),'relevant_columns':cols,'column_count':len(t.columns)})
  out['success']=True
 except Exception as e:out['error']=f'{type(e).__name__}: {e}'
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True,default=str)+'\n');print(json.dumps(out,indent=2,sort_keys=True,default=str))
if __name__=='__main__':main()
