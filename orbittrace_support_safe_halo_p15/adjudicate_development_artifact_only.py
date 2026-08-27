#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

P15_DEV_SOURCE_SHA='22d34131e873825ca60aefbba0b92088f19f57f589fe629bfbd3b7041d160b4b'
P12_RESULT_SHA256='96698c1a7ba700716a79e7bc8b7bc9acb2f9aec653095a5d7e33b14000b87a38'
P13_RESULT_SHA256='d298cebec624c991c4abda9dc809d92d8eea101baaf2b6edbb1862b7acc49739'
P12_MEMBERSHIP_SHA='f158ebfa3a9a3c8006a7c81cbf0b47f7307aa7f2537e8046621b08037230cca3'
P13_CORE_SHA='12e6635085c77c8c705fe225e67811c659e98bf7cd1047649ec2b8d593261b3c'
P15_ARCH='P15_SUPPORT_SAFE_SECONDARY_HALO_AVAILABILITY'


def require(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)


def csha(value)->str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def file_sha(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--canonical-p12',required=True,type=Path)
    p.add_argument('--canonical-p13',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()
    require(file_sha(a.canonical_p12)==P12_RESULT_SHA256,'canonical P12 result bytes changed')
    require(file_sha(a.canonical_p13)==P13_RESULT_SHA256,'canonical P13 result bytes changed')
    p12=json.loads(a.canonical_p12.read_text())
    p13=json.loads(a.canonical_p13.read_text())

    require(p12['configuration']['years']==[2022,2023],'canonical P12 years changed')
    require(p12['configuration']['blind_exclusion']==[20.0,55.0],'canonical P12 blind interval changed')
    require(p12['configuration']['family_count']==226,'canonical P12 family count changed')
    require(p12['configuration']['negative_minimum_per_direction']==128,'canonical P12 negative requirement changed')
    require(p12['configuration']['parameter_search'] is False and p12['configuration']['p12_parameter_search'] is False,'canonical P12 parameter search changed')
    require(p12['claim_boundary'].startswith('Target-excluded development only.'),'canonical P12 target-excluded claim changed')
    dirs=p12['direction_audits']
    require(len(dirs)==452,'canonical P12 direction count changed')
    required=128
    unavailable=[]
    for row in dirs:
        n=int(row['negative_count'])
        if n<required:
            unavailable.append({
                'family_id':str(row['family_id']),
                'source_year':int(row['source_year']),
                'target_year':int(row['target_year']),
                'observed_negative_count':n,
                'required_negative_count':required,
                'status':'CHARACTERIZATION_UNAVAILABLE_INSUFFICIENT_NEGATIVES',
            })
    minimum=min(int(row['negative_count']) for row in dirs)
    require(unavailable==[],'P15 support-safe halo fallback would be nonvacuous on canonical development')
    require(minimum>=required,'canonical P12 minimum negatives below fixed requirement')
    require(p12['membership_pretruth_sha256']==P12_MEMBERSHIP_SHA,'canonical P12 membership identity changed')

    require(p13['verdict']=='PASS_DUAL_OUTPUT_CORE_HALO_P13_DEVELOPMENT','canonical P13 is not promoted PASS')
    require(p13['configuration']['p13_primary_discovery_metrics_use_core_only'] is True,'canonical P13 primary core role changed')
    require(p13['configuration']['p13_membership_metrics_use_halo_only'] is True,'canonical P13 secondary halo role changed')
    require(p13['core_pretruth_sha256']==P13_CORE_SHA,'canonical P13 core identity changed')
    require(p13['halo_pretruth_sha256']==P12_MEMBERSHIP_SHA,'canonical P13 halo identity changed')
    require(p13['core_discovery']=={
        'qualified_matches':95,
        'recovered_at_100':58,
        'recovered_at_500':95,
        'mrr':0.045531138942766655,
        'top100_dominant_precision':0.6884631112636006,
    },'canonical P13 core endpoints changed')
    require(p13['halo_membership']['macro_f1']==0.37661279333940806,'canonical P13 halo macro F1 changed')
    require(p13['halo_membership']['large_shower']['mean_recall']==0.24179462579908398,'canonical P13 halo large recall changed')
    require(p13['halo_membership']['large_shower']['mean_precision']==0.8778478363509471,'canonical P13 halo large precision changed')
    require(p13['no_new_truth_query'] is True and p13['target_information_access'] is False,'canonical P13 firewall changed')

    result={
        'verdict':'PASS_SUPPORT_SAFE_SECONDARY_HALO_P15_DEVELOPMENT',
        'architecture':P15_ARCH,
        'adjudication_mode':'artifact_only_from_immutable_canonical_P12_P13',
        'p15_development_source_sha256':P15_DEV_SOURCE_SHA,
        'fixed_min_direction_negatives':required,
        'canonical_direction_count':len(dirs),
        'canonical_minimum_negative_count':minimum,
        'p15_unavailable_directions':unavailable,
        'p15_unavailable_direction_count':len(unavailable),
        'p15_availability_sha256':csha(unavailable),
        'p15_fallback_vacuous_on_development':True,
        'p15_no_padding_resampling_or_relaxation':True,
        'p15_secondary_characterization_only':True,
        'canonical_p12_result_sha256':P12_RESULT_SHA256,
        'canonical_p12_membership_pretruth_sha256':P12_MEMBERSHIP_SHA,
        'canonical_p13_result_sha256':P13_RESULT_SHA256,
        'canonical_p13_core_pretruth_sha256':P13_CORE_SHA,
        'canonical_p13_halo_pretruth_sha256':P12_MEMBERSHIP_SHA,
        'canonical_core_discovery':p13['core_discovery'],
        'canonical_halo_membership':p13['halo_membership'],
        'new_truth_query':False,
        'matched_truth_access':False,
        'external_data_access':False,
        'target_information_access':False,
        'scientific_interpretation':'P15 changes only exact-P12 secondary-characterization behavior when a direction has <128 target-window negatives. On immutable canonical target-excluded development every one of 452 directions is eligible, so the P15 fallback is mathematically vacuous and canonical P12/P13 outputs remain the promoted development outputs without rerunning floating linear algebra.',
    }
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    a.output.with_suffix(a.output.suffix+'.sha256').write_text(csha(result)+'\n')
    print('P15_ARTIFACT_ONLY_DEVELOPMENT_ADJUDICATION_BEGIN')
    print(json.dumps(result,indent=2,sort_keys=True))
    print('P15_ARTIFACT_ONLY_DEVELOPMENT_ADJUDICATION_END')
    return 0


if __name__=='__main__': raise SystemExit(main())
