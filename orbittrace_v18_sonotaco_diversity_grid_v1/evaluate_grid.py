#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_v16_v15_joint_conformal_membership_v1.evaluate_exposed import evaluate

LAMBDAS=(0.0,0.2,0.4,0.6,0.8)
SCALES=(0.75,1.0,1.5)
PANELS=(('sugar',2013),('sugar',2014),('hdbscan',2013),('hdbscan',2014))
V17_FAMILY_SHA={'sugar':'f019263cc23db60156324e0d24d327e3468638e3ef041b1aba7bd50dd0b03ca7','hdbscan':'3010de4819e16d218f083b8d645c2443f7d2d3dfc81723f488a97150a49358ed'}
V17_METRICS={
    ('sugar',2013):(0.2772197612820636,15),('sugar',2014):(0.3169578830313374,17),
    ('hdbscan',2013):(0.12010507969574384,6),('hdbscan',2014):(0.11542944613677675,6),
}


def require(ok: bool,msg: str)->None:
    if not ok: raise RuntimeError(msg)

def canonical_sha(obj: Any)->str:
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def tag(lam: float,scale: float)->str:
    def f(x: float)->str:
        s=(f'{x:.2f}').rstrip('0').rstrip('.')
        return s.replace('.','p')
    return f'lambda_{f(lam)}__scale_{f(scale)}'

def displacement(lam: float,scale: float)->float:
    return math.sqrt(((lam-0.8)/0.8)**2+((scale-1.0)/0.75)**2)


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--grid-root',type=Path,required=True)
    p.add_argument('--truth-root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.parent.mkdir(parents=True,exist_ok=True)

    manifests={}
    for comparator in ('sugar','hdbscan'):
        m=json.loads((a.grid_root/comparator/'V18_PRETRUTH_GRID_MANIFEST.json').read_text())
        require(m['verdict']=='PASS_V18_ALL_15_PRETRUTH_GRID_OUTPUTS_FROZEN',f'{comparator} grid not frozen')
        require(m['truth_accessed'] is False and m['target_information_access'] is False and m['maarsy_scientific_access'] is False and m['dms_scientific_access'] is False,'firewall violation')
        manifests[comparator]=m
        v17_path=a.grid_root/comparator/tag(0.8,1.0)/'candidate_primary_output.json'
        v17=json.loads(v17_path.read_text())
        require(canonical_sha(v17['families'])==V17_FAMILY_SHA[comparator],f'{comparator} v17 grid point does not reproduce frozen v17 families')

    truth={}
    frozen={}
    for comparator,year in PANELS:
        truth[(comparator,year)]=json.loads((a.truth_root/f'truth_{comparator}_{year}.json').read_text())
        frozen[(comparator,year)]=json.loads((a.truth_root/f'evaluation_{comparator}_{year}.json').read_text())

    rows=[]
    for lam in LAMBDAS:
        for scale in SCALES:
            cfg=tag(lam,scale); panels=[]
            for comparator,year in PANELS:
                candidate=json.loads((a.grid_root/comparator/cfg/'candidate_primary_output.json').read_text())
                budget=int(frozen[(comparator,year)]['candidate_budget']['comparator_budget'])
                cur=evaluate(candidate['families'],truth[(comparator,year)],budget)
                comp=frozen[(comparator,year)]['comparator_summary']
                cm=float(cur['macro_f1']); cr=int(cur['recovered_f1_gt_0_5']); lm=float(comp['macro_f1']); lr=int(comp['recovered_f1_gt_0_5'])
                macro_ratio=cm/lm if lm>0 else float('inf'); recovery_ratio=cr/lr if lr>0 else float('inf')
                win=bool(cm>lm and cr>=lr)
                if abs(lam-0.8)<1e-15 and abs(scale-1.0)<1e-15:
                    vm,vr=V17_METRICS[(comparator,year)]
                    require(abs(cm-vm)<1e-12 and cr==vr,f'v17 metric reproduction failed {comparator} {year}: {(cm,cr)} != {(vm,vr)}')
                panels.append({'comparator':comparator,'year':year,'budget':budget,'candidate_macro_f1':cm,'literature_macro_f1':lm,'candidate_recovered_f1_gt_0_5':cr,'literature_recovered_f1_gt_0_5':lr,'macro_f1_ratio':macro_ratio,'recovery_ratio':recovery_ratio,'superiority_pair_pass':win})
            wins=sum(int(x['superiority_pair_pass']) for x in panels)
            min_macro=min(x['macro_f1_ratio'] for x in panels); min_rec=min(x['recovery_ratio'] for x in panels)
            mean_macro=float(np.mean([x['macro_f1_ratio'] for x in panels])); mean_rec=float(np.mean([x['recovery_ratio'] for x in panels])); disp=displacement(lam,scale)
            selection_key=[wins,min_macro,min_rec,mean_macro,mean_rec,-disp,-lam,-scale]
            rows.append({'tag':cfg,'lambda':lam,'scale':scale,'panel_wins':wins,'all_panel_win':wins==4,'min_macro_f1_ratio':min_macro,'min_recovery_ratio':min_rec,'mean_macro_f1_ratio':mean_macro,'mean_recovery_ratio':mean_rec,'distance_from_v17':disp,'selection_key':selection_key,'panels':panels})

    require(len(rows)==15,'grid result count changed')
    winner=max(rows,key=lambda r:tuple(r['selection_key']))
    result={
        'scientific_stage':'V18_EXPOSED_SONOTACO_DIVERSITY_GRID_DEVELOPMENT',
        'selection_rule':'lexicographic: panel_wins, min_macro_ratio, min_recovery_ratio, mean_macro_ratio, mean_recovery_ratio, nearest_v17, smaller_lambda, smaller_scale',
        'v17_reproduction_pass':True,
        'grid_size':15,'all_results':rows,'winner':winner,
        'verdict':'PASS_V18_EXPOSED_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if winner['all_panel_win'] else 'FAIL_V18_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT',
        'sonotaco_role':'EXPOSED_DEVELOPMENT_ONLY','post_result_second_search':False,
        'maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False,
    }
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'verdict':result['verdict'],'winner':winner,'v17_reproduction_pass':True},indent=2,sort_keys=True,allow_nan=False))
    return 0

if __name__=='__main__': raise SystemExit(main())
