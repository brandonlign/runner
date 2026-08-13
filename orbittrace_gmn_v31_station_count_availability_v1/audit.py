#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,time,urllib.parse,urllib.request
from collections import Counter
from pathlib import Path

P19_SHA='276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8'
ENDPOINT='https://explore.globalmeteornetwork.org/gmn_rest_api'
CHUNK=40
MIN_COMPLETE=0.95
EXAMPLES={'20260510172934_8o0QO':6,'20260509084953_4tVnz':3}

def req(x,m):
    if not x: raise RuntimeError(m)
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def safe_id(x):
    x=str(x); req(x and all(c.isalnum() or c=='_' for c in x),f'unsafe event id {x!r}'); return x

def request(sql,attempts=4):
    url=ENDPOINT+'?'+urllib.parse.urlencode({'sql':sql,'data_shape':'objects','data_format':'json'})
    err=None
    for a in range(attempts):
        try:
            r=urllib.request.Request(url,headers={'User-Agent':'orbittrace-v31-station-availability-v1/1.0'})
            with urllib.request.urlopen(r,timeout=30) as f: payload=json.loads(f.read())
            req(payload.get('ok') is True,'GMN REST response not ok')
            req(payload.get('truncated') is False,'GMN REST response truncated')
            return payload.get('rows',[])
        except Exception as e:
            err=e
            if a+1<attempts: time.sleep(2**a)
    raise RuntimeError(f'GMN REST request failed: {err}')

def count_batch(ids):
    quoted=','.join("'"+safe_id(x)+"'" for x in ids)
    sql=('SELECT meteor_unique_trajectory_identifier, COUNT(*) AS n_station '
         'FROM participating_station WHERE meteor_unique_trajectory_identifier IN ('+quoted+') '
         'GROUP BY meteor_unique_trajectory_identifier')
    rows=request(sql); out={}
    for row in rows:
        eid=safe_id(row['meteor_unique_trajectory_identifier']); n=int(row['n_station'])
        req(eid in ids,'REST returned unrequested ID'); req(eid not in out,'duplicate aggregated ID'); req(n>=1,'nonpositive station count'); out[eid]=n
    return out

def main():
    p=argparse.ArgumentParser();p.add_argument('--p19-prelabel-json',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    req(sha(a.p19_prelabel_json)==P19_SHA,'P19 payload drift'); q=json.loads(a.p19_prelabel_json.read_text()); fam=q['hard_families']; req(len(fam)==226,'hard family count drift')
    ids=sorted({safe_id(e) for f in fam for e in f['event_ids']}); req(len(ids)==8794,'unique hard-member count drift')
    years=Counter(int(x[:4]) for x in ids); req(years==Counter({2022:4726,2023:4068}),f'year counts drift {years}')
    # Non-project public API sanity check before immutable member queries.
    test=count_batch(list(EXAMPLES)); req(test==EXAMPLES,f'public station-count sanity mismatch {test}')
    counts={}
    for start in range(0,len(ids),CHUNK):
        batch=ids[start:start+CHUNK]; got=count_batch(batch); counts.update(got)
        if start==0 or (start//CHUNK+1)%10==0: print(f'station availability {min(start+CHUNK,len(ids))}/{len(ids)}',flush=True)
    req(set(counts).issubset(ids),'count universe drift')
    stats={}; gates=[]
    for y in (2022,2023):
        wanted=[x for x in ids if int(x[:4])==y]; matched=[x for x in wanted if x in counts and isinstance(counts[x],int) and counts[x]>=2]
        frac=len(matched)/len(wanted); gate=frac>=MIN_COMPLETE; gates.append(gate); stats[str(y)]={'requested':len(wanted),'matched_integer_ge2':len(matched),'complete_fraction':frac,'gate_at_least_0_95':gate}
    hist=Counter(counts[x] for x in ids if x in counts)
    verdict='PASS_GMN_V31_STATION_COUNT_AVAILABILITY_V1' if all(gates) else 'FAIL_GMN_V31_STATION_COUNT_AVAILABILITY_V1'
    ordered={x:int(counts[x]) for x in ids if x in counts}; mapping_sha=hashlib.sha256(json.dumps(ordered,separators=(',',':'),sort_keys=True).encode()).hexdigest()
    result={'verdict':verdict,'p19_sha256':P19_SHA,'family_count':226,'unique_member_count':8794,'year_counts':dict(sorted(years.items())),'minimum_complete_fraction':MIN_COMPLETE,'year_stats':stats,'station_count_histogram_diagnostic_only':{str(k):v for k,v in sorted(hist.items())},'count_mapping_sha256':mapping_sha,'api_public_example_sanity':test,'station_codes_emitted':False,'station_geography_accessed':False,'meteor_geometry_accessed':False,'shower_truth_accessed':False,'scientific_ranking_computed':False,'sonotaco_scientific_access':False,'target_information_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False}
    (a.output/'GMN_V31_STATION_COUNT_AVAILABILITY_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    (a.output/'station_counts.json').write_text(json.dumps(ordered,separators=(',',':'),sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True));return 0
if __name__=='__main__': raise SystemExit(main())
