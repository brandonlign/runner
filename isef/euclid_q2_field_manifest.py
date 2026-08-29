#!/usr/bin/env python3
"""Build a field-neutral Euclid Q2 VIS file manifest from the public IRSA index.

Metadata only: this script does not read FITS science pixels. It freezes the
mapping from Q2 field number to the 16 calibrated VIS science/FLAG/RMS files so
validation/discovery code does not depend on Field-1 hardcoding.
"""
import html,json,re,urllib.request
from pathlib import Path
BASE='https://irsa.ipac.caltech.edu/data/Euclid/q2/data'
INDEX=BASE+'/'
OUT=Path('results/euclid_q2_field_manifest.json');OUT.parent.mkdir(parents=True,exist_ok=True)
CENTERS={1:(267.425,-30.019),2:(267.441,-29.259),3:(267.456,-28.499),4:(268.248,-28.610),5:(268.237,-29.369),6:(268.227,-30.129),7:(269.030,-30.236),8:(269.036,-29.476),9:(269.041,-28.716)}

def main():
 req=urllib.request.Request(INDEX,headers={'User-Agent':'isef-euclid-q2-field-manifest/1.0'})
 with urllib.request.urlopen(req,timeout=90) as r:txt=r.read().decode('utf-8','replace')
 names=[html.unescape(x) for x in re.findall(r'href="([^"]+)"',txt)]
 # Keep split science plane and matching auxiliary maps, not the 6.8G combined MEF.
 pat=re.compile(r'^EUC_VIS_SWL-DET-067070-(\d+)-1__[^/]+_(sci|flg|rms)\.fits$')
 by={i:{'field':i,'center_ra_deg':CENTERS[i][0],'center_dec_deg':CENTERS[i][1],'dither_ids':list(range((i-1)*16,i*16)),'epochs':[]} for i in range(1,10)}
 found={}
 for n in names:
  m=pat.match(n)
  if not m:continue
  d=int(m.group(1));kind=m.group(2)
  if 0<=d<144:found.setdefault(d,{})[kind]=n
 for field in range(1,10):
  start=(field-1)*16
  for e,d in enumerate(range(start,start+16)):
   z=found.get(d,{})
   by[field]['epochs'].append({'epoch':e,'dither_id':d,'science':z.get('sci'),'flag':z.get('flg'),'rms':z.get('rms')})
  by[field]['complete']=all(all(x.get(k) for k in ('science','flag','rms')) for x in by[field]['epochs'])
 out={'success':all(x['complete'] for x in by.values()),'source_index':INDEX,'note':'metadata-only public directory parse; no FITS science pixels read','fields':by}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
