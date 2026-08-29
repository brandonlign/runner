#!/usr/bin/env python3
from pathlib import Path
from collections import defaultdict
import io,json,urllib.parse,urllib.request
import numpy as np
from astropy.io import fits
from astropy.table import Table
OUT=Path('results/xmm_dr14s_parent_miss_diagnostic.json');OUT.parent.mkdir(parents=True,exist_ok=True)
EP='https://sky.esa.int/esasky-tap/tap/sync';TAB='catalogues.mv_xsa_epic_stack_cat_fdw';URL='https://xmmssc.aip.de/files/dr14s/xmmstack_v3.2_4xmmdr14s_obslist.fits.gz'
IDS=['3000173020100004','3000173020100026','3000173020100027','3000173020100055','3000173020100069','3000173020100073','3000173020100077','3000173020100080','3000173020100117','3000173020100118','3000173020100119','3000173020100147','3000173020100152','3000173020100155','3000173020100173','3000173020100174','3000173020100175','3000173020100188','3000173020100192','3000173020100193']
def cv(x):
 if np.ma.is_masked(x):return None
 if isinstance(x,(bytes,np.bytes_)):return x.decode().strip()
 if hasattr(x,'item'):
  try:return x.item()
  except:return str(x)
 return x
def tap(q):
 d=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','QUERY':q}).encode();req=urllib.request.Request(EP,data=d,headers={'Content-Type':'application/x-www-form-urlencoded','User-Agent':'ISEF-DR14-parent-diagnostic/1.0'})
 with urllib.request.urlopen(req,timeout=180) as r:raw=r.read()
 t=Table.read(io.BytesIO(raw),format='votable');return [{n:cv(rr[n]) for n in t.colnames} for rr in t]
def load():
 p=Path('/tmp/o.gz');req=urllib.request.Request(URL,headers={'User-Agent':'ISEF-DR14-parent-diagnostic/1.0'})
 with urllib.request.urlopen(req,timeout=120) as r,p.open('wb') as f:
  while True:
   b=r.read(1<<20)
   if not b:break
   f.write(b)
 with fits.open(p,memmap=False) as h:
  tabs=[x for x in h if getattr(x,'data',None) is not None and hasattr(x.data,'names') and x.data.names];d=max(tabs,key=lambda x:len(x.data)).data
  stacks=defaultdict(set); meta={}
  for r in d:
   s=str(cv(r['STACK_ID']));o=str(cv(r['OBS_ID']));stacks[s].add(o);meta[s]={'n':int(cv(r['N_OBSERVATIONS'])),'ref_ra':float(cv(r['REF_RA'])),'ref_dec':float(cv(r['REF_DEC']))}
  return stacks,meta
def main():
 stacks,meta=load();byobs=defaultdict(list)
 for s,os in stacks.items():
  for o in os:byobs[o].append(s)
 res=[]
 for sid in IDS:
  rs=tap(f"SELECT srcid,obs_id,n_obs,n_contrib,ra,dec FROM {TAB} WHERE srcid={sid}")
  summ=next((r for r in rs if r.get('n_obs') is not None),None);child=sorted({str(r['obs_id']) for r in rs if r.get('obs_id') not in (None,'')})
  n=int(summ['n_obs']) if summ else None
  union=sorted({s for o in child for s in byobs.get(o,[])})
  candidates=[]
  for s in union:
   candidates.append({'stack_id':s,'stack_n':len(stacks[s]),'reported_n':meta[s]['n'],'contains_all_child':set(child)<=stacks[s],'missing_child':sorted(set(child)-stacks[s]),'extra_stack_obs':sorted(stacks[s]-set(child)),'ref_ra':meta[s]['ref_ra'],'ref_dec':meta[s]['ref_dec']})
  res.append({'srcid':sid,'encoded_obsid':sid[1:11],'summary':summ,'child_obsids':child,'child_count':len(child),'stacks_containing_encoded':byobs.get(sid[1:11],[]),'candidate_stacks':candidates})
 out={'success':True,'diagnostics':res,'note':'Structural identifiers, coordinates and stack membership only; no flux/spectral/classification outcomes read.'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
