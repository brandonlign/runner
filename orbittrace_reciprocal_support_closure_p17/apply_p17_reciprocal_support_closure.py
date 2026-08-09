#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

P15_DEV_SHA='22d34131e873825ca60aefbba0b92088f19f57f589fe629bfbd3b7041d160b4b'
P15_MATCHED_SHA='23d309f6702ed0aa6769381963ea64701ae59c97376a0bae536b527fbc978fe6'

OLD_COUNT='''    for family_id in family_order:
        require(sum(1 for drec in direction_records if drec["family_id"] == family_id) == 2, f"family {family_id} missing reciprocal direction record")
'''
NEW_COUNT='''    for family_id in family_order:
        p17_record_count = sum(1 for drec in direction_records if drec["family_id"] == family_id)
        p17_unavailable_count = sum(1 for item in p15_unavailable_directions if item["family_id"] == family_id)
        require(p17_record_count + p17_unavailable_count == 2, f"family {family_id} reciprocal direction accounting changed")
        require(p17_record_count in {1, 2}, f"family {family_id} has no support-eligible characterization direction")
        require(p17_unavailable_count in {0, 1}, f"family {family_id} unexpected unavailable-direction multiplicity")
'''

OLD_RECIP='''        reciprocal = next(
            (a for a in crossfit_audits if a["family_id"] == family_id and a["source_year"] == target_year and a["target_year"] == source_year),
            None,
        )
        require(reciprocal is not None, f"missing reciprocal reliability for {family_id} {source_year}->{target_year}")
        p9_reliable = bool(direction_reliable and bool(reciprocal["p3_reliable"]))
'''
NEW_RECIP='''        reciprocal = next(
            (a for a in crossfit_audits if a["family_id"] == family_id and a["source_year"] == target_year and a["target_year"] == source_year),
            None,
        )
        p17_reciprocal_unavailable = any(
            item["family_id"] == family_id
            and int(item["source_year"]) == target_year
            and int(item["target_year"]) == source_year
            and item["status"] == "CHARACTERIZATION_UNAVAILABLE_INSUFFICIENT_NEGATIVES"
            for item in p15_unavailable_directions
        )
        if reciprocal is None:
            require(p17_reciprocal_unavailable, f"missing reciprocal reliability without support-unavailable proof for {family_id} {source_year}->{target_year}")
            p17_reciprocal_p3_reliable = False
        else:
            require(not p17_reciprocal_unavailable, f"reciprocal direction both modeled and unavailable for {family_id} {source_year}->{target_year}")
            p17_reciprocal_p3_reliable = bool(reciprocal["p3_reliable"])
        p9_reliable = bool(direction_reliable and p17_reciprocal_p3_reliable)
'''

OLD_AUDIT='''                "p9_reliable": bool(p9_reliable),
                "p10_floor_consistent_geometry": bool(p10_floor_consistent_geometry),
'''
NEW_AUDIT='''                "p9_reliable": bool(p9_reliable),
                "p17_reciprocal_reliability_available": bool(reciprocal is not None),
                "p17_reciprocal_direction_unavailable": bool(p17_reciprocal_unavailable),
                "p17_reciprocal_fail_closed": bool(reciprocal is None and p17_reciprocal_unavailable and not p9_reliable),
                "p10_floor_consistent_geometry": bool(p10_floor_consistent_geometry),
'''

RESULT_ANCHOR='''    result = {
'''
RESULT_LEDGER='''    p17_reciprocal_closures = sorted(
        [
            {
                "family_id": str(a["family_id"]),
                "source_year": int(a["source_year"]),
                "target_year": int(a["target_year"]),
                "reciprocal_reliability_available": bool(a["p17_reciprocal_reliability_available"]),
                "reciprocal_direction_unavailable": bool(a["p17_reciprocal_direction_unavailable"]),
                "p9_reliable": bool(a["p9_reliable"]),
                "proposal_count": int(a["proposal_count"]),
            }
            for a in candidate_audits
            if a.get("p17_reciprocal_direction_unavailable") is True
        ],
        key=lambda a: (a["family_id"], a["source_year"], a["target_year"]),
    )
    require(all(x["reciprocal_reliability_available"] is False for x in p17_reciprocal_closures), "P17 closure unexpectedly has reciprocal reliability")
    require(all(x["p9_reliable"] is False and x["proposal_count"] == 0 for x in p17_reciprocal_closures), "P17 closure contributed a proposal")
    p17_reciprocal_closure_sha256 = hashlib.sha256(
        json.dumps(p17_reciprocal_closures, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()

    result = {
'''

