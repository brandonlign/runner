#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,math,tempfile
from pathlib import Path
import active_scan,geometry,raw_members
P19_SHA='276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8'; TOL=1e-9

def req(x,m):
    if not x: raise RuntimeError(m)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser()
    for n in ('p19-prelabel-json','quality-source','support-source-parts','candidate-payload','baseline-payload','scorer-parts','v8-result-json','output'): p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True);req(sha(a.p19_prelabel_json)==P19_SHA,'P19 payload drift')
    q=json.loads(a.p19_prelabel_json.read_text()); fam=q['hard_families'];req(len(fam)==226,'hard family count drift')
    members=sorted({str(e) for f in fam for e in f['event_ids']}); req(members,'empty member universe')
    scan=active_scan.load(a); lookup={(y,str(r['id'])):r for y in (2022,2023) for r in scan[y]}
    with tempfile.TemporaryDirectory(prefix='orbittrace_v31_member_pkg_') as td: raw,sources,protected=raw_members.read(set(members),Path(td))
    out=[]; maxerr={'sol':0.0,'sun_lon':0.0,'ecl_lat':0.0,'vg':0.0}
    for eid in members:
        y=int(eid[:4]); req(y in (2022,2023),f'bad member year {eid}'); key=(y,eid); req(key in raw,f'missing raw member {eid}'); req(key in lookup,f'missing active member {eid}')
        sol,ra,dec,vg,sra,sdec,svg=raw[key]; vals=(sol,ra,dec,vg,sra,sdec,svg); req(all(v is not None and math.isfinite(v) for v in vals),f'incomplete raw member {eid}'); req(vg>0 and sra>=0 and sdec>=0 and svg>=0,f'invalid raw member {eid}')
        c=geometry.canonical(sol,ra,dec,vg); arow=lookup[key]
        err={'sol':geometry.circular_error(c[0],arow['sol']),'sun_lon':geometry.circular_error(c[1],arow['sun_lon']),'ecl_lat':abs(c[2]-float(arow['ecl_lat'])),'vg':abs(c[3]-float(arow['vg']))}
        for k,v in err.items(): maxerr[k]=max(maxerr[k],v); req(v<=TOL,f'canonical mismatch {eid} {k} {v}')
        out.append({'id':eid,'year':y,'sol':sol,'ra':ra,'dec':dec,'vg':vg,'ra_sigma':sra,'dec_sigma':sdec,'vg_sigma':svg})
    path=a.output/'GMN_V31_HARD_MEMBER_MEASUREMENTS.jsonl'
    with path.open('w') as f:
        for r in out: f.write(json.dumps(r,separators=(',',':'),sort_keys=True,allow_nan=False)+'\n')
    manifest={'verdict':'PASS_GMN_V31_MEASUREMENT_UNCERTAINTY_PACKAGE_V1','family_count':226,'unique_member_count':len(members),'packaged_member_count':len(out),'complete_member_fraction':len(out)/len(members),'package_sha256':sha(path),'max_canonical_error':maxerr,'equivalence_tolerance':TOL,'monthly_sources':sources,'protected_rows_discarded_before_geometry':protected,'labels_read':False,'scientific_ranking_computed':False,'candidate_membership_changed':False,'blind_exclusion':[20.0,55.0],'sonotaco_2013_2014_access':False,'target_information_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False}
    (a.output/'GMN_V31_MEASUREMENT_UNCERTAINTY_PACKAGE_MANIFEST.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n'); print(json.dumps(manifest,indent=2,sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
