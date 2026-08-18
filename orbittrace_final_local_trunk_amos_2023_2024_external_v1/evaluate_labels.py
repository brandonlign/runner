#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

YEARS = (2023, 2024)
BLIND = (20.0, 55.0)
SCIENTIFIC_ROLE = "PRISTINE_FINAL_EXTERNAL_AMOS_2023_2024_TEST_ONLY"
SELECTED_FINAL_METHOD = "recurrent_local_topomodal_trunk_v1_over_density_sync_parent"
PRIMARY_PASS = "PASS_RECURRENT_LOCAL_TOPOMODAL_TRUNK_V1_AMOS_2023_2024_FINAL_EXTERNAL_VALIDATION"
PRIMARY_FAIL = "FAIL_RECURRENT_LOCAL_TOPOMODAL_TRUNK_V1_AMOS_2023_2024_FINAL_EXTERNAL_VALIDATION"
INCREMENT_PASS = "PASS_LOCAL_TOPOMODAL_TRUNK_INCREMENT_AMOS"
INCREMENT_NO = "NO_DEMONSTRATED_LOCAL_TOPOMODAL_TRUNK_INCREMENT_AMOS"

# Exact inherited evaluators. The parent AMOS evaluator supplies the hardened
# pretruth/label transport checks; the local-trunk GMN evaluator supplies the
# zero-filled eligible-query MRR and membership-retrieval metric semantics.
PARENT_AMOS_EVALUATOR_BLOB = "c45e4739ea68639945b13de54f6e24dc9d870ba3"
LOCAL_TRUNK_GMN_EVALUATOR_BLOB = "749a527b7a9ee3c5f1a70832669d83fa1af592d7"
LOCAL_TRUNK_PROTOCOL_BLOB = "de8d040a1f9d3b0825ce56532efd5950acefc689"
LOCAL_TRUNK_CONSTRUCTOR_BLOB = "cd3fb15263fd4b2e38e4b413ece9b347b64816d5"
LOCAL_TRUNK_LAZY_TRANSPORT_BLOB = "79cc2e51929fd60f8e17faec4c1b04c19e43010e"
LOCAL_TRUNK_EXACT_ROW_TRANSPORT_BLOB = "81e4833ac24bb90fe810b0444da534906b10e798"
LOCAL_TRUNK_SOURCE_COMMIT = "3afb4bd1de98d9c765dcaff79b9e98a0cc1234a4"

LOCAL_EXTRA_KEYS = {
    "schema",
    "density_sync_parent_pretruth_sha256",
    "density_sync_parent_candidates",
    "local_trunk_candidates",
    "local_trunk_diagnostics",
    "local_trunk_changed_slot_count",
    "local_trunk_mechanism_active",
    "local_trunk_parent_ordered_membership_sha256",
    "local_trunk_final_ordered_membership_sha256",
    "local_trunk_source_commit",
    "local_trunk_source_pins",
    "local_trunk_transfer",
    "new_external_survey_hunt",
}


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def membership_sha(ids: list[str] | tuple[str, ...]) -> str:
    return hashlib.sha256("|".join(sorted(str(x) for x in ids)).encode()).hexdigest()


def ordered_membership_sha(candidates: list[dict[str, Any]]) -> str:
    text = "\n".join("|".join(str(x) for x in row["event_ids"]) for row in candidates)
    return hashlib.sha256(text.encode()).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def compare_no_regression(parent: dict[str, Any], final: dict[str, Any]) -> dict[str, bool]:
    return {
        "qualified_recovery_not_lower": int(final["qualified_matches"]) >= int(parent["qualified_matches"]),
        "recovered_at_50_not_lower": int(final["recovered_at_50"]) >= int(parent["recovered_at_50"]),
        "recovered_at_100_not_lower": int(final["recovered_at_100"]) >= int(parent["recovered_at_100"]),
        "top100_precision_not_lower": float(final["top100_dominant_precision"]) >= float(parent["top100_dominant_precision"]),
        "zero_filled_mrr_not_lower": float(final["zero_filled_mrr"]) >= float(parent["zero_filled_mrr"]),
        "fragmentation_not_higher": float(final["fragmentation_median_top500"]) <= float(parent["fragmentation_median_top500"]),
    }


