#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

PRIMARY_FAIL = "FAIL_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_AMOS_2023_2024_FINAL_EXTERNAL_VALIDATION"
INCREMENT_NO = "NO_DEMONSTRATED_DENSITY_SYNCHRONY_INCREMENT_OVER_RECURRENT_EOM_AMOS"


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def member_hash(prefix: str, members: list[str]) -> str:
    return hashlib.sha256((prefix + "|" + "|".join(members)).encode()).hexdigest()[:20]


def order_sha(candidates: list[dict[str, Any]]) -> str:
    return hashlib.sha256("\n".join(str(x["family_id"]) for x in candidates).encode()).hexdigest()


def membership_sha(candidates: list[dict[str, Any]]) -> str:
    return hashlib.sha256("\n".join("|".join(map(str, row["event_ids"])) for row in candidates).encode()).hexdigest()


def mapping_sha(mapping: dict[Any, Any]) -> str:
    payload = {str(k): v for k, v in sorted(mapping.items(), key=lambda kv: int(kv[0]))}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["event_id", "shower_association"])
        w.writeheader()
        w.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def run_eval(evaluator: Path, pretruth: Path, labels23: Path, labels24: Path, output: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable, str(evaluator.resolve()),
            "--pretruth", str(pretruth.resolve()),
            "--pretruth-sha256", sha(pretruth),
            "--labels-2023", str(labels23.resolve()),
            "--labels-2024", str(labels24.resolve()),
            "--output", str(output.resolve()),
        ],
        text=True,
        capture_output=True,
        check=False,
    )


def expect_pretruth_rejection(
    name: str,
    base: dict[str, Any],
    mutate: Callable[[dict[str, Any]], None],
    expected_error: str,
    evaluator: Path,
    work: Path,
) -> dict[str, Any]:
    obj = copy.deepcopy(base)
    mutate(obj)
    path = work / f"tampered_{name}.json"
    write_json(path, obj)
    labels23 = work / "MUST_NOT_OPEN_LABELS_2023.csv"
    labels24 = work / "MUST_NOT_OPEN_LABELS_2024.csv"
    proc = run_eval(evaluator, path, labels23, labels24, work / f"out_{name}")
    combined = proc.stdout + "\n" + proc.stderr
    require(proc.returncode != 0, f"tamper {name} unexpectedly evaluated")
    require(expected_error in combined, f"tamper {name} failed for wrong reason; expected {expected_error!r}; tail={combined[-1200:]!r}")
    require("FileNotFoundError" not in combined and "MUST_NOT_OPEN_LABELS" not in combined, f"tamper {name} reached label file opening")
    return {
        "name": name,
        "rejected": True,
        "label_files_opened": False,
        "expected_error": expected_error,
        "tampered_pretruth_sha256": sha(path),
    }


