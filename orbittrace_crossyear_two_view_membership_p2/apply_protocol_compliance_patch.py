#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

EXPECTED_INPUT_SHA256 = "7637b6fb310ee3f24f1de8479a34d10c594dc55471eee55b8854e1c28787e8dd"

BEFORE_UNIVERSE = '''    valid_events_by_year = {
        year: [e for e in scan_by_year[year] if str(e["id"]) in orbit_by_id]
        for year in YEARS
    }
    valid_nonseed_by_year = {
        year: [e for e in valid_events_by_year[year] if str(e["id"]) not in global_seed_ids]
        for year in YEARS
    }
'''

AFTER_UNIVERSE = '''    # Protocol-compliance rule: the candidate/training universe is EVERY
    # target-excluded non-seed event. Orbit availability may not silently shrink
    # that universe; a missing orbit inside a required family window is an
    # explicit P2 input-ineligibility result.
    nonseed_by_year = {
        year: [e for e in scan_by_year[year] if str(e["id"]) not in global_seed_ids]
        for year in YEARS
    }
'''

BEFORE_WINDOW = '''            target_nonseed_events = valid_nonseed_by_year[target_year]
            mask = wrapped_window_mask(target_nonseed_events, target_center["sol"], base)
            negative_events = [event for event, keep in zip(target_nonseed_events, mask.tolist()) if keep]
            require(len(negative_events) >= MIN_DIRECTION_NEGATIVES, f"P2 input-ineligible: <{MIN_DIRECTION_NEGATIVES} negatives for {family_id} {source_year}->{target_year}")
            positive_events = rows_by_year[target_year]
'''

AFTER_WINDOW = '''            target_nonseed_events = nonseed_by_year[target_year]
            mask = wrapped_window_mask(target_nonseed_events, target_center["sol"], base)
            negative_events = [event for event, keep in zip(target_nonseed_events, mask.tolist()) if keep]
            require(len(negative_events) >= MIN_DIRECTION_NEGATIVES, f"P2 input-ineligible: <{MIN_DIRECTION_NEGATIVES} negatives for {family_id} {source_year}->{target_year}")
            missing_orbit_ids = [str(event["id"]) for event in negative_events if str(event["id"]) not in orbit_by_id]
            require(not missing_orbit_ids, f"P2 input-ineligible: required target-window nonseed lacks valid orbit for {family_id} {source_year}->{target_year}: count={len(missing_orbit_ids)}")
            positive_events = rows_by_year[target_year]
'''


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply_protocol_compliance_patch.py INPUT OUTPUT")
    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    raw = source.read_bytes()
    if digest(raw) != EXPECTED_INPUT_SHA256:
        raise RuntimeError(f"unexpected P2 input source SHA256: {digest(raw)}")
    text = raw.decode("utf-8")
    if text.count(BEFORE_UNIVERSE) != 1:
        raise RuntimeError("P2 universe patch anchor not unique")
    if text.count(BEFORE_WINDOW) != 1:
        raise RuntimeError("P2 window patch anchor not unique")
    patched = text.replace(BEFORE_UNIVERSE, AFTER_UNIVERSE, 1).replace(BEFORE_WINDOW, AFTER_WINDOW, 1)
    if patched.replace(AFTER_WINDOW, BEFORE_WINDOW, 1).replace(AFTER_UNIVERSE, BEFORE_UNIVERSE, 1) != text:
        raise RuntimeError("P2 compliance patch is not exactly reversible")
    output.write_text(patched, encoding="utf-8")
    print(f"P2_PROTOCOL_COMPLIANCE_PATCH_INPUT_SHA256={EXPECTED_INPUT_SHA256}")
    print(f"P2_PROTOCOL_COMPLIANCE_PATCH_OUTPUT_SHA256={digest(patched.encode('utf-8'))}")
    print("P2_PROTOCOL_COMPLIANCE_PATCH_SCOPE=required candidate universe only; no scientific parameter changed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
