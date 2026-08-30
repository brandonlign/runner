#!/usr/bin/env python3
"""Infrastructure-only HETDEX PDR1 access/product probe. No science selection."""
from pathlib import Path
import json,re,urllib.request,urllib.parse
from html import unescape
OUT=Path('results/hetdex_pdr1_access_probe.json');OUT.parent.mkdir(parents=True,exist_ok=True)
URLS=['https://hetdex.org/data-results/','https://web.corral.tacc.utexas.edu/hetdex/HETDEX/pdr/pdr1/']
def get(url):
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-HETDEX-feasibility/1.0'})
 with urllib.request.urlopen(req,timeout=60) as r:return r.status,r.geturl(),r.headers.get('content-type'),r.read(2_000_000).decode('utf-8','replace')
def links(base,html):
 hs=re.findall(r'href=["\']([^"\']+)',html,re.I);return sorted(set(urllib.parse.urljoin(base,unescape(x)) for x in hs))
def main():
 out={'success':True,'status':'INFRASTRUCTURE_ONLY','pages':[],'candidate_product_links':[]}
 try:
  allx=[]
  for u in URLS:
   st,final,ct,h=get(u);ls=links(final,h);out['pages'].append({'url':u,'status':st,'final_url':final,'content_type':ct,'link_count':len(ls)});allx+=ls
  keys=('pdr1','hpsc','source','catalog','fits','h5','hdf','detect','line','spectrum','spectra','cube','tar','gz')
  cand=[x for x in sorted(set(allx)) if any(k in x.lower() for k in keys)]
  out['candidate_product_links']=cand[:300];out['candidate_link_count']=len(cand)
  out['note']='No spectra, source properties, candidate identities, or science outcomes inspected.'
 except Exception as e:out={'success':False,'status':'INFRASTRUCTURE_ONLY','error':f'{type(e).__name__}: {e}'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
