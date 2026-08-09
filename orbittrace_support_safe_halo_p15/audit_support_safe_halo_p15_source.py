#!/usr/bin/env python3
from __future__ import annotations

import difflib
import hashlib
import sys
from pathlib import Path

DEV_PARENT_SHA='78e93b5af19a441bc58b00428d2b356218b33f7a4a891a640dd59cb5d4599c32'
MATCHED_PARENT_SHA='55a1efed550498d51b859ffec555797ba8473d7d8b5f20ad6831c5f15b43b415'
DEV_CHILD_SHA='22d34131e873825ca60aefbba0b92088f19f57f589fe629bfbd3b7041d160b4b'
MATCHED_CHILD_SHA='23d309f6702ed0aa6769381963ea64701ae59c97376a0bae536b527fbc978fe6'

INIT_OLD='    direction_audits: list[dict[str, Any]] = []\n'
INIT_NEW=INIT_OLD+'    p15_unavailable_directions: list[dict[str, Any]] = []\n'
GUARD_OLD='            require(len(negative_events) >= MIN_DIRECTION_NEGATIVES, f"P2 input-ineligible: <{MIN_DIRECTION_NEGATIVES} negatives for {family_id} {source_year}->{target_year}")\n'
GUARD_NEW='''            if len(negative_events) < MIN_DIRECTION_NEGATIVES:
                p15_unavailable_directions.append({
                    "family_id": str(family_id),
                    "source_year": int(source_year),
                    "target_year": int(target_year),
                    "observed_negative_count": int(len(negative_events)),
                    "required_negative_count": int(MIN_DIRECTION_NEGATIVES),
                    "status": "CHARACTERIZATION_UNAVAILABLE_INSUFFICIENT_NEGATIVES",
                })
                continue
'''
EXPR='hashlib.sha256(json.dumps(p15_unavailable_directions, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()'
DEV_META_OLD='''    result = {
        "verdict": verdict,
'''
DEV_META_NEW=f'''    result = {{
        "verdict": verdict,
        "p15_architecture": "P15_SUPPORT_SAFE_SECONDARY_HALO_AVAILABILITY",
        "p15_parent_source_sha256": "{DEV_PARENT_SHA}",
        "p15_min_direction_negatives_unchanged": int(MIN_DIRECTION_NEGATIVES),
        "p15_unavailable_directions": p15_unavailable_directions,
        "p15_unavailable_direction_count": int(len(p15_unavailable_directions)),
        "p15_availability_sha256": {EXPR},
        "p15_no_padding_resampling_or_relaxation": True,
        "p15_secondary_characterization_only": True,
'''
MATCHED_META_OLD='''    halo_checkpoint = {
        "classification": "P13 exact-P12 matched-panel pretruth halo transport",
'''
MATCHED_META_NEW=f'''    halo_checkpoint = {{
        "classification": "P13 exact-P12 matched-panel pretruth halo transport",
        "p15_architecture": "P15_SUPPORT_SAFE_SECONDARY_HALO_AVAILABILITY",
        "p15_parent_source_sha256": "{MATCHED_PARENT_SHA}",
        "p15_min_direction_negatives_unchanged": int(MIN_DIRECTION_NEGATIVES),
        "p15_unavailable_directions": p15_unavailable_directions,
        "p15_unavailable_direction_count": int(len(p15_unavailable_directions)),
        "p15_availability_sha256": {EXPR},
        "p15_no_padding_resampling_or_relaxation": True,
        "p15_secondary_characterization_only": True,
'''


def sha(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(label:str,parent:Path,child:Path,parent_sha:str,child_sha:str,meta_old:str,meta_new:str)->None:
    if sha(parent)!=parent_sha: raise RuntimeError(f'{label} parent SHA changed: {sha(parent)}')
    if sha(child)!=child_sha: raise RuntimeError(f'{label} child SHA changed: {sha(child)}')
    old=parent.read_text(); new=child.read_text()
    for token in (INIT_OLD,GUARD_OLD,meta_old):
        if old.count(token)!=1: raise RuntimeError(f'{label} parent frozen anchor count {old.count(token)}')
    for token in (INIT_NEW,GUARD_NEW,meta_new):
        if new.count(token)!=1: raise RuntimeError(f'{label} child frozen anchor count {new.count(token)}')
    reverted=new.replace(INIT_NEW,INIT_OLD,1).replace(GUARD_NEW,GUARD_OLD,1).replace(meta_new,meta_old,1)
    if reverted!=old:
        raise RuntimeError(f'{label} P15 differs outside exactly three frozen source surfaces')
    if old.count('MIN_DIRECTION_NEGATIVES = 128')!=1 or new.count('MIN_DIRECTION_NEGATIVES = 128')!=1:
        raise RuntimeError(f'{label} exact 128-negative constant changed')
    if new.count('p15_unavailable_directions.append')!=1 or new.count('CHARACTERIZATION_UNAVAILABLE_INSUFFICIENT_NEGATIVES')!=1:
        raise RuntimeError(f'{label} P15 exception surface changed')
    for token in ('resample(','np.random','random.choice','MIN_DIRECTION_NEGATIVES = 64','MIN_DIRECTION_NEGATIVES = 32','OrbitTrace-April','target_coordinate'):
        if token in new: raise RuntimeError(f'{label} forbidden token present: {token}')
    delta='\n'.join(difflib.unified_diff(old.splitlines(),new.splitlines(),fromfile=f'{label}_PARENT',tofile=f'{label}_P15',lineterm=''))
    print(delta)
    print(f'PASS_P15_{label}_EXACT_THREE_SURFACE_REVERSE_EQUIVALENCE')


def main()->int:
    if len(sys.argv)!=5:
        raise SystemExit('usage: audit_support_safe_halo_p15_source.py DEV_PARENT DEV_CHILD MATCHED_PARENT MATCHED_CHILD')
    dp,dc,mp,mc=map(Path,sys.argv[1:])
    audit('DEV',dp,dc,DEV_PARENT_SHA,DEV_CHILD_SHA,DEV_META_OLD,DEV_META_NEW)
    audit('MATCHED',mp,mc,MATCHED_PARENT_SHA,MATCHED_CHILD_SHA,MATCHED_META_OLD,MATCHED_META_NEW)
    print('PASS_P15_SOURCE_TRANSFORM_EXACT_REVERSE_EQUIVALENCE')
    print('NO_COMPARATOR_ARTIFACT_NO_ARCHIVE_NO_TRUTH_NO_EXTERNAL_NO_TARGET_ACCESS')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
