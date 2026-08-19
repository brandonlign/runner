#!/usr/bin/env python3
from __future__ import annotations

import argparse, base64, gzip, hashlib, importlib.util, json, math, struct, subprocess, sys, tempfile, types
from pathlib import Path
from typing import Any

import numpy as np
from scipy.spatial import cKDTree

YEARS=(2022,2023)
MONTH_KEYS=tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1,13))
WINDOW_CENTERS=tuple(float(5+10*i) for i in range(36))
WINDOW_HALF_WIDTH=15.0
RADIUS=1.0
MIN_SUPPORT=4


def req(x:bool,msg:str)->None:
    if not x: raise RuntimeError(msg)

def sha_bytes(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def member_hash(ids:list[str])->str:return hashlib.sha256("|".join(sorted(ids)).encode()).hexdigest()[:20]

def load_module(path:Path,name:str)->Any:
    s=importlib.util.spec_from_file_location(name,path);req(s is not None and s.loader is not None,f"cannot import {path}")
    m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m

def decode_blind_source(parts_root:Path,out:Path)->Any:
    parts=sorted(parts_root.glob('part*.b64'))
    req([p.name for p in parts]==[f'part{i:02d}.b64' for i in range(4)],f"bad blind source parts {[p.name for p in parts]}")
    enc=''.join(''.join(p.read_text().split()) for p in parts)
    raw=gzip.decompress(base64.b64decode(enc,validate=True))
    req(len(raw)==24135,f"blind source byte count {len(raw)}")
    forbidden=['april_candidate_members.csv','247.17','-14.34','37.62','OrbitTrace-April-36.9']
    req(not any(x in raw.decode() for x in forbidden),'target literal in blind scanner source')
    out.write_bytes(raw)
    return load_module(out,'m2d_blind_transport')

def support_event(r:dict[str,Any])->dict[str,Any]:
    o={'id':str(r['id']),'year':int(r['year']),'sol':float(r['sol']),'lon':float(r['sun_lon']),'lat':float(r['ecl_lat']),'vg':float(r['vg'])}
    req(all(math.isfinite(float(o[k])) for k in ('sol','lon','lat','vg')) and o['vg']>0,'bad support event')
    return o

def window_events(all_events:list[dict[str,Any]],center:float,base:Any)->list[dict[str,Any]]:
    return [e for e in all_events if abs(float(base.wrap180(float(e['sol'])-center)))<=WINDOW_HALF_WIDTH]

def build_binary(events:list[dict[str,Any]],candidates:list[dict[str,Any]],structural:Any,path:Path)->dict[str,Any]:
    ordered=sorted(events,key=lambda e:str(e['id']))
    ids=[str(e['id']) for e in ordered]; idx={eid:i for i,eid in enumerate(ids)}
    Z=structural.physical_embedding(ordered)
    raw=cKDTree(Z).query_ball_point(Z,r=RADIUS,p=2.0,eps=0.0,return_sorted=True)
    years=np.asarray([int(e['year']) for e in ordered],dtype=np.int16)
    counts={y:int(np.count_nonzero(years==y)) for y in YEARS}
    req(all(counts[y]>0 for y in YEARS),f'empty annual window {counts}')
    d0=np.fromiter((sum(years[j]==YEARS[0] for j in ns) for ns in raw),dtype=np.int32,count=len(raw))
    d1=np.fromiter((sum(years[j]==YEARS[1] for j in ns) for ns in raw),dtype=np.int32,count=len(raw))
    cand_of=np.full(len(ordered),-1,dtype=np.int32)
    for ci,c in enumerate(candidates):
        for eid in c['event_ids']:
            g=idx[str(eid)];req(cand_of[g]<0,'support-cut candidate overlap');cand_of[g]=ci
    with path.open('wb') as f:
        f.write(b'OTIM1\0\0\0');f.write(struct.pack('<III',counts[YEARS[0]],counts[YEARS[1]],len(candidates)))
        for ci,c in enumerate(candidates):
            inds=[idx[str(e)] for e in c['event_ids']]; local={g:i for i,g in enumerate(inds)}; internal=[];cross=[]
            for li,g in enumerate(inds):
                for j in raw[g]:
                    if j==g:continue
                    cj=int(cand_of[j])
                    if cj==ci:
                        if j>g:internal.append((li,local[j]))
                    else:
                        a=min(int(d0[g]),int(d0[j]));b=min(int(d1[g]),int(d1[j]))
                        if a>0 and b>0:cross.append((li,a,b))
            f.write(struct.pack('<III',len(inds),len(internal),len(cross)))
            for g in inds:f.write(struct.pack('<ii',int(d0[g]),int(d1[g])))
            for u,v in internal:f.write(struct.pack('<II',u,v))
            for u,a,b in cross:f.write(struct.pack('<Iii',u,a,b))
    return {'event_count':len(ordered),'annual_counts':{str(k):v for k,v in counts.items()},'candidate_count':len(candidates)}

def parse_scores(path:Path)->dict[int,float]:
    lines=path.read_text().splitlines();req(lines and lines[0].startswith('candidate\t'),'score header')
    out={}
    for line in lines[1:]:
        p=line.split('\t');out[int(p[0])]=float(p[4])
    return out

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--blind-source-parts',type=Path,required=True)
    ap.add_argument('--candidate-payload',type=Path,required=True)
    ap.add_argument('--baseline-payload',type=Path,required=True)
    ap.add_argument('--scorer-parts',type=Path,required=True)
    ap.add_argument('--support-source',type=Path,required=True)
    ap.add_argument('--structural-source',type=Path,required=True)
    ap.add_argument('--exact-exe',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    req(a.exact_exe.exists(),'missing exact M2D executable')

    with tempfile.TemporaryDirectory() as td0:
        td=Path(td0)
        blind=decode_blind_source(a.blind_source_parts,td/'blind.py')
        blind.YEARS=YEARS;blind.MONTH_KEYS=MONTH_KEYS
        load_args=types.SimpleNamespace(candidate_payload=a.candidate_payload,baseline_payload=a.baseline_payload,scorer_parts=a.scorer_parts)
        _candidate,base,_scorer=blind.load_sources(load_args)
        by_year,sources=blind.parse_catalogue(base)
        req(sorted(by_year)==list(YEARS),f'wrong years {sorted(by_year)}')
        all_events=[]
        for y in YEARS: all_events.extend(support_event(e) for e in by_year[y])
        req(len({e['id'] for e in all_events})==len(all_events),'duplicate pooled IDs')
        support=load_module(a.support_source,'m2d_support_cut')
        structural=load_module(a.structural_source,'m2d_structural')
        req(float(support.RADIUS)==RADIUS and int(support.MIN_SUPPORT)==MIN_SUPPORT,'support constants changed')
        req(float(structural.RADIUS)==RADIUS and int(structural.MIN_SUPPORT)==MIN_SUPPORT,'structural constants changed')

        dedup:dict[tuple[str,...],dict[str,Any]]={}
        window_summary=[]
        for wi,center in enumerate(WINDOW_CENTERS):
            events=window_events(all_events,center,base)
            annual={y:sum(int(e['year'])==y for e in events) for y in YEARS}
            req(min(annual.values())>=1000,f'window {center} underpowered {annual}')
            print(f'[m2d] window {wi+1}/36 center={center:.1f} n={len(events):,} annual={annual}',flush=True)
            candidates,ss=support.support_resolved_cut(structural,events)
            req(bool(candidates),f'no candidates window {center}')
            binp=td/f'w{wi:02d}.bin';scorep=td/f'w{wi:02d}.tsv';errp=td/f'w{wi:02d}.stderr'
            bs=build_binary(events,candidates,structural,binp)
            with errp.open('wb') as ef: subprocess.run([str(a.exact_exe),str(binp),str(scorep)],check=True,stdout=subprocess.DEVNULL,stderr=ef)
            scores=parse_scores(scorep);req(len(scores)==len(candidates),f'missing M2D scores window {center}')
            for ci,c in enumerate(candidates):
                ids=tuple(sorted(map(str,c['event_ids'])))
                row={'family_hash':member_hash(list(ids)),'event_ids':list(ids),'member_count':len(ids),'internal_2d_mass':float(scores[ci]),'modal_contrast':float(c['modal_contrast']),'window_centers':[center]}
                old=dedup.get(ids)
                if old is None:dedup[ids]=row
                else:
                    old['window_centers']=sorted(set(old['window_centers']+[center]))
                    if (row['internal_2d_mass'],row['modal_contrast'])>(old['internal_2d_mass'],old['modal_contrast']):
                        old['internal_2d_mass']=row['internal_2d_mass'];old['modal_contrast']=row['modal_contrast']
            window_summary.append({'center':center,'event_count':len(events),'annual_counts':{str(k):v for k,v in annual.items()},'candidate_count':len(candidates),'support_summary':ss,'binary_summary':bs})
            binp.unlink(missing_ok=True);scorep.unlink(missing_ok=True);errp.unlink(missing_ok=True)

        ranked=list(dedup.values())
        ranked.sort(key=lambda r:(-float(r['internal_2d_mass']),-float(r['modal_contrast']),str(r['family_hash'])))
        for rank,r in enumerate(ranked,1):r['rank']=rank
        payload={'schema':'ORBITTRACE_M2D_BLIND_REDISCOVERY_V1_PRETRUTH','scientific_role':'TARGET_FREE_FULL_YEAR_WINDOWED_M2D_SCAN','years':list(YEARS),'window_centers':list(WINDOW_CENTERS),'window_half_width_deg':WINDOW_HALF_WIDTH,'candidate_count':len(ranked),'catalogue_sources':sources,'window_summary':window_summary,'candidates':ranked,'target_information_access':False,'canonical_ids_accessed':False,'shower_labels_used':False,'post_result_parameter_search':False}
        raw=json.dumps(payload,separators=(',',':'),sort_keys=True,allow_nan=False).encode();gz=gzip.compress(raw,mtime=0)
        out=a.output/'M2D_BLIND_PRETRUTH.json.gz';out.write_bytes(gz)
        digest=sha_bytes(gz);(a.output/'M2D_BLIND_PRETRUTH.sha256').write_text(digest+'  M2D_BLIND_PRETRUTH.json.gz\n')
        lines=['# M2D target-free blind scan','',f'Pretruth SHA-256: `{digest}`','',f'Unique ranked candidate families: **{len(ranked):,}**','', 'No OrbitTrace canonical member table, coordinate, activity interval, or prior family identity was accessed before this ranking was frozen.','', '| rank | members | M2D | windows |','|---:|---:|---:|---|']
        for r in ranked[:50]:lines.append(f"| {r['rank']} | {r['member_count']} | {r['internal_2d_mass']:.12g} | {','.join(f'{x:.0f}' for x in r['window_centers'])} |")
        (a.output/'M2D_BLIND_PRETRUTH.md').write_text('\n'.join(lines)+'\n')
        print('\n'.join(lines),flush=True)
    return 0

if __name__=='__main__':raise SystemExit(main())
