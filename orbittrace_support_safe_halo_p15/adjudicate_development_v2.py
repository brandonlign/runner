#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

P15_SOURCE_SHA='22d34131e873825ca60aefbba0b92088f19f57f589fe629bfbd3b7041d160b4b'
P12_MEMBERSHIP_SHA='f158ebfa3a9a3c8006a7c81cbf0b47f7307aa7f2537e8046621b08037230cca3'
P13_CORE_SHA='12e6635085c77c8c705fe225e67811c659e98bf7cd1047649ec2b8d593261b3c'


def require(ok:bool,msg:str)->None:
    if not ok:
        raise RuntimeError(msg)


def canonical_sha(value)->str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--p15-result',required=True,type=Path)
    p.add_argument('--canonical-p12',required=True,type=Path)
    p.add_argument('--canonical-p13',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()
    new=json.loads(a.p15_result.read_text())
    p12=json.loads(a.canonical_p12.read_text())
    p13=json.loads(a.canonical_p13.read_text())

    require(new['configuration']['years']==[2022,2023],'P15 development years changed')
    require(new['configuration']['blind_exclusion']==[20.0,55.0],'P15 development blind interval changed')
    require(new['configuration']['family_count']==226,'P15 development family count changed')
    require(new['p15_architecture']=='P15_SUPPORT_SAFE_SECONDARY_HALO_AVAILABILITY','P15 architecture changed')
    require(new['p15_parent_source_sha256']=='78e93b5af19a441bc58b00428d2b356218b33f7a4a891a640dd59cb5d4599c32','P15 parent source changed')
    require(new['p15_min_direction_negatives_unchanged']==128,'P15 negative requirement changed')
    require(new['p15_no_padding_resampling_or_relaxation'] is True,'P15 relaxation enabled')
    require(new['p15_secondary_characterization_only'] is True,'P15 became primary')
    require(new['p15_unavailable_direction_count']==0 and new['p15_unavailable_directions']==[],'P15 fallback nonvacuous on development')
    require(new['p15_availability_sha256']==canonical_sha([]),'P15 empty availability ledger hash changed')
    require(len(new['direction_audits'])==452,'P15 development direction count changed')
    require(min(int(x['negative_count']) for x in new['direction_audits'])>=128,'P15 development has support-ineligible direction')

    # Strongest compatibility test: after deleting only P15 metadata, the fresh
    # execution must be object-identical to the authoritative exact P12 JSON.
    inherited={k:v for k,v in new.items() if not k.startswith('p15_')}
    require(inherited==p12,'P15 execution differs from canonical P12 outside added p15_* metadata')
    require(new['membership_pretruth_sha256']==P12_MEMBERSHIP_SHA,'P15 halo membership hash changed')

    require(p13['verdict']=='PASS_DUAL_OUTPUT_CORE_HALO_P13_DEVELOPMENT','canonical P13 is not promoted PASS')
    require(p13['core_pretruth_sha256']==P13_CORE_SHA,'canonical P13 core hash changed')
    require(p13['halo_pretruth_sha256']==P12_MEMBERSHIP_SHA,'canonical P13 halo hash changed')
    require(p13['core_discovery']=={
        'qualified_matches':95,
        'recovered_at_100':58,
        'recovered_at_500':95,
        'mrr':0.045531138942766655,
        'top100_dominant_precision':0.6884631112636006,
    },'canonical P13 core endpoints changed')
    halo=p13['halo_membership']
    require(abs(halo['macro_f1']-new['p12']['macro_f1'])<1e-15,'P15/P13 halo macro F1 mismatch')
    require(halo['qualified_matches_secondary']==new['p12']['qualified_matches'],'P15/P13 halo qualified mismatch')
    require(halo['recovered_at_100_secondary']==new['p12']['recovered_at_100'],'P15/P13 halo recovery@100 mismatch')
    require(halo['recovered_at_500_secondary']==new['p12']['recovered_at_500'],'P15/P13 halo recovery@500 mismatch')
    require(abs(halo['top100_dominant_precision_secondary']-new['p12']['top100_dominant_precision'])<1e-15,'P15/P13 halo top100 precision mismatch')
    require(halo['large_shower']==new['p12_large_shower'],'P15/P13 large-shower halo metrics mismatch')
    require(p13['no_new_truth_query'] is True and p13['target_information_access'] is False,'canonical P13 firewall changed')

    summary={
        'verdict':'PASS_SUPPORT_SAFE_SECONDARY_HALO_P15_DEVELOPMENT',
        'p15_source_sha256':P15_SOURCE_SHA,
        'p15_parent_p12_exact_json_identity':True,
        'p15_fallback_vacuous_on_development':True,
        'directions':len(new['direction_audits']),
        'minimum_negative_count':min(int(x['negative_count']) for x in new['direction_audits']),
        'unavailable_directions':0,
        'p13_core_pretruth_sha256':P13_CORE_SHA,
        'halo_membership_pretruth_sha256':P12_MEMBERSHIP_SHA,
        'core_discovery':p13['core_discovery'],
        'halo_membership':halo,
        'matched_truth_access':False,
        'external_data_access':False,
        'target_information_access':False,
    }
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    a.output.with_suffix(a.output.suffix+'.sha256').write_text(canonical_sha(summary)+'\n')
    print('P15_DEVELOPMENT_ADJUDICATION_BEGIN')
    print(json.dumps(summary,indent=2,sort_keys=True))
    print('P15_DEVELOPMENT_ADJUDICATION_END')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
