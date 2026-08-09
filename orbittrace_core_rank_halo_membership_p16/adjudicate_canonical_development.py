#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

P13_CORE_SHA='12e6635085c77c8c705fe225e67811c659e98bf7cd1047649ec2b8d593261b3c'
P12_HALO_SHA='f158ebfa3a9a3c8006a7c81cbf0b47f7307aa7f2537e8046621b08037230cca3'


def require(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)


def canonical_sha(value:Any)->str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--p12-result',required=True,type=Path)
    p.add_argument('--p12-expanded',required=True,type=Path)
    p.add_argument('--p13-result',required=True,type=Path)
    p.add_argument('--p13-core',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()

    p12=json.loads(a.p12_result.read_text())
    halo=json.loads(gzip.decompress(a.p12_expanded.read_bytes()).decode())
    p13=json.loads(a.p13_result.read_text())
    core=json.loads(a.p13_core.read_text())

    require(p12['configuration']['years']==[2022,2023] and p12['configuration']['blind_exclusion']==[20.0,55.0],'P16 canonical P12 universe changed')
    require(p12['configuration']['family_count']==226 and len(halo)==226,'P16 canonical P12 family count changed')
    require(p12['membership_pretruth_sha256']==P12_HALO_SHA,'P16 canonical P12 halo hash changed')
    require(p13['verdict']=='PASS_DUAL_OUTPUT_CORE_HALO_P13_DEVELOPMENT','P16 canonical P13 not promoted PASS')
    require(p13['configuration']['p13_primary_discovery_metrics_use_core_only'] is True,'P16 canonical P13 core role changed')
    require(p13['configuration']['p13_membership_metrics_use_halo_only'] is True,'P16 canonical P13 halo role changed')
    require(p13['core_pretruth_sha256']==P13_CORE_SHA and p13['halo_pretruth_sha256']==P12_HALO_SHA,'P16 canonical P13 identities changed')
    require(len(core)==226,'P16 canonical P13 core family count changed')

    core_by={str(x['family_id']):x for x in core}; halo_by={str(x['family_id']):x for x in halo}
    require(len(core_by)==len(core) and len(halo_by)==len(halo),'P16 duplicate family IDs in development artifacts')
    require(set(core_by)==set(halo_by),'P16 canonical core/halo family IDs differ')
    correspondence=[]; total_core=0; total_halo=0; total_added=0
    for fid in sorted(core_by):
        cids=set(map(str,core_by[fid]['core_event_ids'])); h=halo_by[fid]; hids=set(map(str,h['event_ids']))
        require(cids and cids<=hids,f'P16 canonical core not subset of halo {fid}')
        added=hids-cids; stored=set(map(str,h.get('p2_added_event_ids',[])))
        require(stored==added,f'P16 canonical added-ID set differs from halo-core difference {fid}')
        require(int(h.get('p2_added_event_count',len(stored)))==len(stored),'P16 canonical added count changed')
        total_core+=len(cids); total_halo+=len(hids); total_added+=len(added)
        correspondence.append({
            'family_id':fid,'core_event_count':len(cids),'halo_event_count':len(hids),'added_event_count':len(added),
            'core_sha256':canonical_sha(sorted(cids)),'halo_sha256':canonical_sha(sorted(hids)),'added_sha256':canonical_sha(sorted(added)),
        })
    require(total_halo-total_core==total_added==17238,'P16 canonical halo addition total changed')

    core_metrics=p13['core_discovery']; halo_metrics=p13['halo_membership']
    require(core_metrics=={
        'qualified_matches':95,'recovered_at_100':58,'recovered_at_500':95,
        'mrr':0.045531138942766655,'top100_dominant_precision':0.6884631112636006,
    },'P16 canonical core discovery endpoints changed')
    require(abs(float(halo_metrics['macro_f1'])-0.37661279333940806)<1e-15,'P16 canonical halo macro F1 changed')
    require(abs(float(halo_metrics['top100_dominant_precision_secondary'])-0.6904890277588119)<1e-15,'P16 canonical halo top100 precision changed')
    require(halo_metrics['large_shower']==p12['p12_large_shower'],'P16 canonical large-shower halo metrics differ')
    require(p13['no_new_truth_query'] is True and p13['target_information_access'] is False,'P16 canonical P13 firewall changed')

    out={
        'verdict':'PASS_P16_CORE_RANK_HALO_MEMBERSHIP_CANONICAL_DEVELOPMENT_IDENTITY',
        'classification':'OUTPUT_ARCHITECTURE_DEVELOPMENT_IDENTITY',
        'years':[2022,2023],'blind_exclusion':[20.0,55.0],
        'family_count':226,
        'p13_core_pretruth_sha256':P13_CORE_SHA,
        'p12_halo_membership_pretruth_sha256':P12_HALO_SHA,
        'core_event_count':total_core,'reported_halo_event_count':total_halo,'already_frozen_halo_additions':total_added,
        'core_halo_correspondence_sha256':canonical_sha(correspondence),
        'core_discovery':core_metrics,
        'reported_membership':halo_metrics,
        'family_existence_and_rank_core_only':True,
        'reported_membership_exact_canonical_label_free_halo':True,
        'new_detector_score_threshold_or_member_proposal':False,
        'matched_comparator_access':False,'external_data_access':False,'target_information_access':False,
    }
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    a.output.with_suffix(a.output.suffix+'.sha256').write_text(canonical_sha(out)+'\n')
    print('P16_CANONICAL_DEVELOPMENT_BEGIN'); print(json.dumps(out,indent=2,sort_keys=True)); print('P16_CANONICAL_DEVELOPMENT_END')
    return 0


if __name__=='__main__': raise SystemExit(main())
