#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pickle
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

REPO='brandonlign/runner'
SCIENCE_HEAD='7e7cd5b26addb2bea8daef50ce6d86388521ea46'
DEV_NAME='orbittrace-p15-support-safe-halo-development-v2'
PRETRUTH_NAME='orbittrace-p15-matched-pretruth-checkpoints'
DEV_SOURCE='22d34131e873825ca60aefbba0b92088f19f57f589fe629bfbd3b7041d160b4b'
P15_SOURCE='23d309f6702ed0aa6769381963ea64701ae59c97376a0bae536b527fbc978fe6'
P15_VALIDATOR_BLOB='d8653b898ca8c106d79df01c855783797294c30c'
P15_FINALIZER_BLOB='17e446565aa324e3de374246abc5a0693fc8467b'
P14_PREP_BLOB='ee932b83ad63d10fb81c5b8c85bb151c4467f8f7'
P14_TRANSPORT_FINALIZER_BLOB='1e9160c7beb5bc7651dc2b9f03db6211bc639ac6'
P13_FINALIZER_BLOB='a5d812b9956742b51e7e3995a71eb308afa7d095'
P14_FINALIZER_BLOB='d1ce98f443b2039d70421e76dadb6ada77d1b0d5'


def require(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)


def run(*args:str,env:dict[str,str]|None=None)->None:
    subprocess.run(args,check=True,env=env)


def git_blob(path:str)->str:
    return subprocess.check_output(['git','hash-object',path],text=True).strip()


def get_json(url:str,token:str)->dict:
    req=urllib.request.Request(url,headers={'Authorization':f'Bearer {token}','Accept':'application/vnd.github+json'})
    with urllib.request.urlopen(req) as r: return json.load(r)


def download(url:str,path:Path,token:str|None=None)->None:
    headers={'Authorization':f'Bearer {token}','Accept':'application/vnd.github+json'} if token else {}
    req=urllib.request.Request(url,headers=headers)
    with urllib.request.urlopen(req) as r, path.open('wb') as w: shutil.copyfileobj(r,w)


def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1<<20),b''): h.update(block)
    return h.hexdigest()


def exact_artifact(aid:int,run_id:int,digest:str,name:str,tag:str,token:str)->Path:
    meta=get_json(f'https://api.github.com/repos/{REPO}/actions/artifacts/{aid}',token)
    require(meta['id']==aid and meta['workflow_run']['id']==run_id and meta['name']==name,f'{tag} artifact metadata mismatch')
    require(meta['digest']==digest and not meta['expired'],f'{tag} artifact digest/expiry mismatch')
    z=Path(f'/tmp/{tag}.zip'); download(f'https://api.github.com/repos/{REPO}/actions/artifacts/{aid}/zip',z,token)
    require('sha256:'+sha256(z)==digest,f'{tag} downloaded ZIP digest mismatch')
    d=Path(f'/tmp/{tag}'); shutil.rmtree(d,ignore_errors=True); d.mkdir()
    with zipfile.ZipFile(z) as zf: zf.extractall(d)
    return d


def copy_checkpoint(root:Path,panel:str,dest:Path)->None:
    hits=list(root.rglob(f'checkpoints/{panel}.pkl'))
    require(len(hits)==1,f'{panel} checkpoint count={len(hits)}')
    side=Path(str(hits[0])+'.sha256')
    require(side.exists(),f'{panel} checkpoint sidecar missing')
    dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(hits[0],dest); shutil.copy2(side,Path(str(dest)+'.sha256'))


