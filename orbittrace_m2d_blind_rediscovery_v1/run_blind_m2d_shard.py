#!/usr/bin/env python3
from __future__ import annotations
import argparse,gzip,json,subprocess,tempfile,types
from pathlib import Path
import run_blind_m2d as core


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--shard-index',type=int,required=True);ap.add_argument('--shard-count',type=int,required=True)
    ap.add_argument('--blind-source-parts',type=Path,required=True);ap.add_argument('--candidate-payload',type=Path,required=True);ap.add_argument('--baseline-payload',type=Path,required=True);ap.add_argument('--scorer-parts',type=Path,required=True);ap.add_argument('--support-source',type=Path,required=True);ap.add_argument('--structural-source',type=Path,required=True);ap.add_argument('--exact-exe',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True);core.req(0<=a.shard_index<a.shard_count,'bad shard')
    centers=[c for i,c in enumerate(core.WINDOW_CENTERS) if i%a.shard_count==a.shard_index];core.req(centers,'empty shard')
    with tempfile.TemporaryDirectory() as td0:
        td=Path(td0);blind=core.decode_blind_source(a.blind_source_parts,td/'blind.py');blind.YEARS=core.YEARS;blind.MONTH_KEYS=core.MONTH_KEYS
        la=types.SimpleNamespace(candidate_payload=a.candidate_payload,baseline_payload=a.baseline_payload,scorer_parts=a.scorer_parts)
        _c,base,_s=blind.load_sources(la);by_year,sources=blind.parse_catalogue(base)
        all_events=[]
        for y in core.YEARS:all_events.extend(core.support_event(e) for e in by_year[y])
        core.req(len({e['id'] for e in all_events})==len(all_events),'duplicate IDs')
        support=core.load_module(a.support_source,f'm2d_support_{a.shard_index}');structural=core.load_module(a.structural_source,f'm2d_structural_{a.shard_index}')
        core.req(float(support.RADIUS)==1.0 and int(support.MIN_SUPPORT)==4,'support constants');core.req(float(structural.RADIUS)==1.0 and int(structural.MIN_SUPPORT)==4,'structural constants')
        dedup={};summaries=[]
        for center in centers:
            events=core.window_events(all_events,center,base);annual={y:sum(int(e['year'])==y for e in events) for y in core.YEARS};core.req(min(annual.values())>=1000,f'underpowered {center} {annual}')
            print(f'[shard {a.shard_index}] center={center:.1f} n={len(events):,}',flush=True)
            candidates,ss=support.support_resolved_cut(structural,events);core.req(bool(candidates),f'no candidates {center}')
            binp=td/f'w{int(center):03d}.bin';scorep=td/f'w{int(center):03d}.tsv';errp=td/f'w{int(center):03d}.stderr'
            bs=core.build_binary(events,candidates,structural,binp)
            with errp.open('wb') as ef:subprocess.run([str(a.exact_exe),str(binp),str(scorep)],check=True,stdout=subprocess.DEVNULL,stderr=ef)
            scores=core.parse_scores(scorep);core.req(len(scores)==len(candidates),'score count')
            for ci,c in enumerate(candidates):
                ids=tuple(sorted(map(str,c['event_ids'])));row={'family_hash':core.member_hash(list(ids)),'event_ids':list(ids),'member_count':len(ids),'internal_2d_mass':float(scores[ci]),'modal_contrast':float(c['modal_contrast']),'window_centers':[center]};old=dedup.get(ids)
                if old is None:dedup[ids]=row
                else:
                    old['window_centers']=sorted(set(old['window_centers']+[center]))
                    if (row['internal_2d_mass'],row['modal_contrast'])>(old['internal_2d_mass'],old['modal_contrast']):old.update({k:row[k] for k in ('internal_2d_mass','modal_contrast')})
            summaries.append({'center':center,'event_count':len(events),'annual_counts':{str(k):v for k,v in annual.items()},'candidate_count':len(candidates),'support_summary':ss,'binary_summary':bs})
            for p in (binp,scorep,errp):p.unlink(missing_ok=True)
        payload={'schema':'ORBITTRACE_M2D_BLIND_REDISCOVERY_V1_SHARD','shard_index':a.shard_index,'shard_count':a.shard_count,'centers':centers,'catalogue_sources':sources,'window_summary':summaries,'candidates':list(dedup.values()),'target_information_access':False,'canonical_ids_accessed':False,'shower_labels_used':False}
        raw=json.dumps(payload,separators=(',',':'),sort_keys=True,allow_nan=False).encode();out=a.output/f'M2D_SHARD_{a.shard_index}.json.gz';out.write_bytes(gzip.compress(raw,mtime=0));(a.output/f'M2D_SHARD_{a.shard_index}.sha256').write_text(core.sha_bytes(out.read_bytes())+'\n')
        print(f'shard {a.shard_index} complete: centers={centers} unique={len(dedup)}',flush=True)

if __name__=='__main__':main()
