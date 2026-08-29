#!/usr/bin/env python3
"""Field-neutral adapter for Euclid Q2 VIS single-dither products.

The existing Stage-0 modules were developed against Field 1 and expose their
16 science URLs through globals in ``euclid_routed_feasibility``.  This adapter
changes only those data-location globals, based on the frozen Q2 field/dither
mapping.  Detector algorithms and thresholds are untouched.
"""
import re,urllib.request
import euclid_routed_feasibility as b

BASE='https://irsa.ipac.caltech.edu/data/Euclid/q2/data'
FIELD_CENTERS={
 1:(267.425,-30.019),2:(267.441,-29.259),3:(267.456,-28.499),
 4:(268.248,-28.610),5:(268.237,-29.369),6:(268.227,-30.129),
 7:(269.030,-30.236),8:(269.036,-29.476),9:(269.041,-28.716),
}
_CACHE=None

def index_names():
 global _CACHE
 if _CACHE is not None:return _CACHE
 req=urllib.request.Request(BASE+'/',headers={'User-Agent':'isef-euclid-field-runtime/1.0'})
 with urllib.request.urlopen(req,timeout=90) as r:txt=r.read().decode('utf-8','replace')
 _CACHE=sorted(set(re.findall(r'href="([^"]+\.fits)"',txt)))
 return _CACHE

def files_for_field(field):
 if field not in FIELD_CENTERS:raise ValueError('field must be 1..9')
 start=(field-1)*16; by={}
 for n in index_names():
  m=re.match(r'^EUC_VIS_SWL-DET-067070-(\d+)-1__[^/]+_sci\.fits$',n)
  if m:
   d=int(m.group(1))
   if start<=d<start+16:by[d]=n
 missing=[d for d in range(start,start+16) if d not in by]
 if missing:raise RuntimeError(f'Field {field}: missing science files for dithers {missing}')
 return [by[d] for d in range(start,start+16)]

def activate_field(field):
 files=files_for_field(field)
 b.FILES=files
 b.URLS=[BASE+'/'+f for f in files]
 # clear any module-level caches used by header readers when present
 for name in ('_HDR_CACHE','HDR_CACHE','_RANGE_CACHE','RANGE_CACHE'):
  obj=getattr(b,name,None)
  if hasattr(obj,'clear'):obj.clear()
 return {'field':field,'center':FIELD_CENTERS[field],'files':files,'urls':list(b.URLS)}