def validate_local_layer(
    pre: dict[str, Any],
    sync_candidates: list[dict[str, Any]],
    ids_by_year: dict[int, list[str]],
) -> list[dict[str, Any]]:
    req(pre["schema"] == "ORBITTRACE_FINAL_LOCAL_TRUNK_AMOS_2023_2024_PRETRUTH", "wrong final pretruth schema")
    req(pre["scientific_role"] == SCIENTIFIC_ROLE and pre["phase"] == "PRETRUTH_FROZEN", "wrong final pretruth role/phase")
    req(pre["selected_final_method"] == SELECTED_FINAL_METHOD, "selected final method changed")
    req(pre["years"] == list(YEARS) and pre["blind_exclusion"] == list(BLIND), "final year/blind freeze changed")
    req(pre["labels_accessed"] is False and pre["amos_shower_associations_accessed"] is False, "final pretruth reports label access")
    req(pre["new_external_survey_hunt"] is False, "replacement external survey became authorized")
    for key in (
        "target_information_access",
        "target_region_events_accessed",
        "orbittrace_target_access",
        "sonotaco_access",
        "asfn_access",
        "efn_access",
        "maarsy_scientific_access",
        "dms_scientific_access",
        "amos_post_result_parameter_search",
    ):
        req(pre[key] is False, f"final pretruth firewall failed: {key}")

    req(pre["local_trunk_source_commit"] == LOCAL_TRUNK_SOURCE_COMMIT, "local-trunk source commit changed")
    req(
        pre["local_trunk_source_pins"]
        == {
            "protocol_git_blob": LOCAL_TRUNK_PROTOCOL_BLOB,
            "constructor_git_blob": LOCAL_TRUNK_CONSTRUCTOR_BLOB,
            "lazy_transport_git_blob": LOCAL_TRUNK_LAZY_TRANSPORT_BLOB,
            "exact_full_row_transport_git_blob": LOCAL_TRUNK_EXACT_ROW_TRANSPORT_BLOB,
        },
        "local-trunk source pins changed",
    )
    transfer = pre["local_trunk_transfer"]
    req(transfer["years"] == list(YEARS), "local-trunk transfer years changed")
    req(float(transfer["radius"]) == 1.0 and int(transfer["min_annual_support"]) == 4, "local-trunk radius/support changed")
    req(transfer["rank_order_preserved_from_density_sync_parent"] is True, "local-trunk rank preservation changed")
    req(transfer["same_rank_parent_subset_only"] is True, "local-trunk same-rank subset invariant changed")
    req(transfer["post_result_parameter_search"] is False, "local-trunk transfer reports parameter search")

    parent_copy = list(pre["density_sync_parent_candidates"])
    req(parent_copy == sync_candidates, "serialized density-sync parent copy differs from hardened parent pretruth")
    req(ordered_membership_sha(parent_copy) == pre["local_trunk_parent_ordered_membership_sha256"], "local-trunk parent membership hash mismatch")

    final = list(pre["local_trunk_candidates"])
    diag = list(pre["local_trunk_diagnostics"])
    req(len(final) == len(sync_candidates) == len(diag), "local-trunk slot/diagnostic count changed")
    req([int(row["rank"]) for row in final] == list(range(1, len(final) + 1)), "local-trunk fixed rank order changed")

    annual_sets = {y: set(ids_by_year[y]) for y in YEARS}
    pooled = set().union(*annual_sets.values())
    seen: set[str] = set()
    changed = 0
    for rank, (parent, row, drow) in enumerate(zip(sync_candidates, final, diag), 1):
        req(set(row) == {"rank", "parent_family_id", "family_id", "parent_node_id", "event_ids", "member_count", "representation_changed"}, f"local-trunk candidate schema changed at rank {rank}")
        req(int(row["rank"]) == rank, f"local-trunk rank changed at {rank}")
        req(str(row["parent_family_id"]) == str(parent["family_id"]), f"local-trunk parent family changed at rank {rank}")
        req(str(row["family_id"]) == str(parent["family_id"]), f"local-trunk preserved family identity changed at rank {rank}")
        req(int(row["parent_node_id"]) == int(parent["node_id"]), f"local-trunk parent node changed at rank {rank}")
        parent_ids = [str(x) for x in parent["event_ids"]]
        final_ids = [str(x) for x in row["event_ids"]]
        req(final_ids and final_ids == sorted(final_ids), f"local-trunk final membership not deterministic at rank {rank}")
        req(len(final_ids) == len(set(final_ids)) == int(row["member_count"]), f"local-trunk final membership count mismatch at rank {rank}")
        req(set(final_ids).issubset(set(parent_ids)), f"local-trunk escaped same-rank parent at rank {rank}")
        req(set(final_ids).issubset(pooled), f"local-trunk contains non-retained event at rank {rank}")
        req(seen.isdisjoint(final_ids), f"local-trunk final slots overlap at rank {rank}")
        seen.update(final_ids)
        changed_here = final_ids != parent_ids
        req(bool(row["representation_changed"]) == changed_here, f"local-trunk changed flag mismatch at rank {rank}")
        changed += int(changed_here)
        if changed_here:
            req(all(len(set(final_ids).intersection(annual_sets[y])) >= 4 for y in YEARS), f"changed local trunk violates 4+4 annual support at rank {rank}")

        req(int(drow["rank"]) == rank, f"local-trunk diagnostic rank changed at {rank}")
        req(str(drow["parent_family_id"]) == str(parent["family_id"]), f"local-trunk diagnostic family changed at {rank}")
        req(int(drow["parent_node_id"]) == int(parent["node_id"]), f"local-trunk diagnostic node changed at {rank}")
        req(drow["parent_membership_sha256"] == membership_sha(parent_ids), f"local-trunk diagnostic parent hash mismatch at {rank}")
        req(drow["final_membership_sha256"] == membership_sha(final_ids), f"local-trunk diagnostic final hash mismatch at {rank}")
        req(int(drow["parent_member_count"]) == len(parent_ids), f"local-trunk diagnostic parent count mismatch at {rank}")
        req(int(drow["final_member_count"]) == len(final_ids), f"local-trunk diagnostic final count mismatch at {rank}")
        req(bool(drow["representation_changed"]) == changed_here, f"local-trunk diagnostic changed flag mismatch at {rank}")
        req(isinstance(drow["topology"], dict), f"local-trunk topology summary missing at rank {rank}")

    req(changed == int(pre["local_trunk_changed_slot_count"]), "local-trunk changed-slot count mismatch")
    req(bool(changed > 0) == bool(pre["local_trunk_mechanism_active"]), "local-trunk mechanism-active flag mismatch")
    req(ordered_membership_sha(final) == pre["local_trunk_final_ordered_membership_sha256"], "local-trunk final membership hash mismatch")
    return final


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pretruth", type=Path, required=True)
    ap.add_argument("--pretruth-sha256", type=str, required=True)
    ap.add_argument("--labels-2023", type=Path, required=True)
    ap.add_argument("--labels-2024", type=Path, required=True)
    ap.add_argument("--parent-amos-evaluator", type=Path, required=True)
    ap.add_argument("--local-trunk-gmn-evaluator", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    req(git_blob_sha(a.parent_amos_evaluator) == PARENT_AMOS_EVALUATOR_BLOB, "hardened parent AMOS evaluator changed")
    req(git_blob_sha(a.local_trunk_gmn_evaluator) == LOCAL_TRUNK_GMN_EVALUATOR_BLOB, "local-trunk GMN metric evaluator changed")

    actual_sha = sha256(a.pretruth)
    req(actual_sha == a.pretruth_sha256.strip().lower(), "pretruth payload hash changed before label evaluation")
    pre = json.loads(a.pretruth.read_text(encoding="utf-8"))

    parent_eval = load_module(a.parent_amos_evaluator, "pinned_parent_amos_evaluator")
    local_eval = load_module(a.local_trunk_gmn_evaluator, "pinned_local_trunk_metric_evaluator")

    # Validate the entire inherited density-synchronous AMOS pretruth using the
    # already-hardened evaluator before labels are opened. Only the new local
    # fields are removed and the historical selected-method string restored.
    parent_pre = {k: v for k, v in pre.items() if k not in LOCAL_EXTRA_KEYS}
    parent_pre["selected_final_method"] = parent_eval.SELECTED_FINAL_METHOD
    ids_by_year, ordinary_candidates, recurrent_candidates, sync_candidates = parent_eval.validate_pretruth(parent_pre)

    # Validate the complete new local layer, still before either label file opens.
    final_candidates = validate_local_layer(pre, sync_candidates, ids_by_year)

    labels_by_year = {
        2023: parent_eval.load_labels(a.labels_2023, ids_by_year[2023], 2023),
        2024: parent_eval.load_labels(a.labels_2024, ids_by_year[2024], 2024),
    }
    hidden: dict[str, str] = {}
    for y in YEARS:
        req(set(hidden).isdisjoint(labels_by_year[y]), "event ID reused across AMOS label years")
        hidden.update(labels_by_year[y])

    annual_sets = {y: set(ids_by_year[y]) for y in YEARS}
    ordinary_metrics = {str(y): local_eval.metrics(ordinary_candidates, hidden, annual_sets[y]) for y in YEARS}
    recurrent_metrics = {str(y): local_eval.metrics(recurrent_candidates, hidden, annual_sets[y]) for y in YEARS}
    sync_metrics = {str(y): local_eval.metrics(sync_candidates, hidden, annual_sets[y]) for y in YEARS}
    final_metrics = {str(y): local_eval.metrics(final_candidates, hidden, annual_sets[y]) for y in YEARS}

    ordinary_gates = {str(y): compare_no_regression(ordinary_metrics[str(y)], final_metrics[str(y)]) for y in YEARS}
    parent_gates = {str(y): compare_no_regression(sync_metrics[str(y)], final_metrics[str(y)]) for y in YEARS}
    strict_vs_ordinary_100 = any(int(final_metrics[str(y)]["recovered_at_100"]) > int(ordinary_metrics[str(y)]["recovered_at_100"]) for y in YEARS)
    active_vs_ordinary = bool(
        [tuple(row["event_ids"]) for row in final_candidates]
        != [tuple(row["event_ids"]) for row in ordinary_candidates]
    )
    local_increment_active = bool(pre["local_trunk_mechanism_active"])
    strict_zero_vs_parent = any(float(final_metrics[str(y)]["zero_filled_mrr"]) > float(sync_metrics[str(y)]["zero_filled_mrr"]) for y in YEARS)

    primary_pass = bool(
        strict_vs_ordinary_100
        and active_vs_ordinary
        and all(all(g.values()) for g in ordinary_gates.values())
        and all(all(g.values()) for g in parent_gates.values())
    )
    primary_verdict = PRIMARY_PASS if primary_pass else PRIMARY_FAIL

    increment_pass = bool(
        local_increment_active
        and strict_zero_vs_parent
        and all(all(g.values()) for g in parent_gates.values())
    )
    increment_verdict = INCREMENT_PASS if increment_pass else INCREMENT_NO

    result = {
        "schema": "ORBITTRACE_FINAL_LOCAL_TRUNK_AMOS_2023_2024_EXTERNAL_RESULT",
        "verdict": primary_verdict,
        "incremental_local_trunk_verdict": increment_verdict,
        "scientific_role": SCIENTIFIC_ROLE,
        "phase": "POSTFREEZE_LABEL_EVALUATION",
        "selected_final_method": SELECTED_FINAL_METHOD,
        "pretruth_sha256": actual_sha,
        "pretruth_internal_integrity_verified_before_labels": True,
        "years": list(YEARS),
        "events_by_year": dict(pre["events_by_year"]),
        "label_file_sha256": {"2023": sha256(a.labels_2023), "2024": sha256(a.labels_2024)},
        "candidate_counts": {
            "ordinary": len(ordinary_candidates),
            "recurrent": len(recurrent_candidates),
            "density_sync": len(sync_candidates),
            "local_trunk": len(final_candidates),
        },
        "local_trunk_changed_slot_count": int(pre["local_trunk_changed_slot_count"]),
        "local_trunk_mechanism_active": local_increment_active,
        "strict_recovered_at_100_improvement_vs_ordinary_some_year": strict_vs_ordinary_100,
        "strict_zero_filled_mrr_improvement_vs_density_sync_some_year": strict_zero_vs_parent,
        "ordinary_metrics": ordinary_metrics,
        "recurrent_metrics": recurrent_metrics,
        "density_sync_metrics": sync_metrics,
        "local_trunk_metrics": final_metrics,
        "local_trunk_vs_ordinary_annual_gates": ordinary_gates,
        "local_trunk_vs_density_sync_annual_gates": parent_gates,
        "blind_exclusion": list(BLIND),
        "candidate_generation_recomputed_after_labels": False,
        "local_membership_recomputed_after_labels": False,
        "ranking_changed_after_labels": False,
        "final_method_switched_after_labels": False,
        "quality_filter_used": False,
        "survey_calibration_used": False,
        "amos_post_result_parameter_search": False,
        "replacement_external_panel_authorized": False,
        "new_external_survey_hunt": False,
        "sonotaco_access": False,
        "asfn_access": False,
        "efn_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "orbittrace_target_access": False,
    }
    out = a.output / "FINAL_LOCAL_TRUNK_AMOS_2023_2024_EXTERNAL_RESULT.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "verdict": primary_verdict,
                "incremental": increment_verdict,
                "strict_vs_ordinary_100": strict_vs_ordinary_100,
                "strict_zero_vs_parent": strict_zero_vs_parent,
                "local_changed_slots": int(pre["local_trunk_changed_slot_count"]),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
