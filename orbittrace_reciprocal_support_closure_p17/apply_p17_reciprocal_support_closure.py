#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

P15_DEV_SHA='22d34131e873825ca60aefbba0b92088f19f57f589fe629bfbd3b7041d160b4b'
P15_MATCHED_SHA='23d309f6702ed0aa6769381963ea64701ae59c97376a0bae536b527fbc978fe6'
P17_RULE='P17_FAIL_CLOSED_RECIPROCAL_SUPPORT_CLOSURE'

OLD_COUNT='''    require(all(sum(1 for d in directions if str(d["family_id"]) == fid) == 2 for fid in family_fold), "P3 family direction count changed")
'''
NEW_COUNT='''    for family_id in family_fold:
        p17_record_count = sum(1 for d in directions if str(d["family_id"]) == family_id)
        p17_unavailable_count = sum(1 for item in p15_unavailable_directions if item["family_id"] == family_id)
        require(p17_record_count + p17_unavailable_count == 2, f"family {family_id} reciprocal direction accounting changed")
        require(p17_record_count in {1, 2}, f"family {family_id} has no support-eligible characterization direction")
        require(p17_unavailable_count in {0, 1}, f"family {family_id} unexpected unavailable-direction multiplicity")
'''

LEDGER_INIT_OLD='''    proposals_by_event: dict[str, list[dict[str, Any]]] = defaultdict(list)
    eps = np.finfo(np.float64).eps
'''
LEDGER_INIT_NEW='''    proposals_by_event: dict[str, list[dict[str, Any]]] = defaultdict(list)
    p17_reciprocal_closures: list[dict[str, Any]] = []
    eps = np.finfo(np.float64).eps
'''

OLD_RECIP='''        reciprocal_key = f"{direction['family_id']}|{direction['target_year']}|{direction['source_year']}"
        require(reciprocal_key in reliability, f"P9 missing reciprocal reliability key {reciprocal_key}")
        reciprocal_gate = reliability[reciprocal_key]
        scoring_fold = int(gate["fold"])
'''
NEW_RECIP='''        reciprocal_key = f"{direction['family_id']}|{direction['target_year']}|{direction['source_year']}"
        reciprocal_gate = reliability.get(reciprocal_key)
        p17_reciprocal_unavailable = any(
            item["family_id"] == str(direction["family_id"])
            and int(item["source_year"]) == int(direction["target_year"])
            and int(item["target_year"]) == int(direction["source_year"])
            and item["status"] == "CHARACTERIZATION_UNAVAILABLE_INSUFFICIENT_NEGATIVES"
            for item in p15_unavailable_directions
        )
        if reciprocal_gate is None:
            require(p17_reciprocal_unavailable, f"missing reciprocal reliability without support-unavailable proof for {reciprocal_key}")
            p17_reciprocal_p3_reliable = False
            p17_reciprocal_closures.append({
                "family_id": str(direction["family_id"]),
                "source_year": int(direction["source_year"]),
                "target_year": int(direction["target_year"]),
                "missing_reciprocal_source_year": int(direction["target_year"]),
                "missing_reciprocal_target_year": int(direction["source_year"]),
                "reciprocal_reliability_available": False,
                "reciprocal_direction_unavailable": True,
                "p17_reciprocal_fail_closed": True,
                "p9_reliable": False,
                "proposal_count": 0,
            })
        else:
            require(not p17_reciprocal_unavailable, f"reciprocal direction both modeled and unavailable for {reciprocal_key}")
            p17_reciprocal_p3_reliable = bool(reciprocal_gate["reliable"])
        scoring_fold = int(gate["fold"])
'''

OLD_VETO='''        if not (bool(gate["reliable"]) and bool(reciprocal_gate["reliable"])):
'''
NEW_VETO='''        direction_reliable = bool(gate["reliable"])
        p9_reliable = bool(direction_reliable and p17_reciprocal_p3_reliable)
        if not p9_reliable:
'''

