#!/usr/bin/env python3
"""Diagnostic only: locate why the frozen PHANGS equations fail their own published labels.
No NGC1427A data; no thresholds are changed or optimized.
"""
import json,math,urllib.request
from pathlib import Path
URL='https://cdsarc.cds.unistra.fr/ftp/J/MNRAS/511/6087/table2.dat'
OUT=Path('results/ngc1427a_phangs_control_diagnostic.json');OUT.parent.mkdir(exist_ok=True)
MU0={'IC5332':29.77,'NGC0628':29.96,'NGC1087':31.00,'NGC1300':31.39,'NGC1365':31.46,'NGC1385':31.18,'NGC1433':29.78,'NGC1512':30.28,'NGC1566':31.24,'NGC1672':31.44,'NGC2835':30.44,'NGC3351':29.99,'NGC3627':30.27,'NGC4254':30.59,'NGC4303':31.15,'NGC4321':30.91,'NGC4535':30.99,'NGC5068':28.58,'NGC7496':31.36}
MUF={'IC5332':29.73,'NGC0628':29.89,'NGC1087':31.05,'NGC1300':32.06,'NGC1365':31.22,'NGC1385':29.96,'NGC1433':31.39,'NGC1512':31.27,'NGC1566':31.13,'NGC1672':30.99,'NGC2835':30.57,'NGC3351':30.36,'NGC3627':30.18,'NGC4254':29.97,'NGC4303':30.65,'NGC4321':31.10,'NGC4535':31.43,'NGC5068':28.46,'NGC7496':31.64}
def ff(s):
 try:return float(s.strip())
 except:return float('nan')
def main():
 with urllib.request.urlopen(urllib.request.Request(URL,headers={'User-Agent':'ISEF-PHANGS-diagnostic/1'}),timeout=120) as r: ls=r.read().decode().splitlines()
 rows=[]
 for ln in ls:
  if len(ln)<186:continue
  g=ln[0:7].strip();t=ln[12:15].strip().upper()
  if g not in MU0 or t not in {'PN','SNR'}:continue
  m=ff(ln[41:57]);oh=ff(ln[76:94]);nh=ff(ln[113:131]);sh=ff(ln[150:168])
  if not all(math.isfinite(x) for x in [m,oh,nh,sh]):continue
  R=oh-math.log10(1+10**nh)
  def eq5(mu):return R > -0.37*(m-mu)-1.16
  rows.append({'g':g,'t':t,'m':m,'oh':oh,'nh':nh,'sh':sh,'R':R,'eq5_initial':eq5(MU0[g]),'eq5_final':eq5(MUF[g]),'eq6_pn':sh<=-0.4})
 def counts(key):
  return {t:{'n':sum(x['t']==t for x in rows),'pass':sum(x['t']==t and x[key] for x in rows)} for t in ['PN','SNR']}
 # Quantiles of margins identify sign/column problems without exposing target data.
 def q(a):
  a=sorted(a);return {str(p):a[min(len(a)-1,round(p*(len(a)-1)))] for p in [0,.1,.5,.9,1]} if a else {}
 margins0=[x['R']-(-0.37*(x['m']-MU0[x['g']])-1.16) for x in rows if x['t']=='PN']
 marginsf=[x['R']-(-0.37*(x['m']-MUF[x['g']])-1.16) for x in rows if x['t']=='PN']
 o={'status':'DIAGNOSTIC_ONLY','ngc1427a_accessed':False,'n':len(rows),'eq5_initial':counts('eq5_initial'),'eq5_final':counts('eq5_final'),'eq6_pn_side':counts('eq6_pn'),'pn_margin_initial_quantiles':q(margins0),'pn_margin_final_quantiles':q(marginsf),'first_three_published_rows':rows[:3],'note':'No threshold tuning. Published paper states all table PN and SNR entries satisfy Eq.5; SNR entries then fail Eq.6. Any disagreement proves implementation/input mismatch.'}
 OUT.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');print(json.dumps(o,indent=2,sort_keys=True))
if __name__=='__main__':main()
