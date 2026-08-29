#!/usr/bin/env python3
"""Inspect released Euclid FLG/RMS MEF layouts without downloading full files."""
import json, math, urllib.request
from pathlib import Path
import euclid_routed_feasibility as b
OUT=Path('results/euclid_aux_manifest.json'); BLOCK=2880

def rr(url,a,b,timeout=60):
    n=b-a+1; req=urllib.request.Request(url,headers={'Range':f'bytes={a}-{b}','User-Agent':'isef-euclid-manifest/1.0'})
    with urllib.request.urlopen(req,timeout=timeout) as r: data=r.read(n+1); h=dict(r.headers.items()); status=r.status
    if status!=206 or len(data)!=n: raise RuntimeError(f'HTTP {status} got={len(data)} want={n}')
    return data,h

def val(s):
    x=s.split('/',1)[0].strip()
    if x.startswith("'"): return x.strip("'").strip()
    if x in ('T','F'): return x=='T'
    try:return float(x.replace('D','E')) if any(c in x for c in '.EDed') else int(x)
    except:return x

def header(url,pos):
    raw,_=rr(url,pos,pos+131071); d={}; cards=[]; end=None
    for i in range(0,len(raw)-79,80):
        c=raw[i:i+80].decode('ascii',errors='replace'); cards.append(c); k=c[:8].strip()
        if k=='END':end=i+80;break
        if len(c)>=10 and c[8:10]=='= ':d[k]=val(c[10:])
    if end is None: raise RuntimeError(f'no END at {pos}')
    hb=math.ceil(end/BLOCK)*BLOCK
    return d,hb,cards[:30]

def data_bytes(h):
    bit=abs(int(h.get('BITPIX',8))); naxis=int(h.get('NAXIS',0)); n=1
    if naxis==0:n=0
    else:
        for i in range(1,naxis+1): n*=int(h.get(f'NAXIS{i}',0))
    p=int(h.get('PCOUNT',0)); g=int(h.get('GCOUNT',1)); raw=(n*bit//8+p)*g
    return math.ceil(raw/BLOCK)*BLOCK if raw else 0

def inspect(url,max_hdus=8):
    first,h=rr(url,0,1023); total=None
    cr=h.get('Content-Range','')
    if '/' in cr:
        try:total=int(cr.rsplit('/',1)[1])
        except:pass
    pos=0; rows=[]
    for idx in range(max_hdus):
        if total is not None and pos>=total: break
        try:
            hd,hb,cards=header(url,pos); db=data_bytes(hd)
            rows.append({'index':idx,'offset':pos,'header_bytes':hb,'data_bytes':db,'keys':sorted(hd.keys()),'xtension':hd.get('XTENSION'),'extname':hd.get('EXTNAME'),'bitpix':hd.get('BITPIX'),'naxis':hd.get('NAXIS'),'naxis1':hd.get('NAXIS1'),'naxis2':hd.get('NAXIS2'),'sample_cards':cards[:12]})
            pos += hb+db
        except Exception as e:
            rows.append({'index':idx,'offset':pos,'error':f'{type(e).__name__}: {e}'});break
    return {'url':url,'total_bytes':total,'hdus':rows}

def main():
    out={'success':True,'products':[]}
    for epoch in (0,10):
      sci=b.FILES[epoch]
      for suffix in ('_flg.fits','_rms.fits'):
        fn=sci.replace('_sci.fits',suffix); url=f'{b.BASE}/{fn}'
        try:r=inspect(url)
        except Exception as e:r={'url':url,'error':f'{type(e).__name__}: {e}'}
        r['epoch']=epoch;r['file']=fn;out['products'].append(r)
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