def refresh_method_hashes(obj: dict[str, Any], method: str) -> None:
    obj[f"{method}_order_sha256"] = order_sha(obj[f"{method}_candidates"])
    obj[f"{method}_membership_sha256"] = membership_sha(obj[f"{method}_candidates"])


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--evaluator", type=Path, required=True)
    p.add_argument("--valid-pretruth", type=Path, required=True)
    p.add_argument("--labels-2023", type=Path, required=True)
    p.add_argument("--labels-2024", type=Path, required=True)
    p.add_argument("--work", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.work.mkdir(parents=True, exist_ok=True)
    a.output.mkdir(parents=True, exist_ok=True)

    base = json.loads(a.valid_pretruth.read_text(encoding="utf-8"))

    # Exact valid synthetic pretruth and exact SPORADIC sentinel remain accepted.
    valid_out = a.work / "valid"
    valid_proc = run_eval(a.evaluator, a.valid_pretruth, a.labels_2023, a.labels_2024, valid_out)
    require(valid_proc.returncode == 0, f"valid hardened evaluator failed: {(valid_proc.stdout + valid_proc.stderr)[-1500:]}")
    valid_result_path = valid_out / "FINAL_DENSITY_SYNC_AMOS_2023_2024_EXTERNAL_RESULT.json"
    valid_result = json.loads(valid_result_path.read_text(encoding="utf-8"))
    require(valid_result["pretruth_internal_integrity_verified_before_labels"] is True, "valid run did not record pretruth integrity")
    exact_sporadic_accepted = True

    pretruth_tests: list[dict[str, Any]] = []

    pretruth_tests.append(expect_pretruth_rejection(
        "source_pin", base,
        lambda x: x["source_pins"].__setitem__("density_sync_git_blob", "0" * 40),
        "pretruth scientific/transport source pins changed", a.evaluator, a.work,
    ))
    pretruth_tests.append(expect_pretruth_rejection(
        "hdbscan_pin", base,
        lambda x: x["frozen_hdbscan"].__setitem__("min_samples", 11),
        "frozen HDBSCAN declaration changed", a.evaluator, a.work,
    ))
    pretruth_tests.append(expect_pretruth_rejection(
        "order_hash", base,
        lambda x: x.__setitem__("ordinary_order_sha256", "0" * 64),
        "ordinary candidate order hash mismatch", a.evaluator, a.work,
    ))

    def nonretained(x: dict[str, Any]) -> None:
        row = x["ordinary_candidates"][0]
        ids = sorted(list(row["event_ids"]) + ["9999-NONRETAINED-SYNTHETIC"])
        row["event_ids"] = ids
        row["member_count"] = len(ids)
        row["family_id"] = member_hash("HDBEOM", ids)
        refresh_method_hashes(x, "ordinary")

    pretruth_tests.append(expect_pretruth_rejection(
        "nonretained_candidate_id", base, nonretained,
        "contains non-retained event IDs", a.evaluator, a.work,
    ))

    def overlap(x: dict[str, Any]) -> None:
        require(len(x["ordinary_candidates"]) >= 2, "synthetic fixture lacks two ordinary candidates")
        donor = str(x["ordinary_candidates"][0]["event_ids"][0])
        row = x["ordinary_candidates"][1]
        require(donor not in row["event_ids"], "synthetic ordinary fixture already overlaps")
        ids = sorted(list(row["event_ids"]) + [donor])
        row["event_ids"] = ids
        row["member_count"] = len(ids)
        row["family_id"] = member_hash("HDBEOM", ids)
        refresh_method_hashes(x, "ordinary")

    pretruth_tests.append(expect_pretruth_rejection(
        "overlapping_membership", base, overlap,
        "ordinary flat candidate memberships overlap", a.evaluator, a.work,
    ))

    def duplicate_retained(x: dict[str, Any]) -> None:
        ids = list(x["event_ids_by_year"]["2023"])
        ids.append(ids[0])
        x["event_ids_by_year"]["2023"] = sorted(ids)
        x["events_by_year"]["2023"] = len(ids)
        x["events_total"] = int(x["events_total"]) + 1

    pretruth_tests.append(expect_pretruth_rejection(
        "duplicate_retained_id", base, duplicate_retained,
        "duplicate retained event ID within 2023", a.evaluator, a.work,
    ))

    def corrupt_annual(x: dict[str, Any]) -> None:
        node = sorted(x["recurrent_annual_eom"], key=int)[0]
        vals = list(x["recurrent_annual_eom"][node])
        vals[0] = float(vals[0]) + 0.001
        x["recurrent_annual_eom"][node] = vals
        new_hash = mapping_sha(x["recurrent_annual_eom"])
        x["recurrent_annual_eom_sha256"] = new_hash
        x["density_sync_parent_annual_sha256"] = new_hash

    pretruth_tests.append(expect_pretruth_rejection(
        "annual_reconstruction", base, corrupt_annual,
        "annual EOM reconstruction mismatch", a.evaluator, a.work,
    ))

    def flip_mechanism(x: dict[str, Any]) -> None:
        x["mechanism_active"]["ordinary_vs_density_sync"] = not bool(x["mechanism_active"]["ordinary_vs_density_sync"])

    pretruth_tests.append(expect_pretruth_rejection(
        "mechanism_flag", base, flip_mechanism,
        "stored mechanism-active flags do not match selected nodes/orders", a.evaluator, a.work,
    ))

    pretruth_tests.append(expect_pretruth_rejection(
        "extra_top_level_field", base,
        lambda x: x.__setitem__("unexpected_truth_field", "SHOULD_FAIL"),
        "unexpected top-level pretruth schema", a.evaluator, a.work,
    ))

    def candidate_extra_field(x: dict[str, Any]) -> None:
        x["ordinary_candidates"][0]["truth_hint"] = "SHOULD_FAIL"

    pretruth_tests.append(expect_pretruth_rejection(
        "candidate_extra_field", base, candidate_extra_field,
        "ordinary candidate 0 has unexpected schema", a.evaluator, a.work,
    ))

    def bad_family(x: dict[str, Any]) -> None:
        x["ordinary_candidates"][0]["family_id"] = "0" * 20
        refresh_method_hashes(x, "ordinary")

    pretruth_tests.append(expect_pretruth_rejection(
        "family_id", base, bad_family,
        "ordinary candidate deterministic family ID mismatch", a.evaluator, a.work,
    ))

    def score_order(x: dict[str, Any]) -> None:
        require(len(x["ordinary_candidates"]) >= 2, "synthetic fixture lacks two ordinary candidates")
        first = float(x["ordinary_candidates"][0]["ordinary_stability"])
        x["ordinary_candidates"][-1]["ordinary_stability"] = first + abs(first) + 1000.0

    pretruth_tests.append(expect_pretruth_rejection(
        "score_order", base, score_order,
        "ordinary candidate order inconsistent with frozen score/tie sort", a.evaluator, a.work,
    ))

    # A structurally valid empty catalogue is a scientific state, not a technical retry.
    empty = copy.deepcopy(base)
    empty_hash = hashlib.sha256(b"").hexdigest()
    for method in ("ordinary", "recurrent", "density_sync"):
        empty[f"{method}_selected_nodes"] = []
        empty[f"{method}_candidates"] = []
        empty[f"{method}_order_sha256"] = empty_hash
        empty[f"{method}_membership_sha256"] = empty_hash
    empty["mechanism_active"] = {
        "ordinary_vs_recurrent": False,
        "recurrent_vs_density_sync": False,
        "ordinary_vs_density_sync": False,
    }
    empty_path = a.work / "valid_empty_catalogues.json"
    write_json(empty_path, empty)
    empty_proc = run_eval(a.evaluator, empty_path, a.labels_2023, a.labels_2024, a.work / "empty_out")
    require(empty_proc.returncode == 0, f"empty candidate catalogue became technical failure: {(empty_proc.stdout + empty_proc.stderr)[-1200:]}")
    empty_result_path = a.work / "empty_out" / "FINAL_DENSITY_SYNC_AMOS_2023_2024_EXTERNAL_RESULT.json"
    empty_result = json.loads(empty_result_path.read_text(encoding="utf-8"))
    require(empty_result["verdict"] == PRIMARY_FAIL, f"empty final catalogue did not yield binding FAIL: {empty_result['verdict']}")
    require(empty_result["incremental_density_synchrony_verdict"] == INCREMENT_NO, "empty final catalogue unexpectedly demonstrated incremental gain")
    require(empty_result["candidate_counts"] == {"ordinary": 0, "recurrent": 0, "density_sync": 0}, "empty candidate counts changed")
    empty_catalogue_binding_fail = True

    # Ambiguous no-association aliases must fail after valid pretruth, before metrics.
    label_rows = read_csv(a.labels_2024)
    idx = next((i for i, r in enumerate(label_rows) if r["shower_association"] == "SPORADIC"), None)
    require(idx is not None, "synthetic 2024 labels lack SPORADIC fixture")
    alias_rows = copy.deepcopy(label_rows)
    alias_rows[int(idx)]["shower_association"] = "sporadic"
    bad_label_path = a.work / "labels_2024_bad_sporadic.csv"
    write_csv(bad_label_path, alias_rows)
    bad_label_proc = run_eval(a.evaluator, a.valid_pretruth, a.labels_2023, bad_label_path, a.work / "bad_label_out")
    combined = bad_label_proc.stdout + "\n" + bad_label_proc.stderr
    require(bad_label_proc.returncode != 0 and "noncanonical SPORADIC sentinel" in combined, "noncanonical SPORADIC sentinel did not fail closed")
    require("FINAL_DENSITY_SYNC_AMOS_2023_2024_EXTERNAL_RESULT.json" not in combined, "bad sentinel reached a scientific result")
    ambiguous_sentinel_rejected = True

    alias_rows2 = copy.deepcopy(label_rows)
    alias_rows2[int(idx)]["shower_association"] = "NONE"
    bad_label_path2 = a.work / "labels_2024_bad_none.csv"
    write_csv(bad_label_path2, alias_rows2)
    bad_label_proc2 = run_eval(a.evaluator, a.valid_pretruth, a.labels_2023, bad_label_path2, a.work / "bad_label_out2")
    combined2 = bad_label_proc2.stdout + "\n" + bad_label_proc2.stderr
    require(bad_label_proc2.returncode != 0 and "ambiguous no-association sentinel" in combined2, "NONE no-association alias did not fail closed")

    assertions = {
        "valid_exact_sporadic_accepted": exact_sporadic_accepted,
        "forged_source_pin_rejected_prelabels": True,
        "forged_hdbscan_pin_rejected_prelabels": True,
        "forged_order_hash_rejected_prelabels": True,
        "nonretained_candidate_id_rejected_prelabels": True,
        "overlapping_membership_rejected_prelabels": True,
        "duplicate_retained_id_rejected_prelabels": True,
        "annual_reconstruction_corruption_rejected_prelabels": True,
        "mechanism_flag_corruption_rejected_prelabels": True,
        "extra_top_level_field_rejected_prelabels": True,
        "extra_candidate_field_rejected_prelabels": True,
        "forged_family_id_rejected_prelabels": True,
        "score_order_inconsistency_rejected_prelabels": True,
        "empty_catalogues_yield_binding_fail_not_technical_retry": empty_catalogue_binding_fail,
        "ambiguous_no_association_sentinels_rejected": ambiguous_sentinel_rejected,
    }
    require(all(assertions.values()), "one or more v3 hardening assertions failed")

    audit = {
        "schema": "FINAL_DENSITY_SYNC_AMOS_EVALUATOR_HARDENING_AUDIT_V3",
        "verdict": "PASS_FINAL_DENSITY_SYNC_AMOS_EVALUATOR_HARDENING_AUDIT_V3",
        "synthetic_only": True,
        "valid_pretruth_sha256": sha(a.valid_pretruth),
        "valid_result_sha256": sha(valid_result_path),
        "empty_catalogue_pretruth_sha256": sha(empty_path),
        "empty_catalogue_result_sha256": sha(empty_result_path),
        "pretruth_tamper_tests": pretruth_tests,
        "pretruth_tamper_test_count": len(pretruth_tests),
        "all_pretruth_tampers_rejected_before_labels": all(t["rejected"] and not t["label_files_opened"] for t in pretruth_tests),
        "assertions": assertions,
        "assertion_count": len(assertions),
        "scientific_method_or_gate_changed": False,
        "scientific_data_accessed": False,
        "gmn_accessed": False,
        "sonotaco_accessed": False,
        "amos_accessed": False,
        "asfn_accessed": False,
        "efn_accessed": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    out = a.output / "FINAL_DENSITY_SYNC_AMOS_EVALUATOR_HARDENING_AUDIT_V3.json"
    out.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
