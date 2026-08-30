#!/usr/bin/env python3
import json, re, urllib.request, urllib.parse
from pathlib import Path
from html.parser import HTMLParser

ROOT='https://almascience.org/almadata/sciver/G31.41Band2/'
OUT=Path('results/alma_band2_g31_access_probe.json'); OUT.parent.mkdir(exist_ok=True)
class Links(HTMLParser):
    def __init__(self): super().__init__(); self.links=[]
    def handle_starttag(self,tag,attrs):
        if tag.lower()=='a':
            d=dict(attrs); h=d.get('href')
            if h:self.links.append(h)
def get(url,timeout=90):
    req=urllib.request.Request(url,headers={'User-Agent':'ISEF-ALMA-B2-AccessProbe/1.0'})
    with urllib.request.urlopen(req,timeout=timeout) as r:return r.status,r.headers, r.read().decode('utf-8','replace')
def head(url):
    try:
        req=urllib.request.Request(url,method='HEAD',headers={'User-Agent':'ISEF-ALMA-B2-AccessProbe/1.0'})
        with urllib.request.urlopen(req,timeout=45) as r:return {'ok':True,'status':r.status,'length':r.headers.get('Content-Length'),'type':r.headers.get('Content-Type'),'final':r.geturl()}
    except Exception as e:return {'ok':False,'error':type(e).__name__+': '+str(e)}

def walk(url,depth=0,maxdepth=3):
    rec={'url':url,'depth':depth}
    try:
        st,h,txt=get(url); rec['status']=st; rec['content_type']=h.get('Content-Type'); rec['html_chars']=len(txt)
        p=Links();p.feed(txt); links=[]
        for x in p.links:
            if x in ('../','./') or x.startswith('?') or x.startswith('#'):continue
            u=urllib.parse.urljoin(url,x)
            if not u.startswith(ROOT):continue
            links.append({'href':x,'url':u})
        rec['links']=links
        children=[]
        if depth<maxdepth:
            for item in links:
                hrf=item['href'].split('?')[0]
                # recurse only into likely directories; never download large science files.
                if hrf.endswith('/') and not any(z in hrf.lower() for z in ['uncalib','raw']):
                    children.append(walk(item['url'],depth+1,maxdepth))
        rec['children']=children
    except Exception as e:rec['error']=type(e).__name__+': '+str(e)
    return rec

o={'status':'ACCESS_SCHEMA_ONLY','root':ROOT,'science_data_read':False}
o['tree']=walk(ROOT)
# Collect file URLs from traversed metadata and HEAD only likely README/FITS/TAR products.
def collect(node,out):
    for x in node.get('links',[]):
        p=x['href'].lower()
        if any(p.endswith(s) for s in ['.fits','.fits.gz','.tar','.tgz','.tar.gz','.txt','.md','.readme']) or 'readme' in p:out.append(x['url'])
    for c in node.get('children',[]):collect(c,out)
files=[];collect(o['tree'],files);files=list(dict.fromkeys(files))
o['file_metadata']={u:head(u) for u in files[:200]}
o['n_metadata_files_found']=len(files)
o['success']=not bool(o['tree'].get('error'))
OUT.write_text(json.dumps(o,indent=2)+'\n');print(json.dumps(o,indent=2))
