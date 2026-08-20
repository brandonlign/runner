#!/usr/bin/env python3
from __future__ import annotations
import argparse, base64, gzip, hashlib, importlib.util, json, math, sys, types
from pathlib import Path
from typing import Any

YEARS=(2022,2023)
MONTH_KEYS=tuple(f'{y}-{m:02d}' for y in YEARS for m in range(1,13))
EXPECTED_BASELINE_GZIP_SHA256='6d72b0f9558b89228953dd73b3760c61df039b713f233473079ae4fac563a100'
EXPECTED_BASELINE_INNER_SHA256='7ff3b13bc45e19b4b886453b4d8cc3b4f18090bf8a2291e39850540fd69b5e53'
EXPECTED_BASELINE_CANDIDATES=8469
EXPECTED_EVENT_COUNT=549636
MAX_RANK=100
EXPECTED_SACV_SHA='cd5a7505c1d095e03de683f78dce8af5cb465ba32ca1dfa3e8b9eb3e78d0fd64'
EXPECTED_BLIND_PART_BLOBS={
 'part00.b64':'ed5c488fb4bf0ed5ae4b1c43f4cfb008501936e1',
 'part01.b64':'65b96befa5726581af74ad11d982fee18de0e4e7',
 'part02.b64':'04175711594c46d67cdb759cbee3a3e93819ce8d',
 'part03.b64':'2b890713e681f3b2372b29577cd66997dada8e07',
}
EXPECTED_BLIND_SOURCE_BYTES=24135

def req(x:bool,msg:str)->None:
    if not x: raise RuntimeError(msg)
