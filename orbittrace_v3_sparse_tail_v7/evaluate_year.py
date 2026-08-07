#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path

METHOD='orbittrace_v3_primary_fixed4_margin_025_v7'; V3='orbittrace_multi_anchor_wavelet_energy_v3'; FIXED4='orbittrace_fixed4'; BROWN='brown2010_wavelet_episode_core'
EXPECTED_V3={2025:0.836860,2023:0.836263}

def args():
 p=argparse.ArgumentParser(); p.add_argument('--input',required=True,type=Path); p.add_argument('--year',required=True,type=int); p.add_argument('--output',required=True,type=Path); return p.parse_args()
def close(a,b,t=5e-6): return abs(float(a)-float(b))<=t

def main():
 a=args(); payload=json.loads(a.input.read_text()); m=payload['metrics']; cand=m[METHOD]; brown=m[BROWN]; f4=m[FIXED4]; v3=m[V3]
 rc=cand['recall']['0.05']; rb=brown['recall']['0.05']; rf=f4['recall']['0.05']
 gates={
  'v7_auc_above_brown':float(cand['weak_auc'])>float(brown['weak_auc']),
  'v7_k4_at_least_fixed4':float(rc['4'])>=float(rf['4']),
  'v7_k6_within_003_brown':float(rc['6'])>=float(rb['6'])-0.03,
  'v7_k8_within_003_brown':float(rc['8'])>=float(rb['8'])-0.03,
  'v7_k12_within_003_brown':float(rc['12'])>=float(rb['12'])-0.03,
  'v7_fpr_005_at_most_0055':float(cand['fpr']['0.05'])<=0.055,
  'v7_worst_sector_fpr_005_at_most_008':float(cand['worst_sector_fpr_005'])<=0.08,
  'v3_auc_reproduced':close(v3['weak_auc'],EXPECTED_V3[a.year]),
  'upstream_integrity':all(bool(x) for x in payload['gates'].values()),
 }
 verdict=f"PASS_V7_{a.year}_DEVELOPMENT" if all(gates.values()) else f"FAIL_V7_{a.year}_DEVELOPMENT"
 out={'verdict':verdict,'year':a.year,'metrics':{'v7_weak_auc':cand['weak_auc'],'brown_weak_auc':brown['weak_auc'],'v3_weak_auc':v3['weak_auc'],'fixed4_weak_auc':f4['weak_auc'],'v7_fpr_005':cand['fpr']['0.05'],'v7_worst_sector_fpr_005':cand['worst_sector_fpr_005'],'v7_recall_005':rc,'brown_recall_005':rb,'fixed4_recall_005':rf},'gates':gates}
 a.output.mkdir(parents=True,exist_ok=True); (a.output/f'V7_{a.year}_DEVELOPMENT.json').write_text(json.dumps(out,indent=2)+'\n')
 lines=[f'# OrbitTrace v7 — {a.year}','',f'Verdict: **`{verdict}`**','',f"v7 AUROC **{float(cand['weak_auc']):.6f}** vs Brown **{float(brown['weak_auc']):.6f}**",'',f"FPR .05 **{float(cand['fpr']['0.05']):.6f}**; worst sector **{float(cand['worst_sector_fpr_005']):.6f}**",'','Recall k=4/6/8/12: **'+' / '.join(f"{float(rc[str(k)]):.6f}" for k in (4,6,8,12))+'**','','## Gates','']+[f"- {'PASS' if ok else 'FAIL'} — `{name}`" for name,ok in gates.items()]
 (a.output/f'V7_{a.year}_DEVELOPMENT.md').write_text('\n'.join(lines)+'\n'); print('\n'.join(lines))
if __name__=='__main__': main()
