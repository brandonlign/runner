#!/usr/bin/env python3
"""Pre-result strict-group adapter for #846.

The original #846 implementation correctly kept qualified-core shower groups intact, but
nonqualified near-miss hard fragments were assigned family-specific BG groups. That violates the
post-#840 standard requiring every fragment associated with the same best known shower to stay in
one fold. This adapter changes only fold-group identity. Event correctness targets, features,
models, weights, thresholds, caps, gates, data, and target firewall remain exactly #846.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

from orbittrace_unified_recurrent_catalogue_lab_v1 import run_lab as v1

SOURCE = Path(__file__).with_name("run_lab.py")
spec = importlib.util.spec_from_file_location("orbittrace_event_membership_calibration_base", SOURCE)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot import {SOURCE}")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

_original_make_rows = module.make_rows


def strict_make_rows(
    hidden: dict[str, str],
    cores: list[dict[str, Any]],
    expanded: list[dict[str, Any]],
    assignments: dict[str, dict[str, Any]],
):
    X, y, _old_groups, eids, meta = _original_make_rows(hidden, cores, expanded, assignments)

    eligible = v1.eligible_labels(hidden)
    group_by_family: dict[str, str] = {}
    association_by_family: dict[str, str | None] = {}
    for core in cores:
        fid = str(core["family_id"])
        truth = v1.family_truth(core, hidden, eligible)
        best_label = truth.get("best_label")
        association_by_family[fid] = None if best_label is None else str(best_label)
        group_by_family[fid] = str(best_label) if best_label is not None else f"BG:{fid}"

    strict_groups: list[str] = []
    for eid in eids:
        fid = str(assignments[str(eid)]["family_id"])
        strict_groups.append(group_by_family[fid])

    if len(strict_groups) != len(eids):
        raise RuntimeError("strict-group row count changed")

    # Fail closed: every family sharing an eligible best-known shower must map to one group.
    for label in sorted(set(x for x in association_by_family.values() if x is not None)):
        fids = [fid for fid, assoc in association_by_family.items() if assoc == label]
        groups = {group_by_family[fid] for fid in fids}
        if groups != {label}:
            raise RuntimeError(f"same-shower grouping failed for {label}: {groups}")

    meta = dict(meta)
    meta["strict_grouping_correction"] = {
        "rule": "all hard fragments with the same best eligible known-shower association share one fold group, including nonqualified near-misses",
        "event_target_rule_unchanged": True,
        "associated_shower_groups": len(set(x for x in association_by_family.values() if x is not None)),
        "background_family_groups": sum(x is None for x in association_by_family.values()),
    }
    return X, y, strict_groups, eids, meta


module.make_rows = strict_make_rows

if __name__ == "__main__":
    raise SystemExit(module.main())