def sha_bytes(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def sha(p:Path)->str:return sha_bytes(p.read_bytes())
def git_blob(p:Path)->str:
    b=p.read_bytes(); return hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()
def load_module(p:Path,name:str)->Any:
    s=importlib.util.spec_from_file_location(name,p); req(s is not None and s.loader is not None,f'cannot import {p}'); m=importlib.util.module_from_spec(s); sys.modules[name]=m; s.loader.exec_module(m); return m

def decode_loader(root:Path,out:Path)->Any:
    parts=sorted(root.glob('part*.b64')); req([p.name for p in parts]==list(EXPECTED_BLIND_PART_BLOBS),'blind source part set changed')
    for p in parts:req(git_blob(p)==EXPECTED_BLIND_PART_BLOBS[p.name],f'blind source blob changed {p.name}')
    enc=''.join(''.join(p.read_text().split()) for p in parts); raw=gzip.decompress(base64.b64decode(enc,validate=True)); req(len(raw)==EXPECTED_BLIND_SOURCE_BYTES,f'blind loader bytes {len(raw)}'); out.write_bytes(raw); return load_module(out,'sacv_target_blind_loader')

def load_baseline(p:Path)->tuple[dict[str,Any],str,str]:
    gz=p.read_bytes(); g=sha_bytes(gz); req(g==EXPECTED_BASELINE_GZIP_SHA256,f'baseline gzip changed {g}'); raw=gzip.decompress(gz); h=sha_bytes(raw); req(h==EXPECTED_BASELINE_INNER_SHA256,f'baseline inner changed {h}'); r=json.loads(raw)
    req(r['schema']=='ORBITTRACE_M2D_BLIND_REDISCOVERY_V1_PRETRUTH','baseline schema'); req(r['scientific_role']=='TARGET_FREE_COMPLETE_M2D_RANKING_BEFORE_ORBITTRACE_REVEAL','baseline role'); req(r['candidate_count']==len(r['candidates'])==EXPECTED_BASELINE_CANDIDATES,'baseline candidates'); req(r['event_count']==EXPECTED_EVENT_COUNT,'baseline event count'); req(r['configuration']['target_interval_exclusion'] is None,'baseline target exclusion');
    for k in ('shower_truth_used','orbittrace_target_information_access','orbittrace_canonical_members_access','prior_orbittrace_reveal_access','post_result_parameter_search'): req(r[k] is False,f'baseline firewall {k}')
    req([int(c['rank']) for c in r['candidates']]==list(range(1,EXPECTED_BASELINE_CANDIDATES+1)),'baseline rank order'); return r,g,h

def normalize(row:dict[str,Any])->dict[str,Any]:
    e={'id':str(row['id']),'year':int(row['year']),'sol':float(row['sol']),'sun_lon':float(row['sun_lon']),'ecl_lat':float(row['ecl_lat']),'vg':float(row['vg'])}
    req(e['year'] in YEARS and e['vg']>0 and all(math.isfinite(float(e[k])) for k in ('sol','sun_lon','ecl_lat','vg')),f'bad event {e["id"]}'); return e

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--baseline-pretruth',type=Path,required=True); ap.add_argument('--blind-source-parts',type=Path,required=True); ap.add_argument('--candidate-payload',type=Path,required=True); ap.add_argument('--baseline-payload',type=Path,required=True); ap.add_argument('--scorer-parts',type=Path,required=True); ap.add_argument('--sacv-source',type=Path,required=True); ap.add_argument('--scratch-loader',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args(); a.output.parent.mkdir(parents=True,exist_ok=True); a.scratch_loader.parent.mkdir(parents=True,exist_ok=True)
    req(sha(a.sacv_source)==EXPECTED_SACV_SHA,'SACV scientific source changed'); sacv=load_module(a.sacv_source,'sacv_frozen_target_runtime'); req(sacv.RMAX==1.0 and sacv.MIN_SUPPORT==4 and abs(sacv.CONTAM_MAX-0.10)<1e-15,'SACV constants changed'); req(list(map(float,sacv.DELTAS[1:]))==list(map(float,range(60,301,10))),'SACV analog offsets changed')
    base,gzsha,innersha=load_baseline(a.baseline_pretruth)
    blind=decode_loader(a.blind_source_parts,a.scratch_loader); blind.YEARS=YEARS; blind.MONTH_KEYS=MONTH_KEYS
    ns=types.SimpleNamespace(candidate_payload=a.candidate_payload,baseline_payload=a.baseline_payload,scorer_parts=a.scorer_parts); _c,b,_s=blind.load_sources(ns); byyear,sources=blind.parse_catalogue(b)
    req(sorted(byyear)==list(YEARS),'blind years'); events=[]
    for y in YEARS: events.extend(normalize(x) for x in byyear[y])
    req(len(events)==EXPECTED_EVENT_COUNT,'blind event count'); ids={e['id'] for e in events}; req(len(ids)==EXPECTED_EVENT_COUNT,'duplicate blind ids')
    rt=sacv.Runtime(events); out=[]
    for original in base['candidates'][:MAX_RANK]:
        rank=int(original['rank']); req(rank==len(out)+1,'top100 rank drift'); c=dict(original); c['family_id']=str(original['family_hash']); req(all(str(x) in ids for x in c['event_ids']),f'missing geometry rank {rank}'); r=rt.proc(c,rank); req(set(r['output_ids']).issubset(set(map(str,c['event_ids']))),f'output escaped parent rank {rank}'); out.append(r); print(json.dumps({'rank':rank,'parent':r['parent_n'],'output':r['output_n'],'refined':r['refined']},sort_keys=True),flush=True)
    req([r['rank'] for r in out]==list(range(1,MAX_RANK+1)),'output order'); payload={'schema':'ORBITTRACE_M2D_SACV_V1_FINAL_TARGET_PRETRUTH','scientific_role':'TOP100_ALREADY_BLIND_M2D_RANKING_WITH_FROZEN_SACV_MEMBERSHIPS_BEFORE_TARGET_REFERENCE_ACCESS','baseline_pretruth_gzip_sha256':gzsha,'baseline_pretruth_inner_sha256':innersha,'complete_baseline_candidate_count':EXPECTED_BASELINE_CANDIDATES,'frozen_candidate_count':MAX_RANK,'blind_catalogue_event_count':EXPECTED_EVENT_COUNT,'years':list(YEARS),'success_rank_cap':MAX_RANK,'configuration':{'rmax':float(sacv.RMAX),'minimum_support':int(sacv.MIN_SUPPORT),'contamination_max':float(sacv.CONTAM_MAX),'analog_offsets_deg':[float(x) for x in sacv.DELTAS[1:]],'physical_scales':{'solar_deg':5.0,'radiant_deg':4.0,'speed_fraction':0.10},'fallback':'exact_parent_unless_reciprocal_crossyear_validation'},'extractions':out,'summary':{'refined':sum(bool(r['refined']) for r in out),'mean_parent_n':sum(r['parent_n'] for r in out)/MAX_RANK,'mean_output_n':sum(r['output_n'] for r in out)/MAX_RANK},'parent_rank_changed':False,'parent_membership_changed':False,'target_reference_access':False,'target_information_used':False,'target_coordinates_accessed':False,'canonical_target_ids_accessed':False,'prior_target_reveal_artifact_accessed':False,'target_aware_parent_selection':False,'reranking_used':False,'family_merge_used':False,'post_result_parameter_search':False}
    a.output.write_text(json.dumps(payload,separators=(',',':'),sort_keys=True,allow_nan=False)+'\n'); print('SACV_FINAL_TARGET_STAGE_A_SEALED',sha(a.output),json.dumps(payload['summary'],sort_keys=True),flush=True); return 0
if __name__=='__main__': raise SystemExit(main())
