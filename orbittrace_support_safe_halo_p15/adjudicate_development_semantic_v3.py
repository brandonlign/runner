#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
from typing import Any

ABS_TOL=1e-12
SCALED_TOL=1e-12
P15_SOURCE='22d34131e873825ca60aefbba0b92088f19f57f589fe629bfbd3b7041d160b4b'
P12_HALO_SHA='f158ebfa3a9a3c8006a7c81cbf0b47f7307aa7f2537e8046621b08037230cca3'
P13_CORE_SHA='12e6635085c77c8c705fe225e67811c659e98bf7cd1047649ec2b8d593261b3c'


def require(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)


def canonical_sha(v:Any)->str:
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def discrete_projection(value:Any,key:str='')->Any:
    # SHA fields encode floating serialization in several inherited audit objects;
    # compare their underlying scientific structure/values separately instead.
    if isinstance(value,dict):
        return {k:discrete_projection(v,k) for k,v in value.items() if 'sha256' not in k.lower()}
    if isinstance(value,list):
        return [discrete_projection(v,key) for v in value]
    if isinstance(value,float):
        return '<FLOAT>'
    return value


def collect_float_diffs(a:Any,b:Any,path:str='',out:list|None=None)->list:
    if out is None: out=[]
    if isinstance(a,dict) and isinstance(b,dict):
        for k in sorted(set(a)&set(b)):
            if 'sha256' in k.lower():
                continue
            collect_float_diffs(a[k],b[k],f'{path}.{k}' if path else k,out)
    elif isinstance(a,list) and isinstance(b,list):
        require(len(a)==len(b),f'continuous comparison list length changed at {path}')
        for i,(x,y) in enumerate(zip(a,b)):
            collect_float_diffs(x,y,f'{path}[{i}]',out)
    elif isinstance(a,float) and isinstance(b,(int,float)) and not isinstance(b,bool):
        av=float(a); bv=float(b)
        require(math.isfinite(av) and math.isfinite(bv),f'nonfinite continuous value at {path}')
        diff=abs(av-bv); scaled=diff/max(1.0,abs(av),abs(bv))
        out.append((diff,scaled,path,av,bv))
    elif isinstance(b,float) and isinstance(a,(int,float)) and not isinstance(a,bool):
        av=float(a); bv=float(b)
        require(math.isfinite(av) and math.isfinite(bv),f'nonfinite continuous value at {path}')
        diff=abs(av-bv); scaled=diff/max(1.0,abs(av),abs(bv))
        out.append((diff,scaled,path,av,bv))
    return out


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--fresh-result',required=True,type=Path)
    p.add_argument('--fresh-expanded',required=True,type=Path)
    p.add_argument('--canonical-p12-result',required=True,type=Path)
    p.add_argument('--canonical-p12-expanded',required=True,type=Path)
    p.add_argument('--canonical-p13-result',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()

    fresh=json.loads(a.fresh_result.read_text())
    fresh_exp=json.loads(gzip.decompress(a.fresh_expanded.read_bytes()).decode())
    p12=json.loads(a.canonical_p12_result.read_text())
    canon_exp=json.loads(gzip.decompress(a.canonical_p12_expanded.read_bytes()).decode())
    p13=json.loads(a.canonical_p13_result.read_text())

    require(fresh['p15_parent_source_sha256']=='78e93b5af19a441bc58b00428d2b356218b33f7a4a891a640dd59cb5d4599c32','P15 parent source changed')
    require(fresh['p15_min_direction_negatives_unchanged']==128,'P15 negative minimum changed')
    require(fresh['p15_no_padding_resampling_or_relaxation'] is True,'P15 support relaxation enabled')
    require(fresh['p15_secondary_characterization_only'] is True,'P15 scientific role changed')
    require(fresh['p15_unavailable_direction_count']==0 and fresh['p15_unavailable_directions']==[],'P15 fallback was not vacuous')
    require(len(fresh['direction_audits'])==452,'P15 direction universe changed')
    require(min(int(x['negative_count']) for x in fresh['direction_audits'])>=128,'P15 development contains support-poor direction')

    inherited={k:v for k,v in fresh.items() if not k.startswith('p15_')}
    require(set(inherited)==set(p12),'P15 inherited top-level schema changed')
    require(discrete_projection(inherited)==discrete_projection(p12),'P15 inherited non-floating scientific structure/values changed')

    # Headline scientific endpoints and discrete burden counts must remain exact,
    # not merely numerically close.
    for key in ('baseline_v8','p12','p12_large_shower'):
        require(fresh[key]==p12[key],f'P15 inherited exact metric dictionary changed: {key}')
    for key in ('assigned_nonseed_events','proposal_events','conflicted_proposal_events','families_gaining_members'):
        require(fresh['diagnostics'][key]==p12['diagnostics'][key],f'P15 inherited discrete diagnostic changed: {key}')

    support_fields=('family_id','source_year','target_year','source_seed_count','positive_count','negative_count')
    for i,(x,y) in enumerate(zip(fresh['direction_audits'],p12['direction_audits'])):
        require(all(x.get(k)==y.get(k) for k in support_fields),f'P15 direction identity/support count changed at index {i}')

    require(len(fresh_exp)==len(canon_exp)==226,'P15 canonical family count changed')
    require([str(x['family_id']) for x in fresh_exp]==[str(x['family_id']) for x in canon_exp],'P15 family order changed')
    for i,(x,y) in enumerate(zip(fresh_exp,canon_exp)):
        require(str(x['family_id'])==str(y['family_id']),f'P15 family ID changed at {i}')
        require(list(map(str,x['event_ids']))==list(map(str,y['event_ids'])),f'P15 exact member IDs changed for {x["family_id"]}')
        require(list(map(str,x.get('p2_added_event_ids',[])))==list(map(str,y.get('p2_added_event_ids',[]))),f'P15 exact added IDs changed for {x["family_id"]}')
        require(int(x.get('p2_added_event_count',0))==int(y.get('p2_added_event_count',0)),f'P15 exact added count changed for {x["family_id"]}')

    floats=collect_float_diffs(inherited,p12)
    max_abs=max((x[0] for x in floats),default=0.0)
    max_scaled=max((x[1] for x in floats),default=0.0)
    worst_abs=max(floats,default=(0.0,0.0,'',0.0,0.0),key=lambda x:x[0])
    worst_scaled=max(floats,default=(0.0,0.0,'',0.0,0.0),key=lambda x:x[1])
    require(max_abs<=ABS_TOL and max_scaled<=SCALED_TOL,f'P15 inherited continuous drift exceeds fixed machine-level tolerance: abs={max_abs} scaled={max_scaled}')

    require(p13['verdict']=='PASS_DUAL_OUTPUT_CORE_HALO_P13_DEVELOPMENT','canonical P13 promotion changed')
    require(p13['core_pretruth_sha256']==P13_CORE_SHA and p13['halo_pretruth_sha256']==P12_HALO_SHA,'canonical P13 core/halo identities changed')
    require(p13['core_discovery']=={'qualified_matches':95,'recovered_at_100':58,'recovered_at_500':95,'mrr':0.045531138942766655,'top100_dominant_precision':0.6884631112636006},'canonical P13 core endpoints changed')
    require(p13['no_new_truth_query'] is True and p13['target_information_access'] is False,'canonical P13 firewall changed')

    # Bitwise identity is intentionally recorded as false: the prior adjudicator
    # failed on platform-level floating serialization despite exact decisions.
    require(inherited!=p12,'P15 semantic adjudicator unexpectedly received bitwise-identical inherited JSON')
    out={
        'verdict':'PASS_P15_SUPPORT_SAFE_HALO_SEMANTIC_DEVELOPMENT_COMPATIBILITY',
        'classification':'NUMERICALLY_STABLE_EXACT_DECISION_COMPATIBILITY',
        'p15_source_sha256':P15_SOURCE,
        'source_execution_run_id':31328065110,
        'source_execution_artifact_id':9042324169,
        'bitwise_json_identity':False,
        'bitwise_identity_failure_preserved':True,
        'fallback_vacuous_on_development':True,
        'directions':452,
        'unavailable_directions':0,
        'family_count':226,
        'exact_family_order':True,
        'exact_event_membership_ids':True,
        'exact_added_member_ids':True,
        'exact_headline_metrics':True,
        'exact_discrete_diagnostics':True,
        'continuous_abs_tolerance':ABS_TOL,
        'continuous_scaled_tolerance':SCALED_TOL,
        'max_continuous_abs_difference':max_abs,
        'max_continuous_scaled_difference':max_scaled,
        'worst_abs_path':worst_abs[2],
        'worst_scaled_path':worst_scaled[2],
        'canonical_p12_halo_pretruth_sha256':P12_HALO_SHA,
        'canonical_p13_core_pretruth_sha256':P13_CORE_SHA,
        'matched_comparator_access':False,
        'external_data_access':False,
        'target_information_access':False,
        'claim_boundary':'P15 development compatibility is semantic/exact-decision, not byte-level floating serialization identity. Any changed family/member decision, metric dictionary, discrete support count, fallback activation, or continuous drift above fixed 1e-12 absolute/scaled tolerance is fatal.',
    }
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    a.output.with_suffix(a.output.suffix+'.sha256').write_text(canonical_sha(out)+'\n')
    print('P15_SEMANTIC_DEVELOPMENT_BEGIN'); print(json.dumps(out,indent=2,sort_keys=True)); print('P15_SEMANTIC_DEVELOPMENT_END')
    return 0


if __name__=='__main__': raise SystemExit(main())
