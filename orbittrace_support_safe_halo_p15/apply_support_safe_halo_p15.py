#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

DEV_PARENT_SHA256='78e93b5af19a441bc58b00428d2b356218b33f7a4a891a640dd59cb5d4599c32'
MATCHED_PARENT_SHA256='55a1efed550498d51b859ffec555797ba8473d7d8b5f20ad6831c5f15b43b415'
DEV_P15_SHA256='22d34131e873825ca60aefbba0b92088f19f57f589fe629bfbd3b7041d160b4b'
MATCHED_P15_SHA256='23d309f6702ed0aa6769381963ea64701ae59c97376a0bae536b527fbc978fe6'
P15_RULE='P15_SUPPORT_SAFE_SECONDARY_HALO_AVAILABILITY'


def sha256(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()


def once(text:str,old:str,new:str,label:str)->str:
    n=text.count(old)
    if n!=1:
        raise RuntimeError(f'P15 anchor {label} count={n}')
    return text.replace(old,new,1)


def main()->int:
    if len(sys.argv)!=3:
        raise SystemExit('usage: apply_support_safe_halo_p15.py P12_PARENT OUTPUT')
    src,out=map(Path,sys.argv[1:])
    raw=src.read_bytes(); parent=sha256(raw)
    if parent not in {DEV_PARENT_SHA256,MATCHED_PARENT_SHA256}:
        raise RuntimeError(f'P15 unsupported parent source SHA: {parent}')
    text=raw.decode('utf-8')

    init_old='    direction_audits: list[dict[str, Any]] = []\n'
    init_new=init_old+'    p15_unavailable_directions: list[dict[str, Any]] = []\n'
    text=once(text,init_old,init_new,'availability ledger initialization')

    guard_old='            require(len(negative_events) >= MIN_DIRECTION_NEGATIVES, f"P2 input-ineligible: <{MIN_DIRECTION_NEGATIVES} negatives for {family_id} {source_year}->{target_year}")\n'
    guard_new='''            if len(negative_events) < MIN_DIRECTION_NEGATIVES:
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
    text=once(text,guard_old,guard_new,'exact negative-support availability rule')

    availability_expr='hashlib.sha256(json.dumps(p15_unavailable_directions, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()'
    if parent==DEV_PARENT_SHA256:
        result_old='''    result = {
        "verdict": verdict,
'''
        result_new=f'''    result = {{
        "verdict": verdict,
        "p15_architecture": "{P15_RULE}",
        "p15_parent_source_sha256": "{DEV_PARENT_SHA256}",
        "p15_min_direction_negatives_unchanged": int(MIN_DIRECTION_NEGATIVES),
        "p15_unavailable_directions": p15_unavailable_directions,
        "p15_unavailable_direction_count": int(len(p15_unavailable_directions)),
        "p15_availability_sha256": {availability_expr},
        "p15_no_padding_resampling_or_relaxation": True,
        "p15_secondary_characterization_only": True,
'''
        text=once(text,result_old,result_new,'development result metadata')
        expected=DEV_P15_SHA256
    else:
        checkpoint_old='''    halo_checkpoint = {
        "classification": "P13 exact-P12 matched-panel pretruth halo transport",
'''
        checkpoint_new=f'''    halo_checkpoint = {{
        "classification": "P13 exact-P12 matched-panel pretruth halo transport",
        "p15_architecture": "{P15_RULE}",
        "p15_parent_source_sha256": "{MATCHED_PARENT_SHA256}",
        "p15_min_direction_negatives_unchanged": int(MIN_DIRECTION_NEGATIVES),
        "p15_unavailable_directions": p15_unavailable_directions,
        "p15_unavailable_direction_count": int(len(p15_unavailable_directions)),
        "p15_availability_sha256": {availability_expr},
        "p15_no_padding_resampling_or_relaxation": True,
        "p15_secondary_characterization_only": True,
'''
        text=once(text,checkpoint_old,checkpoint_new,'matched halo checkpoint metadata')
        expected=MATCHED_P15_SHA256

    if 'MIN_DIRECTION_NEGATIVES = 128' not in text:
        raise RuntimeError('P15 exact 128-negative constant changed or unavailable')
    if 'CHARACTERIZATION_UNAVAILABLE_INSUFFICIENT_NEGATIVES' not in text:
        raise RuntimeError('P15 availability status missing')
    if text.count('p15_unavailable_directions.append')!=1:
        raise RuntimeError('P15 unavailable-direction exception surface is not unique')
    forbidden=('OrbitTrace-April','target_coordinate','resample(','np.random','random.choice','MIN_DIRECTION_NEGATIVES = 64','MIN_DIRECTION_NEGATIVES = 32')
    for token in forbidden:
        if token in text:
            raise RuntimeError(f'P15 forbidden token/source change present: {token}')

    result=sha256(text.encode('utf-8'))
    if result!=expected:
        raise RuntimeError(f'P15 generated source SHA changed: expected={expected} actual={result}')
    out.write_text(text,encoding='utf-8')
    print(f'P15_INPUT_SHA256={parent}')
    print(f'P15_OUTPUT_SHA256={result}')
    print('P15_SCOPE=secondary halo availability only; exact 128-negative requirement unchanged; insufficient directions add zero proposals; all eligible P12 science unchanged')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
