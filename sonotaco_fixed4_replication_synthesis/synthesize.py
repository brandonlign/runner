#!/usr/bin/env python3
"""Descriptive cross-year synthesis of immutable SonotaCo fixed-4° evidence."""
from __future__ import annotations
import argparse, gzip, hashlib, json, math
from pathlib import Path
from scipy.stats import beta, fisher_exact

HASHES={
 'development_json':'093a173210b4d4d3d1e0ef94ad709bc0d3c65679142dc2ae9826f8bafbf9cc13',
 'development_positive':'1db2dcd4c0de2006eb35a4d38f49ba40b34ce030df3f85f48db8f855126858b2',
 'development_negative':'8cd120edd19542feecfb975f9baed2021b2b13c5aeb76c4cba31f88d1d235812',
 'confirmation_json':'6b24f8be2a686cdf199fb0ffbcf3b491acf86b7377825fafc6c03790408caea5',
 'confirmation_positive':'c7a5ee8de1a2084922cf936466e8739114265f35a90f2c25bb68678caefa73b6',
 'confirmation_negative':'42557562f3f840ce620e3528993aae9c575553f941bef660dcb8ae0e581d5ae9',
}

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def rows(path):
 with gzip.open(path,'rt',encoding='utf-8') as f:
  return [json.loads(line) for line in f if line.strip()]
def ci(x,n):
 return [0.0 if x==0 else float(beta.ppf(.025,x,n-x+1)),1.0 if x==n else float(beta.ppf(.975,x+1,n-x))]
def exact_count(rate,n):
 x=round(rate*n)
 if not math.isclose(x/n,rate,rel_tol=0,abs_tol=1e-12): raise RuntimeError((rate,n,x))
 return x