def fetch_assignment(aid:int,zip_sha:str,member:str,member_sha:str,out:Path,tag:str,token:str)->None:
    z=Path(f'/tmp/{tag}.zip'); download(f'https://api.github.com/repos/{REPO}/actions/artifacts/{aid}/zip',z,token)
    require(sha256(z)==zip_sha,f'{tag} assignment ZIP changed')
    d=Path(f'/tmp/{tag}'); shutil.rmtree(d,ignore_errors=True); d.mkdir()
    with zipfile.ZipFile(z) as zf: zf.extractall(d)
    hits=list(d.rglob(member)); require(len(hits)==1,f'{tag} member count={len(hits)}')
    out.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(hits[0],out)
    require(sha256(out)==member_sha,f'{tag} member SHA changed')


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--marker',required=True,type=Path)
    a=p.parse_args()
    token=os.environ['GH_TOKEN']
    base=os.environ['BASE_SHA']; head=os.environ['HEAD_SHA']

    # The PR child must change only the activation marker.
    run('git','fetch','--no-tags','origin',base,head)
    changed=subprocess.check_output(['git','diff','--name-only',base,head],text=True).splitlines()
    require(changed==['orbittrace_support_safe_halo_p15/P15_MATCHED_EVALUATOR_RUN.md'],f'activation diff changed: {changed}')
    marker=subprocess.check_output(['git','show',f'{head}:orbittrace_support_safe_halo_p15/P15_MATCHED_EVALUATOR_RUN.md'],text=True).splitlines()
    require(len(marker)==8 and marker[0]=='EXECUTE_P15_MATCHED_EVALUATOR_AFTER_BOTH_PRETRUTH_CHECKPOINTS','wrong activation marker')
    dev_run,dev_art,dev_digest= int(marker[1]),int(marker[2]),marker[3]
    pre_run,pre_art,pre_digest= int(marker[4]),int(marker[5]),marker[6]
    require(marker[7]==SCIENCE_HEAD,'P15 scientific source head changed')
    for d in (dev_digest,pre_digest): require(d.startswith('sha256:') and len(d)==71,'malformed artifact digest')

    # Exact source lineage, frozen before truth.
    require(git_blob('orbittrace_support_safe_halo_p15/validate_p15_pretruth_checkpoints.py')==P15_VALIDATOR_BLOB,'P15 validator changed')
    require(git_blob('orbittrace_support_safe_halo_p15/finalize_p15_matched_result.py')==P15_FINALIZER_BLOB,'P15 finalizer changed')
    require(git_blob('orbittrace_support_safe_rank_p14/prepare_transport_compatible_p13_finalizer.py')==P14_PREP_BLOB,'P14 transport prep changed')
    require(git_blob('orbittrace_support_safe_rank_p14/finalize_p14_matched_result_transport_v3.py')==P14_TRANSPORT_FINALIZER_BLOB,'P14 transport finalizer changed')
    require(git_blob('orbittrace_core_halo_p13_literature/finalize_p3_evaluator_result.py')==P13_FINALIZER_BLOB,'P13 finalizer changed')
    require(git_blob('orbittrace_core_halo_p13_literature/finalize_p14_matched_result.py')==P14_FINALIZER_BLOB,'P14 finalizer changed')

    dev=exact_artifact(dev_art,dev_run,dev_digest,DEV_NAME,'p15-dev',token)
    summaries=list(dev.rglob('support_safe_secondary_halo_p15_development.json')); require(len(summaries)==1,'P15 dev summary missing/duplicate')
    dr=json.loads(summaries[0].read_text())
    require(dr['verdict']=='PASS_SUPPORT_SAFE_SECONDARY_HALO_P15_DEVELOPMENT','P15 development not exact PASS')
    require(dr['p15_source_sha256']==DEV_SOURCE and dr['p15_parent_p12_exact_json_identity'] is True,'P15 development identity changed')
    require(dr['p15_fallback_vacuous_on_development'] is True and dr['directions']==452 and dr['unavailable_directions']==0 and dr['minimum_negative_count']>=128,'P15 development fallback not vacuous')
    require(dr['matched_truth_access'] is False and dr['external_data_access'] is False and dr['target_information_access'] is False,'P15 development firewall changed')

    pre=exact_artifact(pre_art,pre_run,pre_digest,PRETRUTH_NAME,'p15-pretruth',token)
    copy_checkpoint(pre,'hdbscan',Path('pretruth/checkpoints/hdbscan.pkl'))
    copy_checkpoint(pre,'sugar',Path('pretruth/checkpoints/sugar.pkl'))
    run(sys.executable,'orbittrace_support_safe_halo_p15/validate_p15_pretruth_checkpoints.py','--hdbscan','pretruth/checkpoints/hdbscan.pkl','--sugar','pretruth/checkpoints/sugar.pkl')
    print('PASS_P15_MATCHED_EVALUATOR_PREREQUISITES_FROZEN_BEFORE_TRUTH',flush=True)

    # Exact postfreeze source staging. No truth/cluster value is indexed until the one evaluator call below.
    Path('input/v3').mkdir(parents=True,exist_ok=True); Path('input/evaluator').mkdir(parents=True,exist_ok=True); Path('input/archives').mkdir(parents=True,exist_ok=True); Path('output').mkdir(exist_ok=True)
    run(sys.executable,'orbittrace_wavelet_catalogue_v3/audit_development_source.py')
    require(sha256(Path('/tmp/run_wavelet_catalogue_v3_development.py'))=='ef3e69317af59fdac7a030edc77f742fc4772473d7f16b719b5d804cd4117f51','base runner SHA changed')
    run('git','fetch','--no-tags','--depth=1','origin','d8258581af143308495bd97bedcc142abbbd951a')
    with Path('input/v3/multi_anchor_energy_v3.py').open('wb') as w:
        subprocess.run(['git','show','FETCH_HEAD:orbittrace_multi_anchor_energy_v3/multi_anchor_energy_v3.py'],check=True,stdout=w)
    require(git_blob('input/v3/multi_anchor_energy_v3.py')=='2ba4835db23f8f623cdd28d0a4e6113b7954ecb2','multi-anchor blob changed')

    fetch_assignment(9012424187,'2a953a237d32abfed8cfef110689623ec47e9acc9ed15eddee23a39d358d1bd4','full_catalogue_assignments.jsonl.gz','35f629b1dff4d04cdc13aa8224171ec1ab8e06b52836900d66ff978b5c235761',Path('input/hdbscan_2023.jsonl.gz'),'hdbscan2023',token)
    fetch_assignment(8955917326,'82e95052eb75349031341ea600aebf8f74d6842f03c0e47edf7cdea6de471a89','full_catalogue_assignments.jsonl.gz','8e7580c52e41e6994d6e46f289a7b916565a4efc512c5549ee83f249d0e81ee3',Path('input/hdbscan_2025.jsonl.gz'),'hdbscan2025',token)
    fetch_assignment(8957940764,'ea77c5111a7be51ff2bb45b16df934f7c808c695d08ac12003025de971df4fdf','sugar_uncertainty_assignments.json.gz','2b9e86572f10af447071cb10c56f643c1ad8babfe0d9aa667994ba3639834389',Path('input/sugar_2023.json.gz'),'sugar2023',token)
    fetch_assignment(8957263372,'9df4a48f4808180d534086e560e68ae56486f60171510207acd7bd6fedeebbc9','sugar_uncertainty_assignments.json.gz','77844d700bb14bb9952307fad13eb66cbc62e6a1555e5edd9c8aa0d26968b06e',Path('input/sugar_2025.json.gz'),'sugar2025',token)
    download('https://www.astro.sk/iaumdcDB/public/data/SNMv3/023a.zip',Path('input/archives/023a.zip')); require(sha256(Path('input/archives/023a.zip'))=='9f44696f99164801ff405dab90f68df3666b0d6734fed464a95e7ed0d6f5f430','2023 archive changed')
    download('https://www.astro.sk/iaumdcDB/public/data/SNMv3/025a.zip',Path('input/archives/025a.zip')); require(sha256(Path('input/archives/025a.zip'))=='f4eb716a4b900658fcc658a633d918eca28946f59da75935f1fd5f6bc539bf52','2025 archive changed')

    # These two frozen artifacts/source blobs are the same ones preregistered by the P13/P14 evaluator.
    run('gh','run','download','30920687116','--repo',REPO,'--name','sonotaco-2023-confirmation-source-repair-v2','--dir','/tmp/parser')
    ph=list(Path('/tmp/parser').rglob('run_sonotaco_2023_fixed4_confirmation.py')); require(len(ph)==1,'2023 parser artifact changed'); shutil.copy2(ph[0],'input/parser_2023.py'); require(sha256(Path('input/parser_2023.py'))=='bc2636005cc25da33e8accb6bdb70beea6ab900862cd1e6342a481395ac8f3e6','2023 parser SHA changed')
    run('gh','run','download','30855193522','--repo',REPO,'--name','real-shower-meta-data-audit','--dir','/tmp/mapping')
    mh=list(Path('/tmp/mapping').rglob('audit.json')); require(len(mh)==1,'mapping artifact changed'); shutil.copy2(mh[0],'input/mapping_audit.json'); require(sha256(Path('input/mapping_audit.json'))=='f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778','mapping audit SHA changed')
    run('git','fetch','--no-tags','--depth=1','origin','b1fa693471be78d1634632de942b6f95222c8a92')
    for name in ('evaluate_frozen.py','evaluate_frozen_blindsafe.py'):
        with Path('input/evaluator',name).open('wb') as w: subprocess.run(['git','show',f'FETCH_HEAD:orbittrace_crossfit_seed_floor_membership_p3_literature/{name}'],check=True,stdout=w)
    run(sys.executable,'-m','py_compile','input/parser_2023.py','input/evaluator/evaluate_frozen.py','input/evaluator/evaluate_frozen_blindsafe.py','exact-lit/orbittrace_literature_matched_v8/sonotaco_2025_native_adapter_wrapper.py')
    run(sys.executable,'orbittrace_support_safe_rank_p14/prepare_transport_compatible_p13_finalizer.py','orbittrace_core_halo_p13_literature/finalize_p3_evaluator_result.py','/tmp/finalize_p13_transport.py')

    print('OPEN_MATCHED_TRUTH_AND_COMPETITOR_CLUSTER_VALUES_EXACTLY_ONCE',flush=True)
    env=os.environ.copy(); env['PYTHONPATH']='exact-lit:input/v3:exact-lit/orbittrace_wavelet_catalogue_v3:.'
    run(sys.executable,'-u','input/evaluator/evaluate_frozen_blindsafe.py',
        '--hdbscan-pretruth','pretruth/checkpoints/hdbscan.pkl','--sugar-pretruth','pretruth/checkpoints/sugar.pkl',
        '--exact-row-runner','exact-lit/orbittrace_literature_matched_v8/run_exact_row_benchmark.py','--base-runner','/tmp/run_wavelet_catalogue_v3_development.py',
        '--support-source-parts','exact-lit/orbittrace_fixed4_support_wrapper_development/source_parts','--candidate-payload','exact-lit/sonotaco_fixed4_final_development/candidate.py.gz.b64','--baseline-payload','exact-lit/real_shower_meta_stage0/run_baseline_ceiling.py.gz.b64','--scorer-parts','exact-lit/mondrian_clique_development/source_parts_v2',
        '--parser-2023','input/parser_2023.py','--parser-2025','exact-lit/orbittrace_literature_matched_v8/sonotaco_2025_native_adapter_wrapper.py','--mapping-audit','input/mapping_audit.json',
        '--archive-2023','input/archives/023a.zip','--archive-2025','input/archives/025a.zip','--hdbscan-2023','input/hdbscan_2023.jsonl.gz','--hdbscan-2025','input/hdbscan_2025.jsonl.gz','--sugar-2023','input/sugar_2023.json.gz','--sugar-2025','input/sugar_2025.json.gz','--output','output/p3_evaluator_result.json',env=env)
    run(sys.executable,'/tmp/finalize_p13_transport.py','--p3-result','output/p3_evaluator_result.json','--hdbscan-checkpoint','pretruth/checkpoints/hdbscan.pkl','--sugar-checkpoint','pretruth/checkpoints/sugar.pkl','--output','output/p13_matched_literature_result.json')
    run(sys.executable,'orbittrace_support_safe_halo_p15/finalize_p15_matched_result.py',
        '--base-p14-transport-finalizer','orbittrace_support_safe_rank_p14/finalize_p14_matched_result_transport_v3.py','--base-p14-finalizer','orbittrace_core_halo_p13_literature/finalize_p14_matched_result.py',
        '--p13-result','output/p13_matched_literature_result.json','--hdbscan-checkpoint','pretruth/checkpoints/hdbscan.pkl','--sugar-checkpoint','pretruth/checkpoints/sugar.pkl','--output','output/p15_matched_literature_result.json')
    result=json.loads(Path('output/p15_matched_literature_result.json').read_text())
    require(result['verdict'] in {'PASS_P15_MATCHED_SPARSE_SUPERIORITY_BOTH_COMPARATORS_BOTH_YEARS','FAIL_P15_MATCHED_SPARSE_SUPERIORITY_NO_GO'},'unexpected P15 matched verdict')
    require(result['sparse_superiority_required_against_both_comparators_in_both_years'] is True and result['pairwise_only_no_cross_denominator_comparison'] is True and result['broad_only_does_not_authorize_external'] is True,'matched gates changed')
    require(result['target_access_authorized'] is False,'matched stage authorized target')
    passed=result['verdict'].startswith('PASS_'); require(bool(result['external_validation_authorized'])==passed,'external authorization mismatch')
    provenance={'classification':'P15 matched execution provenance','science_head':SCIENCE_HEAD,'development_run':dev_run,'development_artifact_id':dev_art,'development_artifact_digest':dev_digest,'pretruth_run':pre_run,'pretruth_artifact_id':pre_art,'pretruth_artifact_digest':pre_digest,'p15_source_sha256':P15_SOURCE,'result_sha256':hashlib.sha256(Path('output/p15_matched_literature_result.json').read_bytes()).hexdigest(),'target_access_authorized':False}
    Path('output/p15_matched_execution_provenance.json').write_text(json.dumps(provenance,indent=2,sort_keys=True)+'\n')
    print('P15_MATCHED_FINAL',json.dumps(result,sort_keys=True),flush=True)
    return 0


if __name__=='__main__': raise SystemExit(main())
