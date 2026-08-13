#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json,math,tempfile,urllib.request
from collections import Counter
from pathlib import Path

P19_SHA='276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8'
YEARS=(2022,2023); MONTHS=tuple(range(1,13)); BLIND=(20.0,55.0); MIN_COMPLETE=0.95
URL='https://globalmeteornetwork.org/data/traj_summary_data/monthly/traj_summary_monthly_{year}{month:02d}.txt'
ID=0; SOL=5; NUM_STAT=84

def req(x,m):
    if not x: raise RuntimeError(m)
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def finite(x):
    try: v=float((x or '').strip())
    except ValueError: return None
    return v if math.isfinite(v) else None

def fetch(url,path):
    h=hashlib.sha256(); n=0; r=urllib.request.Request(url,headers={'User-Agent':'orbittrace-v31-observer-count-file-v1/1.0'})
    with urllib.request.urlopen(r,timeout=300) as z,path.open('wb') as out:
        while True:
            b=z.read(1<<20)
            if not b: break
            h.update(b);n+=len(b);out.write(b)
    return {'url':url,'bytes':n,'sha256':h.hexdigest()}

def main():
    p=argparse.ArgumentParser();p.add_argument('--p19-prelabel-json',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    req(sha(a.p19_prelabel_json)==P19_SHA,'P19 payload drift'); payload=json.loads(a.p19_prelabel_json.read_text()); families=payload['hard_families']; req(len(families)==226,'family count drift')
    ids=sorted({str(e) for f in families for e in f['event_ids']}); req(len(ids)==8794,'unique member count drift'); wanted=set(ids)
    year_counts=Counter(int(x[:4]) for x in ids); req(year_counts==Counter({2022:4726,2023:4068}),f'year count drift {year_counts}')
    found={}; sources=[]; protected=0
    with tempfile.TemporaryDirectory(prefix='orbittrace_numstat_') as td:
        root=Path(td)
        for y in YEARS:
            for m in MONTHS:
                path=root/f'{y}{m:02d}.txt'; meta=fetch(URL.format(year=y,month=m),path); meta.update(year=y,month=m);sources.append(meta)
                with path.open('r',encoding='utf-8-sig',errors='replace',newline='') as f:
                    for row in csv.reader(f,delimiter=';'):
                        if not row or row[0].lstrip().startswith('#') or len(row)<=SOL: continue
                        eid=row[ID].strip(); sol=finite(row[SOL])
                        if not eid or sol is None or not 0<=sol<360: continue
                        if BLIND[0]<=sol<=BLIND[1]: protected+=1; continue
                        if eid not in wanted: continue
                        if len(row)<=NUM_STAT: count=None
                        else:
                            v=finite(row[NUM_STAT]); count=int(round(v)) if v is not None and abs(v-round(v))<=1e-9 else None
                        key=(y,eid); req(key not in found,f'duplicate immutable member {key}');found[key]=count
                path.unlink(missing_ok=True)
    req(len(sources)==24,'monthly source count drift')
    stats={};gates=[];hist=Counter()
    for y in YEARS:
        yids=[x for x in ids if int(x[:4])==y]; valid=[]
        for eid in yids:
            n=found.get((y,eid))
            if isinstance(n,int) and n>=2: valid.append(eid);hist[n]+=1
        frac=len(valid)/len(yids);gate=frac>=MIN_COMPLETE;gates.append(gate);stats[str(y)]={'requested':len(yids),'valid_integer_ge2':len(valid),'complete_fraction':frac,'gate_at_least_0_95':gate}
    verdict='PASS_GMN_V31_OBSERVER_COUNT_FILE_AVAILABILITY_V1' if all(gates) else 'FAIL_GMN_V31_OBSERVER_COUNT_FILE_AVAILABILITY_V1'
    result={'verdict':verdict,'family_count':226,'unique_member_count':8794,'year_counts':{str(k):v for k,v in sorted(year_counts.items())},'minimum_complete_fraction':MIN_COMPLETE,'year_stats':stats,'observer_count_histogram_diagnostic_only':{str(k):v for k,v in sorted(hist.items())},'monthly_sources':sources,'protected_rows_discarded_before_num_stat':protected,'per_event_counts_emitted':False,'shower_truth_accessed':False,'meteor_geometry_interpreted_beyond_firewall_sol':False,'scientific_ranking_computed':False,'sonotaco_scientific_access':False,'target_information_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False}
    (a.output/'GMN_V31_OBSERVER_COUNT_FILE_AVAILABILITY_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return 0
if __name__=='__main__': raise SystemExit(main())
