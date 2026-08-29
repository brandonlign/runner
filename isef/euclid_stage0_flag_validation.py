#!/usr/bin/env python3
"""Validate morphology-clean Euclid Stage-0 survivor events against released FLAG/RMS maps.

Reads only tiny HTTP byte ranges from the released per-exposure MEFs. No event is
called astrophysical here; the purpose is to test whether candidate-like flux
excursions coincide with pipeline flags or abnormal local RMS.
"""
import json, math, urllib.request
from pathlib import Path
import numpy as np
import euclid_routed_feasibility as b

SURV=Path('results/euclid_stage0_survivors.json')
OUT=Path('results/euclid_stage0_flag_validation.json')
BLOCK=2880

def rr(url,a,b,timeout=60):
    n=b-a+1; req=urllib.request.Request(url,headers={'Range':f'bytes={a}-{b}','User-Agent':'isef-euclid-flags/1.0'})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        data=r.read(n+1); status=r.status; hdr=dict(r.headers.items())
    if status!=206 or len(data)!=n: raise RuntimeError(f'range failure {url} HTTP={status} got={len(data)} want={n}')
    return data,hdr

def card_value(s):
    x=s.split('/',1)[0].strip()
    if x.startswith("'"): return x.strip("'").strip()
    if x in ('T','F'): return x=='T'
    try: return float(x) if any(c in x for c in '.EDed') else int(x)
    except: return x

def parse_header(raw):
    d={}; end=None
    for i in range(0,len(raw)-79,80):
        c=raw[i:i+80].decode('ascii',errors='replace'); k=c[:8].strip()
        if k=='END': end=i+80; break
        if len(c)>=10 and c[8:10]=='= ': d[k]=card_value(c[10:])
    if end is None: raise RuntimeError('FITS END not found')
    size=math.ceil(end/BLOCK)*BLOCK
    return d,size

def layout(url):
    raw,_=rr(url,0,65535); ph,psz=parse_header(raw)
    # primary can have data, though these products normally do not
    pbit=abs(int(ph.get('BITPIX',8))); pn=int(ph.get('NAXIS',0)); count=1
    for ax in range(1,pn+1): count*=int(ph.get(f'NAXIS{ax}',0))
    pbytes=math.ceil((count*pbit//8)/BLOCK)*BLOCK if count else 0
    first=psz+pbytes
    raw2,_=rr(url,first,first+65535); eh,ehsz=parse_header(raw2)
    bit=int(eh['BITPIX']); nx=int(eh['NAXIS1']); ny=int(eh['NAXIS2']); bpp=abs(bit)//8
    data=nx*ny*bpp; stride=ehsz+math.ceil(data/BLOCK)*BLOCK
    return {'primary_offset':first,'header_bytes':ehsz,'stride':stride,'bitpix':bit,'nx':nx,'ny':ny,'extname':eh.get('EXTNAME','')}

def dtype_for(bit):
    return {8:'>u1',16:'>i2',32:'>i4',64:'>i8',-32:'>f4',-64:'>f8'}[bit]

def stamp(url,k,x,y,half=6):
    lay=layout(url); nx=lay['nx']; ny=lay['ny']; bpp=abs(lay['bitpix'])//8
    cx=int(round(float(x))); cy=int(round(float(y))); x0=max(0,cx-half); x1=min(nx,cx+half+1); y0=max(0,cy-half); y1=min(ny,cy+half+1)
    ext=lay['primary_offset']+k*lay['stride']; data0=ext+lay['header_bytes']
    start=data0+y0*nx*bpp; end=data0+y1*nx*bpp-1
    raw,_=rr(url,start,end); rows=np.frombuffer(raw,dtype=dtype_for(lay['bitpix'])).reshape(y1-y0,nx)
    z=rows[:,x0:x1].copy()
    return z,lay,{'x0':x0,'x1':x1,'y0':y0,'y1':y1,'cx':cx,'cy':cy}

def finite_summary(z):
    a=np.asarray(z,float); f=a[np.isfinite(a)]
    if not len(f): return {'finite':0}
    return {'finite':int(len(f)),'min':float(np.min(f)),'median':float(np.median(f)),'max':float(np.max(f)),'p90':float(np.percentile(f,90))}

def main():
    surv=json.loads(SURV.read_text())['survivors']; rows=[]
    # Validate every strict morphology-clean >20% survivor (currently a tiny list).
    for s in surv:
        e=int(s['event_epoch']); k=int(json.loads(Path('results/euclid_routed_feasibility.json').read_text())['routes'][str(e%4)]['k'])
        q=b.getq(e,k); x,y=b.pix(q,float(s['ra']),float(s['dec'])); sci=b.FILES[e]
        rec={'ra':float(s['ra']),'dec':float(s['dec']),'event_epoch':e,'event_sign':s['event_sign'],'max_excursion':float(s['max_excursion']),'k':k,'extname':q.name,'x':float(x),'y':float(y)}
        for kind,suffix in [('flag','_flg.fits'),('rms','_rms.fits')]:
            fn=sci.replace('_sci.fits',suffix); url=f'{b.BASE}/{fn}'
            try:
                z,lay,box=stamp(url,k,x,y); info={'url_file':fn,'layout':lay,'box':box,'summary':finite_summary(z)}
                if kind=='flag':
                    vals,cnt=np.unique(z,return_counts=True); info['unique_values']=[{'value':int(v),'count':int(c)} for v,c in zip(vals,cnt)]; info['center_value']=int(z[z.shape[0]//2,z.shape[1]//2]); info['nonzero_fraction']=float(np.mean(z!=0))
                else:
                    info['center_value']=float(z[z.shape[0]//2,z.shape[1]//2])
                rec[kind]=info
            except Exception as ex: rec[kind]={'error':f'{type(ex).__name__}: {ex}','url_file':fn}
        rows.append(rec)
    out={'success':True,'note':'released FLAG/RMS map validation of strict morphology-clean Stage-0 excursions; nonzero flags require product-bit interpretation before astrophysical claims','events':rows}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__': main()
