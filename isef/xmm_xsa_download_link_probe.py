#!/usr/bin/env python3
"""Infrastructure-only extraction of catalogue download links from ESA's XSA page.
No catalogue rows or candidate identities are read."""
from pathlib import Path
import html.parser, json, urllib.request, urllib.parse
OUT=Path('results/xmm_xsa_download_link_probe.json');OUT.parent.mkdir(parents=True,exist_ok=True)
URLS=[
 'https://www.cosmos.esa.int/web/xmm-newton/xsa',
 'https://nxsa.esac.esa.int/nxsa-web/#full-catalogues',
 'https://nxsa.esac.esa.int/nxsa-web/',
]
class P(html.parser.HTMLParser):
 def __init__(self,base):super().__init__();self.base=base;self.links=[];self.cur=None;self.text=[]
 def handle_starttag(self,tag,attrs):
  if tag.lower()=='a':
   d=dict(attrs);self.cur=d.get('href');self.text=[]
 def handle_data(self,d):
  if self.cur is not None:self.text.append(d)
 def handle_endtag(self,tag):
  if tag.lower()=='a' and self.cur is not None:
   self.links.append({'text':' '.join(''.join(self.text).split()),'href':urllib.parse.urljoin(self.base,self.cur)})
   self.cur=None;self.text=[]
def fetch(u):
 req=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0 ISEF-XMM-link-probe/1.0'})
 with urllib.request.urlopen(req,timeout=60) as r:return r.geturl(),r.read().decode('utf-8','replace')
def main():
 out={'success':True,'attempts':[],'relevant_links':[]}
 seen=set()
 for u in URLS:
  try:
   final,txt=fetch(u);p=P(final);p.feed(txt)
   rel=[]
   for x in p.links:
    blob=(x['text']+' '+x['href']).lower()
    if any(k in blob for k in ('4xmm','dr14s','stacked source','stacked observation','fits')):
     rel.append(x)
     if x['href'] not in seen:seen.add(x['href']);out['relevant_links'].append(x)
   out['attempts'].append({'url':u,'final_url':final,'bytes':len(txt),'relevant_count':len(rel),'relevant':rel[:100]})
  except Exception as e:out['attempts'].append({'url':u,'error':f'{type(e).__name__}: {e}'})
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
