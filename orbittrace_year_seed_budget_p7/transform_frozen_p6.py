#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

EXPECTED_P6_MEMBERSHIP_SHA='40b0b720ef37427bc2d89aeb71c145683cbc69eff9b56ac5516e87fc34348ff6'
EXPECTED_P6_DECISIONS_SHA='5e76bbf2fd75acdf1d1bc770dc3c60de338a6388524c956544afe4c1aabc8490'
EXPECTED_FAMILY_COUNT=226
EXPECTED_P6_ASSIGNMENTS=21626
EXPECTED_P7_ASSIGNMENTS=4463
EXPECTED_DROPPED_ASSIGNMENTS=17163
EXPECTED_GAINING_FAMILIES=214
EXPECTED_BINDING_CELLS=283
EXPECTED_BINDING_FAMILIES=174
EXPECTED_P7_MEMBERSHIP_SHA='c68dcf21761cdad3048508902a7382039ea543df5b58a6b95a094c7c17f2db7a'
EXPECTED_P7_DECISIONS_SHA='4ffb9a4a4735788322825aaa24a1adee50ac7f5d13d0aba61c579d4b7b206ba5'
YEARS=(2022,2023)


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')


def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument('--p6-expanded-families',required=True,type=Path)
    p.add_argument('--p6-membership-sha',required=True,type=Path)
    p.add_argument('--p6-decisions',required=True,type=Path)
    p.add_argument('--p6-decisions-sha',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)

    require(a.p6_membership_sha.read_text().strip()==EXPECTED_P6_MEMBERSHIP_SHA,'P6 stored membership SHA changed')
    require(a.p6_decisions_sha.read_text().strip()==EXPECTED_P6_DECISIONS_SHA,'P6 stored decisions SHA changed')
    p6_raw=gzip.decompress(a.p6_expanded_families.read_bytes())
    require(hashlib.sha256(p6_raw).hexdigest()==EXPECTED_P6_MEMBERSHIP_SHA,'P6 expanded membership payload changed')
    p6_families=json.loads(p6_raw)
    require(len(p6_families)==EXPECTED_FAMILY_COUNT,'P6 family count changed')

    d_raw=gzip.decompress(a.p6_decisions.read_bytes())
    require(hashlib.sha256(d_raw).hexdigest()==EXPECTED_P6_DECISIONS_SHA,'P6 decisions payload changed')
    p6_decisions=json.loads(d_raw)
    assignments=p6_decisions['assignments']
    require(len(assignments)==EXPECTED_P6_ASSIGNMENTS,'P6 assignment count changed')

    by_family_year: dict[tuple[str,int],list[tuple[str,dict[str,Any]]]]=defaultdict(list)
    for eid,rec in assignments.items():
        fid=str(rec['family_id']); year=int(rec['target_year'])
        require(year in YEARS,f'P6 assignment target year changed: {year}')
        by_family_year[(fid,year)].append((str(eid),rec))

    keep_ids:set[str]=set()
    family_year_budgets:dict[str,dict[str,dict[str,int]]]={}
    binding_cells=0; binding_families:set[str]=set()
    seed_ids_by_family:dict[str,set[str]]={}

    for family in p6_families:
        fid=str(family['family_id'])
        additions=set(map(str,family.get('p2_added_event_ids',[])))
        members=set(map(str,family['event_ids']))
        require(additions<=members,f'P6 addition outside family {fid}')
        seeds=members-additions
        require(bool(seeds),f'empty immutable seed set {fid}')
        seed_ids_by_family[fid]=seeds
        seed_by_year=Counter(int(eid[:4]) for eid in seeds)
        require(set(seed_by_year)<=set(YEARS),f'immutable seed year changed for {fid}: {seed_by_year}')
        family_year_budgets[fid]={}
        for year in YEARS:
            rows=list(by_family_year.get((fid,year),[]))
            rows.sort(key=lambda item:(-float(item[1]['responsibility']),-float(item[1]['probability']),item[0]))
            budget=int(seed_by_year.get(year,0))
            if len(rows)>budget:
                binding_cells+=1; binding_families.add(fid)
            selected=rows[:budget]
            keep_ids.update(eid for eid,_ in selected)
            family_year_budgets[fid][str(year)]={
                'immutable_seed_count':budget,
                'p6_assignment_count':len(rows),
                'retained_addition_count':len(selected),
            }

    require(binding_cells==EXPECTED_BINDING_CELLS,f'binding-cell count changed: {binding_cells}')
    require(len(binding_families)==EXPECTED_BINDING_FAMILIES,f'binding-family count changed: {len(binding_families)}')
    require(len(keep_ids)==EXPECTED_P7_ASSIGNMENTS,f'P7 retained-assignment count changed: {len(keep_ids)}')
    require(len(set(assignments)-keep_ids)==EXPECTED_DROPPED_ASSIGNMENTS,'P7 dropped-assignment count changed')

    p7_families=[]
    for family in p6_families:
        row=json.loads(json.dumps(family))
        fid=str(row['family_id'])
        p6_additions=set(map(str,row.get('p2_added_event_ids',[])))
        seeds=seed_ids_by_family[fid]
        kept=p6_additions & keep_ids
        row['p2_added_event_ids']=sorted(kept)
        row['p2_added_event_count']=len(kept)
        row['event_ids']=sorted(seeds|kept)
        row['event_count']=len(row['event_ids'])
        p7_families.append(row)
    require(sum(int(f['p2_added_event_count']) for f in p7_families)==EXPECTED_P7_ASSIGNMENTS,'P7 family addition count changed')
    require(sum(bool(f['p2_added_event_count']) for f in p7_families)==EXPECTED_GAINING_FAMILIES,'P7 gaining-family count changed')

    p7_raw=canonical_bytes(p7_families)
    membership_sha=hashlib.sha256(p7_raw).hexdigest()
    require(membership_sha==EXPECTED_P7_MEMBERSHIP_SHA,f'P7 membership SHA changed: {membership_sha}')

    retained={eid:assignments[eid] for eid in sorted(keep_ids)}
    decision_payload={
        'source_p6_decisions_sha256':EXPECTED_P6_DECISIONS_SHA,
        'selection_rule':'within each family and target year retain at most immutable v8 seed count; rank by responsibility desc, probability desc, event_id asc',
        'family_year_budgets':{
            fid:{
                'immutable_seed_count_by_year':{y:int(rec[y]['immutable_seed_count']) for y in map(str,YEARS)},
                'retained_addition_count_by_year':{y:int(rec[y]['retained_addition_count']) for y in map(str,YEARS)},
            }
            for fid,rec in family_year_budgets.items()
        },
        'dropped_assignment_event_ids':sorted(set(assignments)-keep_ids),
        'assignments':retained,
    }
    decision_raw=canonical_bytes(decision_payload)
    decisions_sha=hashlib.sha256(decision_raw).hexdigest()
    require(decisions_sha==EXPECTED_P7_DECISIONS_SHA,f'P7 decisions SHA changed: {decisions_sha}')

    # Explicitly enforce the per-year evidence budget in the final retained payload.
    retained_counts=Counter((str(rec['family_id']),int(rec['target_year'])) for rec in retained.values())
    for fid,rec in family_year_budgets.items():
        for year in YEARS:
            require(retained_counts.get((fid,year),0)<=int(rec[str(year)]['immutable_seed_count']),f'P7 evidence budget exceeded: {fid} {year}')

    (a.output/'p7_expanded_families.json.gz').write_bytes(gzip.compress(p7_raw))
    (a.output/'p7_membership_pretruth.sha256').write_text(membership_sha+'\n')
    (a.output/'p7_decisions_pretruth.json.gz').write_bytes(gzip.compress(decision_raw))
    (a.output/'p7_decisions_pretruth.sha256').write_text(decisions_sha+'\n')
    summary={
        'source_p6_membership_sha256':EXPECTED_P6_MEMBERSHIP_SHA,
        'source_p6_decisions_sha256':EXPECTED_P6_DECISIONS_SHA,
        'family_count':EXPECTED_FAMILY_COUNT,
        'p6_assignments':EXPECTED_P6_ASSIGNMENTS,
        'retained_assignments':EXPECTED_P7_ASSIGNMENTS,
        'dropped_assignments':EXPECTED_DROPPED_ASSIGNMENTS,
        'families_gaining_members':EXPECTED_GAINING_FAMILIES,
        'budget_binding_family_year_cells':binding_cells,
        'budget_binding_families':len(binding_families),
        'membership_pretruth_sha256':membership_sha,
        'decisions_pretruth_sha256':decisions_sha,
        'known_shower_truth_accessed':False,
        'target_information_accessed':False,
    }
    (a.output/'p7_pretruth_transform.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps(summary,indent=2,sort_keys=True),flush=True)
    return 0

if __name__=='__main__':
    raise SystemExit(main())
