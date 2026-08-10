#!/usr/bin/env python3
"""Pre-result strict-group adapter for #846.

The original #846 implementation correctly kept qualified-core shower groups intact, but
nonqualified near-miss hard fragments were assigned family-specific BG groups. That violates the
post-#840 standard requiring every fragment associated with the same known shower to stay in one
fold. This adapter changes only fold-group identity. Event correctness targets, features,
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
    qualified_target_by_family: dict[str, str | None] = {}

    for core in cores:
        fid = str(core["family_id"])

        # Preserve #846's original event-correctness target exactly for qualified cores.
        qualified_target, _purity, _overlap = module.family_target(hidden, core)
        qualified_target = None if qualified_target is None else str(qualified_target)
        qualified_target_by_family[fid] = qualified_target

        # For nonqualified near-miss fragments, recover only the best eligible shower association
        # for fold grouping. It is not used as an event-correctness target or model feature.
        if qualified_target is not None:
            association = qualified_target
        else:
            truth = v1.family_truth(core, hidden, eligible)
            best_label = truth.get("best_label")
            association = None if best_label is None else str(best_label)

        association_by_family[fid] = association
        group_by_family[fid] = association if association is not None else f"BG:{fid}"

    strict_groups: list[str] = []
    for eid in eids:
        fid = str(assignments[str(eid)]["family_id"])
        strict_groups.append(group_by_family[fid])

    if len(strict_groups) != len(eids):
        raise RuntimeError("strict-group row count changed")

    # Fail closed: each qualified #846 target identity must itself be the fold-group identity.
    for fid, target in qualified_target_by_family.items():
        if target is not None and group_by_family[fid] != target:
            raise RuntimeError(f"qualified target/group mismatch for {fid}: {target} vs {group_by_family[fid]}")

    # Fail closed: every fragment assigned to the same shower association maps to that one group.
    for label in sorted(set(x for x in association_by_family.values() if x is not None)):
        fids = [fid for fid, assoc in association_by_family.items() if assoc == label]
        groups = {group_by_family[fid] for fid in fids}
        if groups != {label}:
            raise RuntimeError(f"same-shower grouping failed for {label}: {groups}")

    meta = dict(meta)
    meta["strict_grouping_correction"] = {
        "rule": "qualified cores group by their unchanged #846 target identity; nonqualified near-misses group by best eligible shower association; all same-shower fragments share one fold group",
        "event_target_rule_unchanged": True,
        "qualified_target_groups": len(set(x for x in qualified_target_by_family.values() if x is not None)),
        "associated_shower_groups": len(set(x for x in association_by_family.values() if x is not None)),
        "background_family_groups": sum(x is None for x in association_by_family.values()),
    }
    return X, y, strict_groups, eids, meta


module.make_rows = strict_make_rows

if __name__ == "__main__":
    raise SystemExit(module.main())
