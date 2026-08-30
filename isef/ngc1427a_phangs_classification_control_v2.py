#!/usr/bin/env python3
"""Corrected external PHANGS-MUSE PN/SNR classification control.

Correction is literature-driven, not outcome-tuned: Scheuermann+2022 Sec 2.4
states that objects consistent within their measurement uncertainty with being a
PN are retained. v1 incorrectly hard-cut central values. No NGC1427A data used.
"""
import json,math,urllib.request
from pathlib import Path
URL='https://cdsarc.cds.unistra.fr/ftp/J/MNRAS/511/6087/table2.dat'
OUT=Path('results/ngc1427a_phangs_classification_control_v2.json');OUT.parent.mkdir(exist_ok=True)
# Converged PNLF moduli from Scheuermann+2022 Table 3.
MU={'IC5332':29.73,'NGC0628':29.89,'NGC1087':31.05,'NGC1300':32.06,'NGC1365':31.22,'NGC1385':29.96,'NGC1433':31.39,'NGC1512':31.27,'NGC1566':31.13,'NGC1672':30.99,'NGC2835':30.57,'NGC3351':30.36,'NGC3627':30.18,'NGC4254':29.97,'NGC4303':30.65,'NGC4321':31.10,'NGC4535':31.43,'NGC5068':28.46,'NGC7496':31.64}
def f(s):
 try:return float(s.strip())
 except:return float('nan')
def main():
 with urllib.request.urlopen(urllib.request.Request(URL,headers={'User-Agent':'ISEF-PHANGS-control-v2/1'}),timeout=120) as r: lines=r.read().decode().splitlines()
 rows=[]
 for ln in lines:
  if len(ln)<186:continue
  g=ln[0:7].strip(); typ=ln[12:15].strip().upper()
  if g not in MU or typ not in {'PN','SNR'}:continue
  m,em,oh,eoh,nh,enh,sh,esh=[f(ln[a:b]) for a,b in [(41,57),(58,75),(76,94),(95,112),(113,131),(132,149),(150,168),(169,186)]]
  if not all(math.isfinite(x) for x in [m,em,oh,eoh,nh,enh,sh,esh]):continue
  t=10**nh; R=oh-math.log10(1+t); d=t/(1+t)
  # Approximate 1-sigma propagation for the tabulated log-ratios. This is the
  # literal operationalization of "consistent within the uncertainty" in Sec 2.4.
  sR=math.sqrt(eoh*eoh+(d*enh)**2)
  M=m-MU[g]; boundary=-0.37*M-1.16
  # Retain if the 1-sigma interval overlaps the PN side of Eq.5.
  eq5=(R+sR)>=boundary
  # SNR iff its SII/Ha ratio is significantly on the shock side; retain as PN
  # if the 1-sigma interval still overlaps log(SII/Ha)<=-0.4.
  eq6_pn=(sh-esh)<=-0.40
  pred=eq5 and eq6_pn
  rows.append((g,typ,pred,eq5,eq6_pn))
 pn=[x for x in rows if x[1]=='PN'];snr=[x for x in rows if x[1]=='SNR']
 tp=sum(x[2] for x in pn);fp=sum(x[2] for x in snr)
 recall=tp/len(pn);cont=fp/(tp+fp) if tp+fp else None
 o={'status':'EXTERNAL_PHANGS_SOURCE_LEVEL_CONTROL_V2','ngc1427a_accessed':False,'n_evaluable':len(rows),'pn_total':len(pn),'snr_total':len(snr),'pn_predicted':tp,'snr_predicted_pn':fp,'pn_eq5_consistent':sum(x[3] for x in pn),'pn_eq6_consistent':sum(x[4] for x in pn),'snr_eq5_consistent':sum(x[3] for x in snr),'snr_eq6_consistent_pn_side':sum(x[4] for x in snr),'recall':recall,'contamination_pn_snr_only':cont,'gate_recall_ge_0p80':recall>=.80,'gate_contamination_le_0p10':cont is not None and cont<=.10,'gate_passed':recall>=.80 and cont is not None and cont<=.10,'correction_provenance':'v1 hard-cut central values, contrary to Scheuermann+2022 Sec 2.4 statement that objects consistent within uncertainty with PN are retained. v2 uses 1-sigma interval overlap; thresholds Eq5/Eq6 unchanged.','note':'External source-level classification control only; target detection/completeness still requires blinded injection gate.'}
 OUT.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');print(json.dumps(o,indent=2,sort_keys=True))
if __name__=='__main__':main()
