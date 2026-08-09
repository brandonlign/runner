#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

EXPECTED_P5_MEMBERSHIP_SHA='933be44170bc91cf8e92a38b84689d590610ecdf809e911ac40022b5d4e806c9'
EXPECTED_P5_DECISIONS_SHA='b9b87427e8d5521e92bca3d27ef9528da7509f2c9d5a647764789abc65323711'
EXPECTED_CROSSFIT_SHA='55defa606101cfc0e0f9038d326fd19cfd99d0c423b68602ecd5581e00ff8ac1'
EXPECTED_MODEL_SHA='8ac8b13ab025a636884d44a2b19d478c9de5c138c3da190f3dfe3d73490257eb'
EXPECTED_FAMILY_COUNT=226
EXPECTED_P5_ASSIGNMENTS=24946
EXPECTED_ELIGIBLE_FAMILIES=218
EXPECTED_INELIGIBLE_FAMILIES=8
EXPECTED_DROPPED_ASSIGNMENTS=3320
EXPECTED_P6_ASSIGNMENTS=21626
EXPECTED_P6_GAINING_FAMILIES=214
EXPECTED_P6_MEMBERSHIP_SHA='40b0b720ef37427bc2d89aeb71c145683cbc69eff9b56ac5516e87fc34348ff6'
EXPECTED_P6_DECISIONS_SHA='5e76bbf2fd75acdf1d1bc770dc3c60de338a6388524c956544afe4c1aabc8490'


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument('--p5-expanded-families',required=True,type=Path)
    p.add_argument('--p5-membership-sha',required=True,type=Path)
    p.add_argument('--p5-decisions',required=True,type=Path)
    p.add_argument('--p5-decisions-sha',required=True,type=Path)
    p.add_argument('--crossfit-json',required=True,type=Path)
    p.add_argument('--crossfit-sha',required=True,type=Path)
    p.add_argument('--model-sha',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)

    require(a.p5_membership_sha.read_text().strip()==EXPECTED_P5_MEMBERSHIP_SHA,'P5 stored membership SHA changed')
    require(a.p5_decisions_sha.read_text().strip()==EXPECTED_P5_DECISIONS_SHA,'P5 stored decisions SHA changed')
    require(a.crossfit_sha.read_text().strip()==EXPECTED_CROSSFIT_SHA,'P5 crossfit SHA changed')
    require(a.model_sha.read_text().strip()==EXPECTED_MODEL_SHA,'P5 model SHA changed')

    p5_raw=gzip.decompress(a.p5_expanded_families.read_bytes())
    require(hashlib.sha256(p5_raw).hexdigest()==EXPECTED_P5_MEMBERSHIP_SHA,'P5 expanded membership payload changed')
    p5_families=json.loads(p5_raw)
    require(len(p5_families)==EXPECTED_FAMILY_COUNT,'P5 family count changed')
    require(canonical_sha(p5_families)==EXPECTED_P5_MEMBERSHIP_SHA,'P5 family canonical identity changed')

    decisions_raw=gzip.decompress(a.p5_decisions.read_bytes())
    require(hashlib.sha256(decisions_raw).hexdigest()==EXPECTED_P5_DECISIONS_SHA,'P5 decisions payload changed')
    p5_decisions=json.loads(decisions_raw)
    assignments=p5_decisions['assignments']
    require(len(assignments)==EXPECTED_P5_ASSIGNMENTS,'P5 assignment count changed')

    crossfit=json.loads(a.crossfit_json.read_text())
    require(canonical_sha(crossfit)==EXPECTED_CROSSFIT_SHA,'P5 crossfit canonical payload changed')
    reliability=crossfit['reliability']
    require(len(reliability)==452,'P5 family-direction count changed')

    status: dict[str,list[bool]]={}
    for rec in reliability.values():
        fid=str(rec['family_id'])
        status.setdefault(fid,[]).append(bool(rec['reliable']))
    require(len(status)==EXPECTED_FAMILY_COUNT,'P5 crossfit family universe changed')
    require(all(len(v)==2 for v in status.values()),'family does not have exactly two reciprocal directions')
    eligible=sorted(fid for fid,v in status.items() if all(v))
    ineligible=sorted(fid for fid,v in status.items() if not all(v))
    require(len(eligible)==EXPECTED_ELIGIBLE_FAMILIES,'eligible-family count changed')
    require(len(ineligible)==EXPECTED_INELIGIBLE_FAMILIES,'ineligible-family count changed')
    eligible_set=set(eligible)

    p6_families=[]
    dropped=[]
    for family in p5_families:
        row=json.loads(json.dumps(family))
        fid=str(row['family_id'])
        additions=set(map(str,row.get('p2_added_event_ids',[])))
        members=set(map(str,row['event_ids']))
        require(additions <= members,f'P5 addition outside expanded family {fid}')
        seeds=members-additions
        require(bool(seeds),f'empty immutable v8 seed family {fid}')
        keep=additions if fid in eligible_set else set()
        if fid not in eligible_set:
            dropped.extend(sorted(additions))
        row['p2_added_event_ids']=sorted(keep)
        row['p2_added_event_count']=len(keep)
        row['event_ids']=sorted(seeds|keep)
        row['event_count']=len(row['event_ids'])
        p6_families.append(row)

    order=[str(f['family_id']) for f in p6_families]
    require(len(order)==len(set(order))==EXPECTED_FAMILY_COUNT,'P6 family IDs/order changed')
    p6_raw=canonical_bytes(p6_families)
    p6_membership_sha=hashlib.sha256(p6_raw).hexdigest()
    require(p6_membership_sha==EXPECTED_P6_MEMBERSHIP_SHA,f'P6 membership SHA changed: {p6_membership_sha}')

    p6_assignments={eid:assignments[eid] for eid in sorted(assignments) if str(assignments[eid]['family_id']) in eligible_set}
    decision_payload={
        'source_p5_decisions_sha256': EXPECTED_P5_DECISIONS_SHA,
        'bidirectionally_reliable_family_ids': eligible,
        'ineligible_family_ids': ineligible,
        'dropped_assignment_event_ids': sorted(set(dropped)),
        'assignments': p6_assignments,
    }
    p6_decision_raw=canonical_bytes(decision_payload)
    p6_decisions_sha=hashlib.sha256(p6_decision_raw).hexdigest()
    require(p6_decisions_sha==EXPECTED_P6_DECISIONS_SHA,f'P6 decisions SHA changed: {p6_decisions_sha}')
    require(len(set(dropped))==EXPECTED_DROPPED_ASSIGNMENTS,'P6 dropped-assignment count changed')
    require(len(p6_assignments)==EXPECTED_P6_ASSIGNMENTS,'P6 retained-assignment count changed')
    require(sum(int(f.get('p2_added_event_count',0)) for f in p6_families)==EXPECTED_P6_ASSIGNMENTS,'P6 family addition count changed')
    require(sum(bool(f.get('p2_added_event_count',0)) for f in p6_families)==EXPECTED_P6_GAINING_FAMILIES,'P6 gaining-family count changed')
    require(all(int(f.get('p2_added_event_count',0))==0 for f in p6_families if str(f['family_id']) in set(ineligible)),'ineligible family retained P6 addition')

    (a.output/'p6_expanded_families.json.gz').write_bytes(gzip.compress(p6_raw))
    (a.output/'p6_membership_pretruth.sha256').write_text(p6_membership_sha+'\n')
    (a.output/'p6_decisions_pretruth.json.gz').write_bytes(gzip.compress(p6_decision_raw))
    (a.output/'p6_decisions_pretruth.sha256').write_text(p6_decisions_sha+'\n')
    summary={
        'source_p5_membership_sha256':EXPECTED_P5_MEMBERSHIP_SHA,
        'source_p5_decisions_sha256':EXPECTED_P5_DECISIONS_SHA,
        'source_crossfit_sha256':EXPECTED_CROSSFIT_SHA,
        'source_model_sha256':EXPECTED_MODEL_SHA,
        'family_count':EXPECTED_FAMILY_COUNT,
        'bidirectionally_reliable_families':len(eligible),
        'ineligible_families':len(ineligible),
        'ineligible_family_ids':ineligible,
        'dropped_assignments':len(set(dropped)),
        'retained_assignments':len(p6_assignments),
        'families_gaining_members':EXPECTED_P6_GAINING_FAMILIES,
        'membership_pretruth_sha256':p6_membership_sha,
        'decisions_pretruth_sha256':p6_decisions_sha,
        'known_shower_truth_accessed':False,
        'target_information_accessed':False,
    }
    (a.output/'p6_pretruth_transform.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps(summary,indent=2,sort_keys=True),flush=True)
    return 0

if __name__=='__main__':
    raise SystemExit(main())
