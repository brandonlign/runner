#!/usr/bin/env python3
from __future__ import annotations
import argparse, itertools, json
from pathlib import Path
import numpy as np
from orbittrace_v22_sonotaco_grouped_oof_ranker_v1 import train_evaluate as v22
from orbittrace_v24_twohead_worst_prediction_v1 import train_evaluate as v24
from orbittrace_v19_quality_consensus_fusion_v1 import run_variants_pretruth as v19

FEATURE_DIM=71; RECOVERY=0.5
EXPECTED={2013:(0.14888037368183737,9,11),2014:(0.15198123772301594,9,9)}

def require(ok,msg):
    if not ok: raise RuntimeError(msg)

def make_order(base_order, removed_slots, incoming_ids):
    top=list(base_order[:len(removed_slots[0])]) if False else None

def main():
    p=argparse.ArgumentParser(); p.add_argument('--payload-root',type=Path,required=True); p.add_argument('--truth-root',type=Path,required=True); p.add_argument('--ranker-source',type=Path,required=True); p.add_argument('--output',type=Path,required=True); a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    require(v22.sha(a.ranker_source)==v24.RANKER_SOURCE_SHA,'#839 ranker changed'); ranker=v22.load_module(a.ranker_source,'frozen_839_v31_labelset_diag')
    truth={}; frozen={}
    for r,y in v24.PANELS: truth[(r,y)]=json.loads((a.truth_root/f'truth_{r}_{y}.json').read_text()); frozen[(r,y)]=json.loads((a.truth_root/f'evaluation_{r}_{y}.json').read_text())
    data={}; Xs=[]; A=[]; B=[]; groups=[]; offsets={}; cursor=0
    for r in v24.ROUTES:
        root=a.payload_root/r; meta=json.loads((root/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text()); fp=json.loads((root/'family_memberships.json').read_text()); ids=list(map(str,meta['family_ids'])); fams=fp['families']; X=np.load(root/'features.npy',allow_pickle=False); C=np.load(root/'centroids.npy',allow_pickle=False)
        require(meta['truth_accessed'] is False and fp['truth_accessed'] is False and meta['feature_dimension']==FEATURE_DIM,'invalid pretruth'); require([str(f['family_id']) for f in fams]==ids and X.shape==(len(ids),71) and C.shape==(len(ids),8) and v22.array_sha(X)==meta['feature_sha256'] and v22.array_sha(C)==meta['centroid_sha256'],'payload identity changed')
        by={y:truth[(r,y)] for y in v24.YEARS}; eligible=v22.eligible_from_year_truth(by); hidden={}; hidden.update(by[2013]); hidden.update(by[2014]); base=[v22.family_truth(f,hidden,eligible) for f in fams]
        q13=[]; q14=[]; rg=[]
        for i,(fam,t) in enumerate(zip(fams,base)):
            lab=t['best_label']; rg.append('SHOWER/'+str(lab) if lab is not None else f'NEG/{r}/{ids[i]}'); x13,x14=(0.0,0.0) if (not t['positive'] or lab is None) else v24.annual_f1_for_fixed_label(fam,str(lab),by); q13.append(float(x13)); q14.append(float(x14))
        offsets[r]=(cursor,cursor+len(ids)); cursor+=len(ids); Xs.append(X); A.append(np.asarray(q13,float)); B.append(np.asarray(q14,float)); groups.extend(rg); data[r]={'meta':meta,'fams':fams,'ids':ids,'C':C,'groups':rg,'y13':np.asarray(q13,float),'y14':np.asarray(q14,float)}
    X=np.vstack(Xs); y13=np.concatenate(A); y14=np.concatenate(B); folds=np.asarray([v22.v1.deterministic_fold(g) for g in groups]); m13=np.zeros(cursor); m14=np.zeros(cursor)
    for f in range(5):
        tr=folds!=f; te=folds==f; require({groups[i] for i in np.where(tr)[0]}.isdisjoint({groups[i] for i in np.where(te)[0]}),'group leakage'); mu=X[tr].mean(0); sd=X[tr].std(0,ddof=0); scale=sd.copy(); scale[scale==0]=1.; Ztr=(X[tr]-mu)/scale; Zte=(X[te]-mu)/scale; teidx=np.where(te)[0]
        for yy,out in ((y13,m13),(y14,m14)):
            pos=yy[tr]>RECOVERY; neg=~pos; P=Ztr[pos]; N=Ztr[neg]; require(len(P)>0 and len(N)>0,'missing references')
            for j,gi in enumerate(teidx): out[gi]=float(np.min(np.linalg.norm(N-Zte[j],axis=1))-np.min(np.linalg.norm(P-Zte[j],axis=1)))
    score=np.minimum(m13,m14); lo,hi=offsets['hdbscan']; rd=data['hdbscan']; ids=rd['ids']; tie=[(int(rd['meta']['tie_rank'][i]),ids[i]) for i in range(len(ids))]; idx=ranker.diversity_order(score[lo:hi],rd['C'],0.8,1.0,tie); local=[ids[i] for i in idx]; base19=list(map(str,rd['meta']['v19_order'])); order=list(v19.fusion_orders(local,base19)['rank_sum']); ranked=v22.rerank(rd['fams'],order); byid={fid:i for i,fid in enumerate(ids)}
    annual_out={}
    for year in (2013,2014):
        expm,expr,budget=EXPECTED[year]; cur=v22.evaluate(ranked,truth[('hdbscan',year)],budget); require(abs(cur['macro_f1']-expm)<1e-12 and cur['recovered_f1_gt_0_5']==expr,f'v31 reproduction failed {year}')
        annual=rd['y13'] if year==2013 else rd['y14']; lit=frozen[('hdbscan',year)]['comparator_summary']; lm=float(lit['macro_f1']); lr=int(lit['recovered_f1_gt_0_5']); top=list(order[:budget]); top_groups={rd['groups'][byid[fid]] for fid in top}; group_members={}
        for i,g in enumerate(rd['groups']):
            if g.startswith('SHOWER/') and float(annual[i])>RECOVERY: group_members.setdefault(g,[]).append(i)
        incoming=[]
        for g,inds in sorted(group_members.items()):
            if g in top_groups: continue
            best=sorted(inds,key=lambda i:(-float(annual[i]),ids[i]))[0]; incoming.append({'group':g,'family_id':ids[best],'annual_f1':float(annual[best])})
        def eval_conf(removed_slots, chosen):
            newtop=list(top); removed_ids=[]
            for slot,item in zip(sorted(removed_slots),sorted(chosen,key=lambda z:z['group'])):
                removed_ids.append(newtop[slot]); newtop[slot]=item['family_id']
            require(len(set(newtop))==budget,'substitution produced duplicate family'); used=set(newtop); full=newtop+[fid for fid in order if fid not in used]; ev=v22.evaluate(v22.rerank(rd['fams'],full),truth[('hdbscan',year)],budget); passed=bool(float(ev['macro_f1'])>lm and int(ev['recovered_f1_gt_0_5'])>=lr)
            return {'removed_slots':[int(s+1) for s in sorted(removed_slots)],'removed_family_ids':sorted(removed_ids),'incoming_groups':sorted(x['group'] for x in chosen),'incoming_family_ids':sorted(x['family_id'] for x in chosen),'macro_f1':float(ev['macro_f1']),'recovered_f1_gt_0_5':int(ev['recovered_f1_gt_0_5']),'gate_pass':passed}
        results={}
        for k in (1,2):
            rows=[]
            for slots in itertools.combinations(range(budget),k):
                for chosen in itertools.combinations(incoming,k): rows.append(eval_conf(slots,chosen))
            require(rows,f'no substitution configs k={k} year={year}'); rows.sort(key=lambda r:(not r['gate_pass'],-r['macro_f1'],-r['recovered_f1_gt_0_5'],tuple(r['removed_family_ids']),tuple(r['incoming_groups']))); best=rows[0]; results[str(k)]={'configurations_evaluated':len(rows),'gate_passing_configurations':int(sum(r['gate_pass'] for r in rows)),'any_gate_pass':bool(any(r['gate_pass'] for r in rows)),'best':best}
        minimum=1 if results['1']['any_gate_pass'] else (2 if results['2']['any_gate_pass'] else None)
        annual_out[str(year)]={'budget':budget,'v31':{'macro_f1':float(cur['macro_f1']),'recovered_f1_gt_0_5':int(cur['recovered_f1_gt_0_5'])},'literature':{'macro_f1':lm,'recovered_f1_gt_0_5':lr},'top_budget_families':top,'top_budget_groups':[rd['groups'][byid[fid]] for fid in top],'incoming_missed_recoverable_groups':incoming,'substitution_results':results,'minimum_substitutions_to_gate_within_two':minimum if minimum is not None else 'NONE_WITHIN_TWO'}
    result={'verdict':'PASS_V31_HDB_LABELSET_SUBSTITUTION_DIAGNOSTIC','scientific_role':'POST_RESULT_TRUTH_AWARE_ORACLE_DIAGNOSTIC_ONLY','annual':annual_out,'substitution_counts_evaluated':[1,2],'three_or_more_substitutions_evaluated':False,'successor_selected':False,'deployable_rank_selected':False,'candidate_membership_changed':False,'feature_search':False,'model_search':False,'metric_search':False,'k_search':False,'threshold_search':False,'diversity_search':False,'fusion_search':False,'post_result_second_search':False,'sonotaco_role':'EXPOSED_DEVELOPMENT_ONLY','maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False,'target_region_events_accessed':False,'blind_exclusion':[20.0,55.0]}
    (a.output/'V31_HDB_LABELSET_SUBSTITUTION_DIAGNOSTIC.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n'); print(json.dumps({'verdict':result['verdict'],'annual':{y:{'minimum':d['minimum_substitutions_to_gate_within_two'],'k1':d['substitution_results']['1'],'k2':d['substitution_results']['2']} for y,d in annual_out.items()}},indent=2,sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
