#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
from orbittrace_v23_worst_year_oof_ranker_v1 import train_evaluate as v23
from orbittrace_v24_two_head_annual_oof_ranker_v1 import train_evaluate as v24
from orbittrace_sonotaco_group_recoverability_oof_v1 import train_evaluate as gr
EXPECTED={'v24':{'sugar':('8cbf4366f6591cdae1314f9c66e9fce12c2d7c414d03a0b378bbeb86c0fe87f8','04bef1a6b145324c63ab0acf2dcdd8bfc4f58385db75aacf53713dc038cdd052'),'hdbscan':('a087685b5deda68ddfd721cc446ab6c2bb522d70c738678270176d5362b06034','ebab51e28d2c4dc606ec966ca9d87606fbeecb5a903c2d1cb9c497858df27c86')},'gr':{'sugar':('460459ea272e7275fe537a22ebbe182ec4cdb8aa6b4403c1c93983a447c5d711','5b2042d873d3fb41a83b6906cd3a4363daf4b0b200980667a81cd67c1590a1df'),'hdbscan':('7701373d421b853a1d2a716f1dd1b7cb99a81337f15ecc38c05f3df577a90744','f77da004ad382bca29bb8e6638d698f832735754a60f50b6e29faa9f980c3ca6')}}
def req(x,m):
    if not x: raise RuntimeError(m)
def osh(a): return hashlib.sha256('\n'.join(a).encode()).hexdigest()
def fuse3(a,b,c):
    req(set(a)==set(b)==set(c),'fusion universe mismatch'); p=[{x:i+1 for i,x in enumerate(o)} for o in (a,b,c)]
    return sorted(a,key=lambda x:(sum(q[x] for q in p),max(q[x] for q in p),min(q[x] for q in p),x))
def run_parent(mod,kind,args,out):
    captured=[]; old=v23.load_module
    def load(path,name):
        m=old(path,name); od=m.diversity_order
        def div(scores,centroids,lam,scale,tie):
            idx=od(scores,centroids,lam,scale,tie); ids=[str(t[1]) for t in tie]; captured.append([ids[i] for i in idx]); return idx
        m.diversity_order=div; return m
    v23.load_module=load
    try:
        sys.argv=[kind,'--sugar-root',str(args.sugar_root),'--hdbscan-root',str(args.hdbscan_root),'--truth-root',str(args.truth_root),'--ranker-source',str(args.ranker_source),'--output',str(out)]
        req(mod.main()==0,f'{kind} parent failed')
    finally: v23.load_module=old
    req(len(captured)==2,f'{kind} did not expose exactly two diversity orders'); return {'sugar':captured[0],'hdbscan':captured[1]}
def main():
    p=argparse.ArgumentParser()
    for n in ('sugar_root','hdbscan_root','truth_root','ranker_source','output'): p.add_argument('--'+n.replace('_','-'),dest=n,type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    v24o=run_parent(v24,'v24',a,a.output/'parent_v24'); gro=run_parent(gr,'gr',a,a.output/'parent_gr')
    r24=json.load(open(a.output/'parent_v24/V24_EXPOSED_TWO_HEAD_OOF_RESULT.json')); rg=json.load(open(a.output/'parent_gr/SONOTACO_GROUP_RECOVERABILITY_OOF_RESULT.json'))
    roots={'sugar':a.sugar_root,'hdbscan':a.hdbscan_root}; variants={}; diag={}
    for route in ('sugar','hdbscan'):
        d24=r24['order_diagnostics'][route]; dg=rg['order_diagnostics'][route]
        req((d24['quality_order_sha256'],d24['fused_order_sha256'])==EXPECTED['v24'][route],f'{route} v24 parent identity failed')
        req((dg['classifier_diversity_order_sha256'],dg['fused_order_sha256'])==EXPECTED['gr'][route],f'{route} group parent identity failed')
        req(osh(v24o[route])==EXPECTED['v24'][route][0] and osh(gro[route])==EXPECTED['gr'][route][0],f'{route} captured parent order mismatch')
        meta=json.load(open(roots[route]/'V22_PRETRUTH_FEATURE_MANIFEST.json')); v19=list(map(str,meta['v19_order'])); fused=fuse3(v24o[route],gro[route],v19)
        fams=json.load(open(roots[route]/'family_memberships.json'))['families']; variants[route]=v23.rerank(fams,fused)
        diag[route]={'v24_order_sha256':osh(v24o[route]),'group_order_sha256':osh(gro[route]),'v19_order_sha256':osh(v19),'threeway_order_sha256':osh(fused)}
    panels=[]
    for route,year in v23.PANELS:
        truth=json.load(open(a.truth_root/f'truth_{route}_{year}.json')); ev=json.load(open(a.truth_root/f'evaluation_{route}_{year}.json')); budget=int(ev['candidate_budget']['comparator_budget'])
        cur=v23.evaluate(variants[route],truth,budget); lit=ev['comparator_summary']; cm=float(cur['macro_f1']); cr=int(cur['recovered_f1_gt_0_5']); lm=float(lit['macro_f1']); lr=int(lit['recovered_f1_gt_0_5'])
        panels.append({'comparator':route,'year':year,'budget':budget,'candidate_macro_f1':cm,'literature_macro_f1':lm,'candidate_recovered_f1_gt_0_5':cr,'literature_recovered_f1_gt_0_5':lr,'superiority_pair_pass':bool(cm>lm and cr>=lr)})
    wins=sum(int(x['superiority_pair_pass']) for x in panels); result={'verdict':'PASS_V24_GROUPRECOVERY_RANKFUSION_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if wins==4 else 'FAIL_V24_GROUPRECOVERY_RANKFUSION_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT','panel_wins':wins,'panels':panels,'parent_order_reproduction':diag,'fusion':'equal rank sum of exact v24 diversity order, exact #1004 group-recovery diversity order, and v19','fusion_search':False,'post_result_second_search':False,'sonotaco_role':'EXPOSED_DEVELOPMENT_ONLY','maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False,'target_region_events_accessed':False,'blind_exclusion':[20.0,55.0]}
    (a.output/'V24_GROUPRECOVERY_RANKFUSION_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(json.dumps(result,indent=2,sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