DEV_LEDGER_ANCHOR='''    result = {
'''
MATCHED_LEDGER_ANCHOR='''    halo_checkpoint = {
'''
LEDGER_CODE='''    p17_reciprocal_closures = sorted(
        p17_reciprocal_closures,
        key=lambda x: (x["family_id"], x["source_year"], x["target_year"]),
    )
    require(len(p17_reciprocal_closures) == len(p15_unavailable_directions), "P17 reciprocal closure coverage changed")
    require(all(x["reciprocal_reliability_available"] is False and x["reciprocal_direction_unavailable"] is True for x in p17_reciprocal_closures), "P17 closure availability semantics changed")
    require(all(x["p17_reciprocal_fail_closed"] is True and x["p9_reliable"] is False and x["proposal_count"] == 0 for x in p17_reciprocal_closures), "P17 closure contributed positive evidence")
    p17_reciprocal_closure_sha256 = hashlib.sha256(
        json.dumps(p17_reciprocal_closures, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()

'''

FIELDS_OLD='''        "p15_secondary_characterization_only": True,
'''
FIELDS_NEW='''        "p15_secondary_characterization_only": True,
        "p17_architecture": "P17_FAIL_CLOSED_RECIPROCAL_SUPPORT_CLOSURE",
        "p17_bidirectional_reliability_threshold_changed": False,
        "p17_missing_reciprocal_creates_positive_evidence": False,
        "p17_reciprocal_closures": p17_reciprocal_closures,
        "p17_reciprocal_closure_count": len(p17_reciprocal_closures),
        "p17_reciprocal_closure_sha256": p17_reciprocal_closure_sha256,
'''


def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()


def once(text:str,old:str,new:str,label:str)->str:
    n=text.count(old)
    if n!=1:
        raise RuntimeError(f'P17 anchor {label} count={n}')
    return text.replace(old,new,1)


def main()->int:
    if len(sys.argv)!=3:
        raise SystemExit('usage: apply_p17_reciprocal_support_closure.py P15_SOURCE OUTPUT')
    source,output=map(Path,sys.argv[1:])
    raw=source.read_bytes(); digest=sha(raw)
    if digest not in {P15_DEV_SHA,P15_MATCHED_SHA}:
        raise RuntimeError(f'unexpected P15 parent SHA: {digest}')
    text=raw.decode('utf-8')
    text=once(text,OLD_COUNT,NEW_COUNT,'P3 reciprocal direction accounting')
    text=once(text,LEDGER_INIT_OLD,LEDGER_INIT_NEW,'P17 closure ledger initialization')
    text=once(text,OLD_RECIP,NEW_RECIP,'fail-closed reciprocal P9 lookup')
    text=once(text,OLD_VETO,NEW_VETO,'exact P9 bidirectional veto')
    if digest==P15_DEV_SHA:
        text=once(text,DEV_LEDGER_ANCHOR,LEDGER_CODE+DEV_LEDGER_ANCHOR,'development closure ledger freeze')
    else:
        text=once(text,MATCHED_LEDGER_ANCHOR,LEDGER_CODE+MATCHED_LEDGER_ANCHOR,'matched closure ledger freeze')
    text=once(text,FIELDS_OLD,FIELDS_NEW,'P17 closure provenance')

    if text.count('MIN_DIRECTION_NEGATIVES = 128')!=1:
        raise RuntimeError('P17 changed immutable 128-negative threshold')
    if 'p17_reciprocal_p3_reliable = True' in text:
        raise RuntimeError('P17 fabricates reciprocal positive reliability')
    if text.count('p9_reliable = bool(direction_reliable and p17_reciprocal_p3_reliable)')!=1:
        raise RuntimeError('P17 exact P9 fail-closed conjunction missing')
    if text.count('len(p17_reciprocal_closures) == len(p15_unavailable_directions)')!=1:
        raise RuntimeError('P17 closure coverage invariant missing')
    for token in ('OrbitTrace-April','target_coordinate'):
        if token in text:
            raise RuntimeError(f'forbidden target token present: {token}')
    output.write_text(text,encoding='utf-8')
    print(f'P17_PARENT_SHA256={digest}')
    print(f'P17_OUTPUT_SHA256={sha(text.encode("utf-8"))}')
    print('P17_SCOPE=represent P15-unavailable reciprocal explicitly; missing reciprocal reliability is fail-closed false; no P12 threshold/model/geometry/rank/proposal change')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
