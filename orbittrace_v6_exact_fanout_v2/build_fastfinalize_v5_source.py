#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

REPAIRED_V6_SHA256 = "257aab9d0f4d710a1b62af6088cfb9c0939062018d44dbacd074b4e7898eaa24"
START = "    proposal_cal, v3_cal, fixed4_cal, calibration_summary = calibrate_year_v6(\n"
END = "    primary_by_anchor: dict[str, dict[str, Any]] = {}\n"

REPLACEMENT = '''    # Execution-only fast-finalize v5. The immutable prefix was already run
    # once and hash-frozen before exact scoring. This block restores only those
    # exact prefix locals plus externally computed exact_records_all; from
    # primary_by_anchor onward the original repaired scientific source is byte-
    # for-byte unchanged.
    state = globals().get("_ORBITTRACE_FASTFINALIZE_STATE")
    if state is None:
        raise RuntimeError("fast-finalize state not installed")
    if int(state["year"]) != int(year):
        raise RuntimeError("fast-finalize year mismatch")
    proposal_cal = state["proposal_cal"]
    v3_cal = state["v3_cal"]
    fixed4_cal = state["fixed4_cal"]
    calibration_summary = state["calibration_summary"]
    event_lookup = {str(event["id"]): event for event in events}
    prefix_audit = state["prefix_audit"]
    proposal_cap = int(prefix_audit["proposal_cap_per_window"])
    if proposal_cap != old.MAX_COMPONENTS_PER_BIN * PROPOSALS_PER_WINDOW_FACTOR:
        raise RuntimeError("fast-finalize proposal cap mismatch")
    if int(prefix_audit["max_primary_proposals_per_year"]) != proposal_cap * int(360 / old.WINDOW_STEP_DEG):
        raise RuntimeError("fast-finalize annual proposal budget mismatch")
    prefilter_candidates = int(prefix_audit["prefilter_candidates"])
    proposal_scored = int(prefix_audit["proposal_candidates_scored"])
    primary_selected_total = int(prefix_audit["primary_proposals_selected_before_dedup"])
    rescue_selected_total = int(prefix_audit["rescue_proposals_selected_before_dedup"])
    window_count = int(prefix_audit["window_count"])
    unsupported_windows = int(prefix_audit["unsupported_windows"])
    centers = [float(index * old.WINDOW_STEP_DEG) for index in range(int(360 / old.WINDOW_STEP_DEG))]
    provisional = {
        str(record["proposal_anchor_id"]): record
        for record in state["provisional_records"]
    }
    if len(provisional) != int(prefix_audit["deduplicated_exact_proposals"]):
        raise RuntimeError("fast-finalize provisional count mismatch")
    exact_records_all = state["exact_records_all"]
    if len(exact_records_all) != len(provisional):
        raise RuntimeError("fast-finalize exact output cardinality mismatch")
'''


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: build_fastfinalize_v5_source.py REPAIRED_SOURCE OUTPUT")
    source = Path(sys.argv[1]); output = Path(sys.argv[2])
    raw = source.read_bytes()
    if digest(raw) != REPAIRED_V6_SHA256:
        raise RuntimeError(f"repaired source identity changed: {digest(raw)}")
    text = raw.decode("utf-8")
    if text.count(START) != 1 or text.count(END) != 1:
        raise RuntimeError("fast-finalize patch anchors not unique")
    start = text.index(START)
    end = text.index(END, start)
    if end <= start:
        raise RuntimeError("fast-finalize patch anchors reversed")
    removed = text[start:end]
    # The removed prefix must contain all expensive phases exactly once and end
    # immediately after exact-rescore collection. These are source-identity
    # guards, not alternative scientific definitions.
    for token in (
        "calibrate_year_v6(",
        "NearestNeighbors(",
        "candidate_from_indices(",
        "exact_rescore_window_v6(",
        "exact_records_all.extend(",
    ):
        if token not in removed:
            raise RuntimeError(f"expected immutable prefix token missing: {token}")
    if "primary_by_anchor" in removed:
        raise RuntimeError("scientific post-exact tail entered removed prefix")
    patched = text[:start] + REPLACEMENT + text[end:]
    # The entire scientific tail from primary_by_anchor to EOF is untouched.
    if patched[patched.index(END):] != text[end:]:
        raise RuntimeError("post-exact scientific tail changed")
    output.write_text(patched, encoding="utf-8")
    print(f"FASTFINALIZE_V5_REPAIRED_INPUT_SHA256={REPAIRED_V6_SHA256}")
    print(f"FASTFINALIZE_V5_REMOVED_PREFIX_SHA256={digest(removed.encode())}")
    print(f"FASTFINALIZE_V5_OUTPUT_SHA256={digest(patched.encode())}")
    print(f"FASTFINALIZE_V5_POSTEXACT_TAIL_SHA256={digest(text[end:].encode())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
