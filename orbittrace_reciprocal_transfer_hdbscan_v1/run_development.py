#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np

from orbittrace_reciprocal_transfer_hdbscan_v1.reciprocal_transfer import (
    MIN_CLUSTER_SIZE,
    MIN_SAMPLES,
    build_reciprocal_transfer,
)


YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
QUALITY_SHA = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
PARENT_RESULT_SHA = "433c641f57122b244b9476f5cbcb5e6f82956d9467270a9f24945600a32d2106"
PARENT_PRELABEL_SHA = "e304f6660697ed27a7e2e546ba2b9f2ecdb43f923745cb7424a3781ad55b9ad1"
PROTOCOL_BLOB = "6181ba8e4dfa34f869249389bda2eae46ca2c690"
KERNEL_BLOB = "f3a7c8d5ea53bf856fb8d0225d5d578c4248e5ce"
SYNTHETIC_AUDIT_RUN = 31849167489
SYNTHETIC_AUDIT_ARTIFACT = 9236929569
SYNTHETIC_AUDIT_RESULT_SHA = "8c39cb44258df6b8fbc3160dd2c2d2d98bc58de6910bda017cf6f726182cbea1"


def req(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_parent_helpers() -> Any:
    root = Path(__file__).resolve().parents[1]
    parent_dir = root / "orbittrace_recurrent_eom_hdbscan_v1"
    parent_runner = parent_dir / "run_development.py"
    req(parent_runner.exists(), "promoted recurrent-EOM runner missing")
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    spec = importlib.util.spec_from_file_location("reciprocal_transfer_parent_helpers", parent_runner)
    req(spec is not None and spec.loader is not None, "cannot load promoted recurrent-EOM runner")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def save_array(path: Path, array: np.ndarray) -> str:
    np.save(path, np.asarray(array), allow_pickle=False)
    return sha(path)


def save_ids(path: Path, ids: list[str]) -> str:
    path.write_text("\n".join(ids) + "\n")
    return sha(path)


def json_candidate(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "family_id": str(row["family_id"]),
        "annual_labels": {"2022": int(row["annual_labels"]["2022"]), "2023": int(row["annual_labels"]["2023"])},
        "event_ids_2022": list(row["event_ids_2022"]),
        "event_ids_2023": list(row["event_ids_2023"]),
        "event_ids": list(row["event_ids"]),
        "n_2022": int(row["n_2022"]),
        "n_2023": int(row["n_2023"]),
        "persistence_2022": float(row["persistence_2022"]),
        "persistence_2023": float(row["persistence_2023"]),
        "worst_year_persistence": float(row["worst_year_persistence"]),
        "best_year_persistence": float(row["best_year_persistence"]),
        "forward_majority_fraction_reporting_only": float(row["forward_majority_fraction_reporting_only"]),
        "backward_majority_fraction_reporting_only": float(row["backward_majority_fraction_reporting_only"]),
    }


def mappings_json(mapping: dict[int, int | None]) -> dict[str, int | None]:
    return {str(k): (None if v is None else int(v)) for k, v in sorted(mapping.items())}


def fractions_json(mapping: dict[int, float]) -> dict[str, float]:
    return {str(k): float(v) for k, v in sorted(mapping.items())}


def metric_core(row: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in row.items() if k != "first_rank_by_label"}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--quality-source", type=Path, required=True)
    p.add_argument("--support-source-parts", type=Path, required=True)
    p.add_argument("--candidate-payload", type=Path, required=True)
    p.add_argument("--baseline-payload", type=Path, required=True)
    p.add_argument("--scorer-parts", type=Path, required=True)
    p.add_argument("--v8-result-json", type=Path, required=True)
    p.add_argument("--parent-result-json", type=Path, required=True)
    p.add_argument("--parent-prelabel-json", type=Path, required=True)
    p.add_argument("--synthetic-audit-json", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    parent = load_parent_helpers()
    req(parent.QUALITY_SHA == QUALITY_SHA, "parent quality-source pin drift")
    req(parent.V8_RESULT_SHA == V8_RESULT_SHA, "parent support-result pin drift")
    req(parent.MIN_CLUSTER_SIZE == MIN_CLUSTER_SIZE and parent.MIN_SAMPLES == MIN_SAMPLES, "parent HDBSCAN size pins drift")
    req(tuple(parent.YEARS) == YEARS and tuple(parent.BLIND) == BLIND, "parent year/firewall pins drift")

    req(sha(a.quality_source) == QUALITY_SHA, "frozen GMN runtime utility source changed")
    req(sha(a.v8_result_json) == V8_RESULT_SHA, "frozen GMN support artifact changed")
    req(sha(a.synthetic_audit_json) == SYNTHETIC_AUDIT_RESULT_SHA, "synthetic audit receipt changed")
    audit = json.loads(a.synthetic_audit_json.read_text())
    req(audit["verdict"] == "PASS_RECIPROCAL_TRANSFER_HDBSCAN_V1_SYNTHETIC_AUDIT", "synthetic audit did not pass")
    req(audit["gmn_accessed"] is False and audit["truth_accessed"] is False, "synthetic audit crossed data boundary")

    qmod = parent.load_module(a.quality_source, "reciprocal_transfer_frozen_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-reciprocal-transfer-hdbscan-v1-development-2022-2023-target-excluded"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden_sealed, sources = support.parse_catalogue(base)
    req(sorted(scan) == list(YEARS), f"GMN runtime accessed wrong years: {sorted(scan)}")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "GMN source list changed")

    events_by_year: dict[int, list[dict[str, Any]]] = {}
    for year in YEARS:
        raw = list(scan[year])
        rows = [parent.normalize_event(row, year) for row in raw]
        req(len(rows) == len(raw), f"event normalization changed {year} event count")
        req(all(not (BLIND[0] <= e["sol"] <= BLIND[1]) for e in rows), f"protected region survived parser in {year}")
        req(len({e["id"] for e in rows}) == len(rows), f"duplicate annual event IDs in {year}")
        events_by_year[year] = rows
    all_ids = [e["id"] for year in YEARS for e in events_by_year[year]]
    req(len(set(all_ids)) == len(all_ids), "duplicate pooled event IDs")

    ids22 = [str(e["id"]) for e in events_by_year[2022]]
    ids23 = [str(e["id"]) for e in events_by_year[2023]]
    X22 = parent.geo_matrix(events_by_year[2022])
    X23 = parent.geo_matrix(events_by_year[2023])

    # The successor is generated completely before the parent prelabel/result or
    # sealed shower truth are opened below.
    successor = build_reciprocal_transfer(X22, ids22, X23, ids23)
    candidates = [json_candidate(c) for c in successor.candidates]

    array_hashes = {
        "geo6_2022": save_array(a.output / "RECIPROCAL_TRANSFER_GEO6_2022.npy", X22),
        "geo6_2023": save_array(a.output / "RECIPROCAL_TRANSFER_GEO6_2023.npy", X23),
        "labels_2022": save_array(a.output / "RECIPROCAL_TRANSFER_LABELS_2022.npy", successor.labels_2022),
        "labels_2023": save_array(a.output / "RECIPROCAL_TRANSFER_LABELS_2023.npy", successor.labels_2023),
        "persistence_2022": save_array(a.output / "RECIPROCAL_TRANSFER_PERSISTENCE_2022.npy", successor.persistence_2022),
        "persistence_2023": save_array(a.output / "RECIPROCAL_TRANSFER_PERSISTENCE_2023.npy", successor.persistence_2023),
        "predicted_2022_to_2023": save_array(a.output / "RECIPROCAL_TRANSFER_PREDICTED_2022_TO_2023.npy", successor.predicted_2022_to_2023),
        "predicted_2023_to_2022": save_array(a.output / "RECIPROCAL_TRANSFER_PREDICTED_2023_TO_2022.npy", successor.predicted_2023_to_2022),
        "probabilities_2022_to_2023_reporting_only": save_array(a.output / "RECIPROCAL_TRANSFER_PROB_2022_TO_2023.npy", successor.probabilities_2022_to_2023),
        "probabilities_2023_to_2022_reporting_only": save_array(a.output / "RECIPROCAL_TRANSFER_PROB_2023_TO_2022.npy", successor.probabilities_2023_to_2022),
        "condensed_tree_2022": save_array(a.output / "RECIPROCAL_TRANSFER_CONDENSED_TREE_2022.npy", successor.condensed_tree_2022),
        "condensed_tree_2023": save_array(a.output / "RECIPROCAL_TRANSFER_CONDENSED_TREE_2023.npy", successor.condensed_tree_2023),
    }
    id_hashes = {
        "2022": save_ids(a.output / "RECIPROCAL_TRANSFER_INPUT_IDS_2022.txt", ids22),
        "2023": save_ids(a.output / "RECIPROCAL_TRANSFER_INPUT_IDS_2023.txt", ids23),
    }

    prelabel = {
        "scientific_role": "PRELABEL_FROZEN_RECIPROCAL_TRANSFER_HDBSCAN_V1",
        "events_by_year": {"2022": len(ids22), "2023": len(ids23)},
        "input_id_sha256": id_hashes,
        "array_sha256": array_hashes,
        "native_cluster_count": {"2022": len(successor.persistence_2022), "2023": len(successor.persistence_2023)},
        "forward_mapping": mappings_json(successor.forward_mapping),
        "backward_mapping": mappings_json(successor.backward_mapping),
        "forward_majority_fraction_reporting_only": fractions_json(successor.forward_fraction),
        "backward_majority_fraction_reporting_only": fractions_json(successor.backward_fraction),
        "reciprocal_candidate_count": len(candidates),
        "candidates": candidates,
        "ranking_rule": [
            "descending min(native persistence 2022, native persistence 2023)",
            "descending max(native persistence 2022, native persistence 2023)",
            "descending min(native member count 2022, native member count 2023)",
            "descending total native member count",
            "ascending deterministic family ID",
        ],
        "prediction_probabilities_used_for_matching": False,
        "prediction_probabilities_used_for_ranking": False,
        "majority_fractions_used_for_ranking": False,
        "strict_majority_rule": "non-noise counterpart count * 2 > native annual cluster member count",
        "frozen_hdbscan": {
            "representation": "GEO6",
            "min_cluster_size": MIN_CLUSTER_SIZE,
            "min_samples": MIN_SAMPLES,
            "metric": "euclidean",
            "cluster_selection_method": "eom",
            "cluster_selection_epsilon": 0.0,
            "allow_single_cluster": False,
            "prediction_data": True,
        },
        "protocol_git_blob": PROTOCOL_BLOB,
        "kernel_git_blob": KERNEL_BLOB,
        "synthetic_audit_run": SYNTHETIC_AUDIT_RUN,
        "synthetic_audit_artifact": SYNTHETIC_AUDIT_ARTIFACT,
        "synthetic_audit_result_sha256": SYNTHETIC_AUDIT_RESULT_SHA,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "amos_scientific_access": False,
        "efn_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    prelabel_path = a.output / "RECIPROCAL_TRANSFER_HDBSCAN_V1_PRELABEL.json"
    prelabel_path.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    prelabel_sha = sha(prelabel_path)

    # Only after successor generation/ranking and the complete prelabel freeze may
    # promoted-parent outputs and shower truth enter evaluation.
    req(sha(a.parent_result_json) == PARENT_RESULT_SHA, "promoted parent result changed")
    req(sha(a.parent_prelabel_json) == PARENT_PRELABEL_SHA, "promoted parent prelabel changed")
    parent_result = json.loads(a.parent_result_json.read_text())
    parent_prelabel = json.loads(a.parent_prelabel_json.read_text())
    req(parent_result["verdict"] == "PASS_RECURRENT_EOM_HDBSCAN_V1_GMN_DEVELOPMENT", "promoted parent no longer PASS")
    req(parent_result["events_by_year"] == {"2022": len(ids22), "2023": len(ids23)}, "current GMN event counts differ from promoted parent")
    parent_candidates = list(parent_prelabel["successor_candidates"])

    hidden = hidden_sealed
    ids_by_year = {2022: set(ids22), 2023: set(ids23)}
    req(all(eid in ids_by_year[2022] or eid in ids_by_year[2023] for eid in hidden), "label outside pooled accessible event IDs")

    reproduced_parent_metrics = {str(y): parent.metrics(parent_candidates, hidden, ids_by_year[y]) for y in YEARS}
    req(reproduced_parent_metrics == parent_result["successor_metrics"], "promoted recurrent-EOM metrics failed exact reproduction")
    successor_metrics = {str(y): parent.metrics(candidates, hidden, ids_by_year[y]) for y in YEARS}
    annual_gates = {str(y): parent.annual_gate(reproduced_parent_metrics[str(y)], successor_metrics[str(y)]) for y in YEARS}
    strict_100 = any(
        int(successor_metrics[str(y)]["recovered_at_100"]) > int(reproduced_parent_metrics[str(y)]["recovered_at_100"])
        for y in YEARS
    )
    parent_membership_order = [tuple(str(x) for x in c["event_ids"]) for c in parent_candidates]
    successor_membership_order = [tuple(str(x) for x in c["event_ids"]) for c in candidates]
    mechanism_active = bool(candidates) and successor_membership_order != parent_membership_order
    passed = bool(strict_100 and mechanism_active and all(all(g.values()) for g in annual_gates.values()))
    verdict = "PASS_RECIPROCAL_TRANSFER_HDBSCAN_V1_GMN_DEVELOPMENT" if passed else "FAIL_RECIPROCAL_TRANSFER_HDBSCAN_V1_GMN_DEVELOPMENT"

    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_DEVELOPMENT_ONLY",
        "prelabel_sha256": prelabel_sha,
        "events_total": len(ids22) + len(ids23),
        "events_by_year": {"2022": len(ids22), "2023": len(ids23)},
        "parent_result_sha256": PARENT_RESULT_SHA,
        "parent_prelabel_sha256": PARENT_PRELABEL_SHA,
        "parent_metrics_exactly_reproduced": True,
        "parent_candidate_count": len(parent_candidates),
        "successor_candidate_count": len(candidates),
        "native_cluster_count": {"2022": len(successor.persistence_2022), "2023": len(successor.persistence_2023)},
        "mechanism_active": mechanism_active,
        "strict_recovered_at_100_improvement_some_year": strict_100,
        "parent_metrics": reproduced_parent_metrics,
        "successor_metrics": successor_metrics,
        "annual_gates": annual_gates,
        "frozen_hdbscan": prelabel["frozen_hdbscan"],
        "strict_majority_rule": prelabel["strict_majority_rule"],
        "prediction_probabilities_used_for_matching": False,
        "prediction_probabilities_used_for_ranking": False,
        "majority_fractions_used_for_ranking": False,
        "synthetic_audit_run": SYNTHETIC_AUDIT_RUN,
        "synthetic_audit_artifact": SYNTHETIC_AUDIT_ARTIFACT,
        "synthetic_audit_result_sha256": SYNTHETIC_AUDIT_RESULT_SHA,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "amos_scientific_access": False,
        "efn_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "post_result_parameter_search": False,
    }
    result_path = a.output / "RECIPROCAL_TRANSFER_HDBSCAN_V1_GMN_DEVELOPMENT.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "verdict": verdict,
        "mechanism_active": mechanism_active,
        "parent": {y: metric_core(reproduced_parent_metrics[y]) for y in reproduced_parent_metrics},
        "successor": {y: metric_core(successor_metrics[y]) for y in successor_metrics},
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