def main():
 p=argparse.ArgumentParser(); p.add_argument('--development',type=Path,required=True); p.add_argument('--confirmation',type=Path,required=True); p.add_argument('--output',type=Path,required=True); a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
 files={
  'development_json':a.development/'sonotaco_k4_phase_scale_diagnostic.json',
  'development_positive':a.development/'positive_phase_scale_records.jsonl.gz',
  'development_negative':a.development/'negative_phase_scale_records.jsonl.gz',
  'confirmation_json':a.confirmation/'sonotaco_2024_fixed4_confirmation.json',
  'confirmation_positive':a.confirmation/'positive_records.jsonl.gz',
  'confirmation_negative':a.confirmation/'negative_records.jsonl.gz',
 }
 checks={k:sha(v)==HASHES[k] for k,v in files.items()}
 if not all(checks.values()): raise RuntimeError(checks)
 d=json.loads(files['development_json'].read_text()); c=json.loads(files['confirmation_json'].read_text())
 dp=rows(files['development_positive']); dn=rows(files['development_negative']); cp=rows(files['confirmation_positive']); cn=rows(files['confirmation_negative'])
 years={}
 for name,pos,neg in [('2025 development',dp,dn),('2024 confirmation',cp,cn)]:
  year={}
  for alpha in (.05,.01):
   recall={}
   for k in (4,6,8,12):
    subset=[r for r in pos if r['k']==k]
    key=(r['p']['4'] if 'p' in r else r['local_p'] for r in subset)
    x=sum(float(v)<=alpha for v in key); n=len(subset)
    recall[str(k)]={'x':x,'n':n,'rate':x/n,'exact_95_ci':ci(x,n)}
   pvals=[float(r['p']['4'] if 'p' in r else r['local_p']) for r in neg]
   fx=sum(v<=alpha for v in pvals); fn=len(pvals)
   year[str(alpha)]={'recall':recall,'false_positive':{'x':fx,'n':fn,'rate':fx/fn,'exact_95_ci':ci(fx,fn)}}
  years[name]=year
 pooled={}
 for alpha in (.05,.01):
  recall={}
  for k in (4,6,8,12):
   a1=years['2025 development'][str(alpha)]['recall'][str(k)]; a2=years['2024 confirmation'][str(alpha)]['recall'][str(k)]
   x=a1['x']+a2['x']; n=a1['n']+a2['n']
   odds,pv=fisher_exact([[a1['x'],a1['n']-a1['x']],[a2['x'],a2['n']-a2['x']]])
   recall[str(k)]={'x':x,'n':n,'rate':x/n,'exact_95_ci':ci(x,n),'year_heterogeneity_fisher_p':float(pv),'odds_ratio':float(odds)}
  f1=years['2025 development'][str(alpha)]['false_positive']; f2=years['2024 confirmation'][str(alpha)]['false_positive']; x=f1['x']+f2['x']; n=f1['n']+f2['n']
  pooled[str(alpha)]={'recall':recall,'false_positive':{'x':x,'n':n,'rate':x/n,'exact_95_ci':ci(x,n)}}
 result={
  'classification':'DESCRIPTIVE_REPLICATION_SYNTHESIS_NOT_A_CONFIRMATION_RESCUE',
  'immutable_input_checks':checks,
  'year_specific_weak_auc':{'2025_development_fixed4':d['metrics']['by_scale']['4']['weak_auc'],'2024_confirmation_fixed4':c['candidate_weak_auc']},
  'years':years,'pooled_descriptive':pooled,
  'formal_confirmation_verdict':c['verdict'],
  'interpretation':{
   'formal_status':'The preregistered 2024 all-gates confirmation failed and remains failed.',
   'replication':'Calibration, AUROC, folds, alpha-0.05 k=4, and all k=6/k=8 endpoints replicated.',
   'strict_tail':'2024 k=4 alpha-0.01 was 6/132; the gate required 7/132. Descriptively, 2025+2024 was 14/268.',
   'restriction':'The pooled result combines development and confirmation data and cannot replace the one-shot verdict.'
  }
 }
 (a.output/'fixed4_replication_synthesis.json').write_text(json.dumps(result,indent=2))
 lines=['# Fixed-4° SonotaCo replication synthesis','',f"Formal 2024 verdict: **`{c['verdict']}`**",'', '> This is a descriptive synthesis of immutable development and confirmation artifacts. It does not revise or rescue the preregistered confirmation verdict.','', '## Independent 2024 result','',f"- AUROC: **{c['candidate_weak_auc']:.6f}**",f"- k=4 recall at 0.05: **{years['2024 confirmation']['0.05']['recall']['4']['x']}/132 = {years['2024 confirmation']['0.05']['recall']['4']['rate']:.6f}**",f"- k=4 recall at 0.01: **{years['2024 confirmation']['0.01']['recall']['4']['x']}/132 = {years['2024 confirmation']['0.01']['recall']['4']['rate']:.6f}** (one recovery below the frozen gate)",'','## Cross-year descriptive consistency','', '| endpoint | 2025 development | 2024 confirmation | pooled descriptive | Fisher heterogeneity p |','|---|---:|---:|---:|---:|']
 for alpha in (.05,.01):
  key=str(alpha); p4=pooled[key]['recall']['4']; d4=years['2025 development'][key]['recall']['4']; c4=years['2024 confirmation'][key]['recall']['4']
  lines.append(f"| k=4 recall @ {alpha:.2f} | {d4['x']}/{d4['n']} ({d4['rate']:.4f}) | {c4['x']}/{c4['n']} ({c4['rate']:.4f}) | {p4['x']}/{p4['n']} ({p4['rate']:.4f}) | {p4['year_heterogeneity_fisher_p']:.4f} |")
 lines.extend(['',f"- pooled descriptive FPR at 0.05: **{pooled['0.05']['false_positive']['x']}/{pooled['0.05']['false_positive']['n']} = {pooled['0.05']['false_positive']['rate']:.6f}**",f"- pooled descriptive FPR at 0.01: **{pooled['0.01']['false_positive']['x']}/{pooled['0.01']['false_positive']['n']} = {pooled['0.01']['false_positive']['rate']:.6f}**",'', '## Scientific conclusion','', 'The fixed 4° method shows strong, unusually consistent cross-year transfer, but the correct formal statement remains: **broad independent replication with a one-recovery strict-tail confirmation miss**, not a complete confirmation pass.'])
 (a.output/'FIXED4_REPLICATION_SYNTHESIS.md').write_text('\n'.join(lines)+'\n')
 print('\n'.join(lines))
if __name__=='__main__': main()
