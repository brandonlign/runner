#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pickle
from pathlib import Path
from typing import Any

REQUIRED_PANELS=('hdbscan','sugar')
PASS_CLASSES={'BROAD_CATALOGUE_SUPERIORITY','SPARSE_STREAM_SUPERIORITY'}
EXPECTED_ASSIGNMENT_SHA={
    'hdbscan':{2023:'35f629b1dff4d04cdc13aa8224171ec1ab8e06b52836900d66ff978b5c235761',2025:'8e7580c52e41e6996d6e46f289a7b916565a4efc512c5549ee83f249d0e81ee3'},
    'sugar':{2023:'2b9e86572f10af447071cb10c56f643c1ad8babfe0d9aa667994ba3639834389',2025:'77844d700bb14bb9952307fad13eb66cbc62e6a1555e5edd9c8aa0d26968b06e'},
}
EXPECTED_ASSIGNMENT_COUNT={'hdbscan':{2023:26460,2025:19658},'sugar':{2023:30414,2025:23200}}


def require(ok:bool,message:str)->None:
    if not ok: raise RuntimeError(message)


def load_json(path:Path)->dict[str,Any]: return json.loads(path.read_text())

def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''): h.update(chunk)
    return h.hexdigest()


def parse_args()->argparse.Namespace:
    p=argparse.ArgumentParser()
    for panel in REQUIRED_PANELS:
        p.add_argument(f'--{panel}-result',required=True,type=Path)
        p.add_argument(f'--{panel}-checkpoint',required=True,type=Path)
    p.add_argument('--p13-development-result',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    return p.parse_args()


def main()->int:
    a=parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    dev=load_json(a.p13_development_result)
    require(dev['verdict']=='PASS_DUAL_OUTPUT_CORE_HALO_P13_DEVELOPMENT','P13 development pass not authoritative')
    require(dev['configuration']['p13_primary_discovery_metrics_use_core_only'] is True,'P13 primary core boundary changed')
    require(dev['configuration']['p13_membership_metrics_use_halo_only'] is True,'P13 halo boundary changed')
    require(dev['core_discovery']['qualified_matches']==95 and dev['core_discovery']['recovered_at_100']==58,'P13 development core baseline changed')
    require(dev['halo_membership']['macro_f1']>=0.2536657194465356,'P13 development halo F1 gate no longer passes')
    require(dev['halo_membership']['large_shower']['mean_recall']>=1.5*0.06738386922850433,'P13 development halo recall gate no longer passes')
    require(dev['halo_membership']['large_shower']['mean_precision']>=0.85,'P13 development halo precision gate no longer passes')

    panels={}
    all_pass=True
    for panel in REQUIRED_PANELS:
        result=load_json(getattr(a,f'{panel}_result'))
        cp=pickle.loads(getattr(a,f'{panel}_checkpoint').read_bytes())
        require(cp['panel']==panel and result['panel']==panel,'panel identity mismatch')
        require(cp['p13_primary_core_only'] is True and cp['p13_halo_secondary_only'] is True,'P13 layer boundary changed')
        require(cp['competitor_cluster_values_accessed'] is False and cp['known_shower_truth_accessed'] is False,'pretruth checkpoint crossed data boundary')
        require(result['classification'] in {'BROAD_CATALOGUE_SUPERIORITY','SPARSE_STREAM_SUPERIORITY','NO_P3_CATALOGUE_SUPERIORITY'},'unexpected generic evaluator classification')
        require(result['assignment_source_sha256']==EXPECTED_ASSIGNMENT_SHA[panel],'assignment provenance changed')
        require(result['assignment_counts']==EXPECTED_ASSIGNMENT_COUNT[panel],'assignment counts changed')
        # Generic evaluator's P3 slot is deliberately the exact P13 core. It must equal its own internal-v8 reconstruction exactly.
        require(result['p3']==result['internal_v8'],'primary candidate differs from exact immutable core reconstruction')
        require(all(abs(float(v))<=1e-15 for v in result['delta']['p3_minus_internal_v8'].values()),'P13 core/internal-v8 delta is nonzero')
        require(result['gates']['strict_row_universe_exact'] is True,'strict exact-row universe failed')
        require(result['gates']['truth_ids_match_assignments'] is True,'truth/assignment universe mismatch')
        require(result['gates']['internal_v8_frozen_before_truth'] is True,'core was not frozen before truth')
        require(result['gates']['competitor_values_unread_until_freeze'] is True,'comparator values entered before freeze')
        require(result['gates']['truth_values_unread_until_freeze'] is True,'truth entered before freeze')
        panel_pass=result['classification'] in PASS_CLASSES
        all_pass &= panel_pass
        panels[panel]={
            'classification':result['classification'],
            'pass_required_sparse_or_broad_bar':panel_pass,
            'core':result['p3'],
            'competitor':result['competitor'],
            'delta_core_minus_competitor':result['delta']['p3_minus_competitor'],
            'size_delta_core_minus_competitor':result['size_delta']['p3_minus_competitor'],
            'gates':result['gates'],
            'core_pretruth_sha256':cp['p13_core_pretruth_sha256'],
            'halo_membership_pretruth_sha256':cp['p13_halo_membership_pretruth_sha256'],
            'halo_secondary':cp['p3_diagnostics'],
            'checkpoint_sha256':sha256_file(getattr(a,f'{panel}_checkpoint')),
            'result_sha256':sha256_file(getattr(a,f'{panel}_result')),
        }

    verdict='PASS_P13_MATCHED_SPARSE_SUPERIORITY_BOTH_COMPARATORS_BOTH_YEARS' if all_pass else 'FAIL_P13_MATCHED_SPARSE_SUPERIORITY_NO_GO'
    out={
        'verdict':verdict,
        'classification':'P13 primary immutable-core matched catalogue comparison; exact P12 halo frozen/reported separately',
        'years':[2023,2025],
        'blind_exclusion':[20.0,55.0],
        'pairwise_no_denominator_mixing':True,
        'primary_discovery_uses_core_only':True,
        'halo_secondary_only':True,
        'mandatory_sparse_or_broad_superiority_separate_against_both_comparators':True,
        'panels':panels,
        'development_artifact_core_sha256':dev['core_pretruth_sha256'],
        'development_artifact_halo_sha256':dev['halo_pretruth_sha256'],
        'target_information_access':False,
    }
    (a.output/'p13_matched_literature_aggregate.json').write_text(json.dumps(out,indent=2)+'\n')
    (a.output/'P13_MATCHED_LITERATURE_AGGREGATE.md').write_text(
        '# OrbitTrace P13 matched literature aggregate\n\n'
        f'Verdict: **`{verdict}`**\n\n'
        + ''.join(f'- {p}: **{panels[p]["classification"]}**\n' for p in REQUIRED_PANELS)
        + '\nPrimary comparison uses immutable cores only; exact transported halos are secondary and cannot affect superiority.\n'
        + 'No OrbitTrace target information or 20°–55° event was used.\n'
    )
    print((a.output/'P13_MATCHED_LITERATURE_AGGREGATE.md').read_text(),flush=True)
    return 0


if __name__=='__main__': raise SystemExit(main())
