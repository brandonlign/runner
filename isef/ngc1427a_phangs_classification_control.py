#!/usr/bin/env python3
"""External source-level positive control for frozen NGC1427A PN criteria.

Uses only the published Scheuermann+2022 PHANGS-MUSE PN/SNR catalogue and
published Table-3 PNLF moduli. No NGC1427A data are accessed.
"""
import json, math, urllib.request
from pathlib import Path
URL='https://cdsarc.cds.unistra.fr/ftp/J/MNRAS/511/6087/table2.dat'
OUT=Path('results/ngc1427a_phangs_classification_control.json'); OUT.parent.mkdir(exist_ok=True)
MU={
'IC5332':29.73,'NGC0628':29.89,'NGC1087':31.05,'NGC1300':32.06,'NGC1365':31.22,
'NGC1385':29.96,'NGC1433':31.39,'NGC1512':31.27,'NGC1566':31.13,'NGC1672':30.99,
'NGC2835':30.57,'NGC3351':30.36,'NGC3627':30.18,'NGC4254':29.97,'NGC4303':30.65,
'NGC4321':31.10,'NGC4535':31.43,'NGC5068':28.46,'NGC7496':31.64}

def f(s):
    try:return float(s.strip())
    except:return float('nan')

def main():
    req=urllib.request.Request(URL,headers={'User-Agent':'ISEF-NGC1427A-PHANGS-control/1.0'})
    with urllib.request.urlopen(req,timeout=120) as r: lines=r.read().decode('ascii','replace').splitlines()
    rows=[]
    for ln in lines:
        if len(ln)<186: continue
        gal=ln[0:7].strip().replace(' ',''); typ=ln[12:15].strip().upper()
        if gal not in MU or typ not in {'PN','SNR'}: continue
        m=f(ln[41:57]); loh=f(ln[76:94]); lnh=f(ln[113:131]); lsh=f(ln[150:168])
        if not all(math.isfinite(x) for x in [m,loh,lnh,lsh]): continue
        # Published diagnostic: OIII / (Halpha + NII6583)
        R=loh-math.log10(1.0+10.0**lnh)
        M=m-MU[gal]
        boundary=-0.37*M-1.16
        hii_pass=R>boundary
        shock=(lsh>-0.40)
        pred_pn=bool(hii_pass and not shock)
        rows.append((gal,typ,pred_pn,R,boundary,lsh))
    pn=[x for x in rows if x[1]=='PN']; snr=[x for x in rows if x[1]=='SNR']
    tp=sum(x[2] for x in pn); fn=len(pn)-tp; fp=sum(x[2] for x in snr); tn=len(snr)-fp
    recall=tp/len(pn) if pn else None
    precision=tp/(tp+fp) if tp+fp else None
    contamination=fp/(tp+fp) if tp+fp else None
    by={}
    for g in MU:
        q=[x for x in rows if x[0]==g]
        if not q: continue
        p=[x for x in q if x[1]=='PN']; s=[x for x in q if x[1]=='SNR']; t=sum(x[2] for x in p); ff=sum(x[2] for x in s)
        by[g]={'n':len(q),'pn':len(p),'snr':len(s),'pn_recall':t/len(p) if p else None,'snr_false_pn':ff}
    o={'status':'EXTERNAL_PHANGS_SOURCE_LEVEL_CONTROL','source':'Scheuermann+2022 VizieR J/MNRAS/511/6087/table2','ngc1427a_accessed':False,
       'n_rows_evaluable':len(rows),'pn_total':len(pn),'snr_total':len(snr),'tp_pn':tp,'fn_pn':fn,'fp_snr_as_pn':fp,'tn_snr':tn,
       'recall':recall,'precision_against_pn_snr_only':precision,'contamination_against_pn_snr_only':contamination,'by_galaxy':by,
       'gate_recall_ge_0p80':bool(recall is not None and recall>=0.80),'gate_contamination_le_0p10':bool(contamination is not None and contamination<=0.10),
       'gate_passed':bool(recall is not None and contamination is not None and recall>=0.80 and contamination<=0.10),
       'note':'This validates only published line-ratio classification on a PN+SNR-labelled external MUSE catalogue; it does not validate NGC1427A detection/completeness or HII-region rejection in a full blind candidate set.'}
    OUT.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n'); print(json.dumps(o,indent=2,sort_keys=True))
if __name__=='__main__': main()
