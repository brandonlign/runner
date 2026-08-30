#!/usr/bin/env python3
"""APO-only visit-level RV replication calibration for the DR20 extreme-speed project.
Development only; no LCO source identities or LCO visit outcomes are emitted.
"""
from pathlib import Path
import json,urllib.request,gzip,shutil
import numpy as np
from astropy.io import fits
OUT=Path('results/sdss_dr20_apo_visit_rv_calibration.json');OUT.parent.mkdir(parents=True,exist_ok=True)
STAR='https://dr20.sdss.org/sas/dr20/spectro/astra/0.8.1/summary/mwmAllStar-0.8.1.fits.gz'
VIS='https://dr20.sdss.org/sas/dr20/spectro/astra/0.8.1/summary/mwmAllVisit-0.8.1.fits.gz'
def dl(url,p):
 req=urllib.request.Request(url,headers={'User-Agent':'ISEF-DR20-APO-VisitCal/1.0'})
 with urllib.request.urlopen(req,timeout=300) as r,open(p,'wb') as f:
  while True:
   b=r.read(8<<20)
   if not b:break
   f.write(b)
def ungz(gz,ff):
 with gzip.open(gz,'rb') as a,open(ff,'wb') as b:shutil.copyfileobj(a,b,length=8<<20)
def table(ff,need):
 with fits.open(ff,memmap=True) as h:
  cc=[x.data for x in h[1:] if getattr(x,'data',None) is not None and hasattr(x.data,'names') and all(k in x.data.names for k in need) and len(x.data)>0]
  if not cc:raise RuntimeError('required table absent: '+str(need))
  # return copied selected columns to close FITS safely
  d=max(cc,key=len);return {k:np.array(d[k]) for k in need}
def q(x):
 x=np.asarray(x,float);x=x[np.isfinite(x)]
 return {str(p):float(np.quantile(x,p)) for p in [0,.5,.9,.95,.99,.999,1]} if len(x) else {}
def main():
 out={'success':False,'status':'APO_VISIT_RV_CALIBRATION','lco_source_outcomes_accessed':False,'identities_emitted':False}
 try:
  sg=Path('/tmp/s.gz');sf=Path('/tmp/s.fits');vg=Path('/tmp/v.gz');vf=Path('/tmp/v.fits');dl(STAR,sg);ungz(sg,sf);dl(VIS,vg);ungz(vg,vf)
  sk=['sdss_id','telescope','v_rad','e_v_rad','std_v_rad','snr','n_good_rvs','zwarning_flags','nmf_flags'];s=table(sf,sk)
  st=np.char.lower(np.char.strip(s['telescope'].astype(str)));apo=st=='apo25m';v=s['v_rad'].astype(float);ev=s['e_v_rad'].astype(float);sv=s['std_v_rad'].astype(float);sn=s['snr'].astype(float);ng=s['n_good_rvs'].astype(int);zw=s['zwarning_flags'].astype(np.int64);nm=s['nmf_flags'].astype(np.int64)
  base=apo&np.isfinite(v)&np.isfinite(ev)&np.isfinite(sv)&np.isfinite(sn)&(sn>10)&(ev<30)&(ng>=2)&(sv<=30)&(zw==0)&(nm==0)&(np.abs(v)>300)
  ids=s['sdss_id'][base].astype(np.int64);summ=v[base]
  # Only development APO identities are used internally for join and never emitted.
  smap={int(i):float(x) for i,x in zip(ids,summ)}
  vk=['sdss_id','telescope','xcsao_v_rad','xcsao_e_v_rad','xcsao_rxc','snr','zwarning_flags'];vv=table(vf,vk);vt=np.char.lower(np.char.strip(vv['telescope'].astype(str)))
  by={}
  for i,tel,rv,e,rxc,snr,z in zip(vv['sdss_id'],vt,vv['xcsao_v_rad'],vv['xcsao_e_v_rad'],vv['xcsao_rxc'],vv['snr'],vv['zwarning_flags']):
   ii=int(i)
   if tel!='apo25m' or ii not in smap:continue
   try: rv=float(rv);e=float(e);rxc=float(rxc);snr=float(snr);z=int(z)
   except:continue
   if not(np.isfinite(rv) and np.isfinite(e) and np.isfinite(rxc) and np.isfinite(snr)):continue
   if e>=30 or snr<=10 or z!=0:continue
   by.setdefault(ii,[]).append((rv,e,rxc))
  meddiff=[];robsc=[];nvis=[];agree20=[];agree30=[];agree50=[];rxc=[]
  usable=0
  for i,x in smap.items():
   a=by.get(i,[])
   if len(a)<2:continue
   rr=np.array([z[0] for z in a]);usable+=1;nvis.append(len(rr));m=float(np.median(rr));meddiff.append(abs(m-x));robsc.append(float(1.4826*np.median(np.abs(rr-m))));agree20.append(int(np.sum(np.abs(rr-x)<=20)));agree30.append(int(np.sum(np.abs(rr-x)<=30)));agree50.append(int(np.sum(np.abs(rr-x)<=50)));rxc.extend([z[2] for z in a])
  md=np.array(meddiff);rs=np.array(robsc);nv=np.array(nvis);a20=np.array(agree20);a30=np.array(agree30);a50=np.array(agree50)
  out.update(apo_extreme_rv300_summary_n=int(len(smap)),apo_with_ge2_quality_visits=int(usable),median_summary_difference_kms=q(md),robust_visit_scatter_kms=q(rs),quality_visit_count=q(nv),xcsao_rxc=q(rxc),fractions={
   'median_within20':float(np.mean(md<=20)) if usable else None,'median_within30':float(np.mean(md<=30)) if usable else None,'median_within50':float(np.mean(md<=50)) if usable else None,'scatter_le20':float(np.mean(rs<=20)) if usable else None,'scatter_le30':float(np.mean(rs<=30)) if usable else None,'atleast2_within30':float(np.mean(a30>=2)) if usable else None,'atleast2_within50':float(np.mean(a50>=2)) if usable else None})
  out['success']=True;out['decision']='APO_VISIT_CALIBRATION_READY' if usable>=100 else 'APO_VISIT_CALIBRATION_TOO_SMALL'
 except Exception as e:
  out['error']=f'{type(e).__name__}: {e}';out['decision']='INFRASTRUCTURE_FAILURE_NO_SCIENTIFIC_DECISION'
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
