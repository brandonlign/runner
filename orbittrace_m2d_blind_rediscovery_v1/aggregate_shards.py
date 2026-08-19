#!/usr/bin/env python3
from __future__ import annotations
import argparse,gzip,hashlib,json
from pathlib import Path

CENTERS=tuple(float(5+10*i) for i in range(36))
def req(x,msg):
    if not x:raise RuntimeError(msg)
def sha(b):return hashlib.sha256(b).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--shard-count',type=int,default=6);a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    files=sorted(a.input.rglob('M2D_SHARD_*.json.gz'));req(len(files)==a.shard_count,f'shard file count {len(files)}')
    shards=[json.loads(gzip.decompress(p.read_bytes())) for p in files];req({s['shard_index'] for s in shards}==set(range(a.shard_count)),'shard indices')
    centers=sorted(c for s in shards for c in s['centers']);req(centers==list(CENTERS),f'center coverage {centers}')
    first_sources=shards[0]['catalogue_sources'];req(all(s['catalogue_sources']==first_sources for s in shards),'catalogue source mismatch')
    req(all(s['target_information_access'] is False and s['canonical_ids_accessed'] is False and s['shower_labels_used'] is False for s in shards),'shard firewall')
    dedup={}
    for s in shards:
        for row in s['candidates']:
            ids=tuple(sorted(map(str,row['event_ids'])));old=dedup.get(ids)
            if old is None:dedup[ids]=dict(row)
            else:
                old['window_centers']=sorted(set(old['window_centers']+row['window_centers']))
                if (float(row['internal_2d_mass']),float(row['modal_contrast']))>(float(old['internal_2d_mass']),float(old['modal_contrast'])):
                    old['internal_2d_mass']=float(row['internal_2d_mass']);old['modal_contrast']=float(row['modal_contrast'])
    ranked=list(dedup.values());ranked.sort(key=lambda r:(-float(r['internal_2d_mass']),-float(r['modal_contrast']),str(r['family_hash'])))
    for i,r in enumerate(ranked,1):r['rank']=i
    summaries=sorted((x for s in shards for x in s['window_summary']),key=lambda x:x['center'])
    payload={'schema':'ORBITTRACE_M2D_BLIND_REDISCOVERY_V1_PRETRUTH','scientific_role':'TARGET_FREE_FULL_YEAR_WINDOWED_M2D_SCAN','years':[2022,2023],'window_centers':list(CENTERS),'window_half_width_deg':15.0,'candidate_count':len(ranked),'catalogue_sources':first_sources,'window_summary':summaries,'candidates':ranked,'target_information_access':False,'canonical_ids_accessed':False,'shower_labels_used':False,'post_result_parameter_search':False,'execution_partition_only':{'shards':a.shard_count}}
    raw=json.dumps(payload,separators=(',',':'),sort_keys=True,allow_nan=False).encode();gz=gzip.compress(raw,mtime=0);out=a.output/'M2D_BLIND_PRETRUTH.json.gz';out.write_bytes(gz);digest=sha(gz);(a.output/'M2D_BLIND_PRETRUTH.sha256').write_text(digest+'  M2D_BLIND_PRETRUTH.json.gz\n')
    lines=['# M2D target-free blind scan','',f'Pretruth SHA-256: `{digest}`','',f'Unique ranked candidate families: **{len(ranked):,}**','', 'All 36 generic 30° seasonal windows were processed before target IDs were available.','', '| rank | members | M2D | windows |','|---:|---:|---:|---|']
    for r in ranked[:50]:lines.append(f"| {r['rank']} | {r['member_count']} | {r['internal_2d_mass']:.12g} | {','.join(f'{x:.0f}' for x in r['window_centers'])} |")
    (a.output/'M2D_BLIND_PRETRUTH.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines))

if __name__=='__main__':main()