RESULT_FIELDS='''        "p15_availability_sha256": p15_availability_sha256,
'''
RESULT_FIELDS_NEW='''        "p15_availability_sha256": p15_availability_sha256,
        "p17_architecture": "P17_FAIL_CLOSED_RECIPROCAL_SUPPORT_CLOSURE",
        "p17_bidirectional_reliability_threshold_changed": False,
        "p17_missing_reciprocal_creates_positive_evidence": False,
        "p17_reciprocal_closures": p17_reciprocal_closures,
        "p17_reciprocal_closure_count": len(p17_reciprocal_closures),
        "p17_reciprocal_closure_sha256": p17_reciprocal_closure_sha256,
'''

HALO_FIELDS='''        "p15_availability_sha256": p15_availability_sha256,
        "core_families": families,
'''
HALO_FIELDS_NEW='''        "p15_availability_sha256": p15_availability_sha256,
        "p17_architecture": "P17_FAIL_CLOSED_RECIPROCAL_SUPPORT_CLOSURE",
        "p17_bidirectional_reliability_threshold_changed": False,
        "p17_missing_reciprocal_creates_positive_evidence": False,
        "p17_reciprocal_closures": p17_reciprocal_closures,
        "p17_reciprocal_closure_count": len(p17_reciprocal_closures),
        "p17_reciprocal_closure_sha256": p17_reciprocal_closure_sha256,
        "core_families": families,
'''


def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()


def once(text:str,old:str,new:str,label:str)->str:
    n=text.count(old)
    if n!=1: raise RuntimeError(f'P17 anchor {label} count={n}')
    return text.replace(old,new,1)


def main()->int:
    if len(sys.argv)!=3: raise SystemExit('usage: apply_p17_reciprocal_support_closure.py P15_SOURCE OUTPUT')
    source,output=map(Path,sys.argv[1:]); raw=source.read_bytes(); digest=sha(raw)
    if digest not in {P15_DEV_SHA,P15_MATCHED_SHA}: raise RuntimeError(f'unexpected P15 parent SHA: {digest}')
    text=raw.decode()
    text=once(text,OLD_COUNT,NEW_COUNT,'reciprocal direction accounting')
    text=once(text,OLD_RECIP,NEW_RECIP,'fail-closed reciprocal P9 reliability')
    text=once(text,OLD_AUDIT,NEW_AUDIT,'candidate closure audit')
    text=once(text,RESULT_ANCHOR,RESULT_LEDGER,'closure ledger')
    text=once(text,RESULT_FIELDS,RESULT_FIELDS_NEW,'result closure provenance')
    text=once(text,HALO_FIELDS,HALO_FIELDS_NEW,'halo checkpoint closure provenance')
    if text.count('MIN_DIRECTION_NEGATIVES = 128')!=1: raise RuntimeError('P17 changed immutable 128-negative threshold')
    if 'p17_reciprocal_p3_reliable = True' in text: raise RuntimeError('P17 fabricates reciprocal positive reliability')
    for token in ('OrbitTrace-April','target_coordinate'):
        if token in text: raise RuntimeError(f'forbidden target token present: {token}')
    output.write_text(text)
    print(f'P17_PARENT_SHA256={digest}')
    print(f'P17_OUTPUT_SHA256={sha(text.encode())}')
    print('P17_SCOPE=represent P15-unavailable reciprocal explicitly; missing reciprocal reliability is fail-closed false; no P12 threshold/model/geometry/rank change')
    return 0


if __name__=='__main__': raise SystemExit(main())
