#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

from orbittrace_ecdf_recurrent_rank_hdbscan_v1.ecdf_rank import canonical_membership, rank_candidates

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
QUALITY_SHA = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
PARENT_RESULT_SHA = "433c641f57122b244b9476f5cbcb5e6f82956d9467270a9f24945600a32d2106"
PARENT_PRELABEL_SHA = "e304f6660697ed27a7e2e546ba2b9f2ecdb43f923745cb7424a3781ad55b9ad1"
SYNTHETIC_AUDIT_RUN = 31850982974
SYNTHETIC_AUDIT_ARTIFACT = 9237498759
SYNTHETIC_AUDIT_RESULT_SHA = "f413de74a568eebadd549276d30e70bf1d171dbebc17447e0ba1ebf8c8db3dec"
PROTOCOL_BLOB = "2b8329afbcd16b4ac5afb1f35260ee87e7212bb6"
RANKER_BLOB = "89601baf31a133d93409c57961baa57e9203c09f"


def req(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_parent_helpers() -> Any:
    root = Path(__file__).resolve().parents[1]
    parent_dir = root / "orbittrace_recurrent_eom_hdbscan_v1"
    runner = parent_dir / "run_development.py"
    req(runner.exists(), "promoted recurrent-EOM runner missing")
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    spec = importlib.util.spec_from_file_location("ecdf_rank_parent_helpers", runner)
    req(spec is not None and spec.loader is not None, "cannot load promoted recurrent-EOM runner")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def metric_core(row: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in row.items() if k != "first_rank_by_label"}


def order_hash(rows: list[dict[str, Any]]) -> str:
    return hashlib.sha256(("\n".join(str(x["family_id"]) for x in rows) + "\n").encode()).hexdigest()


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
    req(tuple(parent.YEARS) == YEARS and tuple(parent.BLIND) == BLIND, "parent year/firewall pins drift")
    req(sha(a.quality_source) == QUALITY_SHA, "frozen GMN runtime utility changed")
    req(sha(a.v8_result_json) == V8_RESULT_SHA, "frozen GMN support artifact changed")
    req(sha(a.parent_prelabel_json) == PARENT_PRELABEL_SHA, "promoted parent prelabel changed")
    req(sha(a.parent_result_json) == PARENT_RESULT_SHA, "promoted parent result bytes changed")
    req(sha(a.synthetic_audit_json) == SYNTHETIC_AUDIT_RESULT_SHA, "synthetic audit receipt changed")

    audit = json.loads(a.synthetic_audit_json.read_text())
    req(audit["verdict"] == "PASS_ECDF_RECURRENT_RANK_HDBSCAN_V1_SYNTHETIC_AUDIT", "synthetic audit did not pass")
    req(all(audit["checks"].values()), "synthetic audit check failed")
    req(audit["gmn_accessed"] is False and audit["truth_accessed"] is False, "synthetic audit crossed data boundary")

    # Parent prelabel is explicitly label-free and is the only parent scientific
    # output read before the successor order is frozen.
    parent_prelabel = json.loads(a.parent_prelabel_json.read_text())
    req(parent_prelabel["scientific_role"] == "PRELABEL_FROZEN_RECURRENT_EOM_HDBSCAN_V1", "parent prelabel role changed")
    req(parent_prelabel["blind_exclusion"] == list(BLIND), "parent blind interval changed")
    req(parent_prelabel["target_information_access"] is False, "parent prelabel target access flag changed")
    req(parent_prelabel["target_region_events_accessed"] is False, "parent prelabel target-region flag changed")

    qmod = parent.load_module(a.quality_source, "ecdf_rank_frozen_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-ecdf-recurrent-rank-hdbscan-v1-development-2022-2023-target-excluded"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden_sealed, sources = support.parse_catalogue(base)
    req(sorted(scan) == list(YEARS), f"GMN runtime accessed wrong years: {sorted(scan)}")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "GMN source list changed")

    ids_by_year: dict[int, set[str]] = {}
    for year in YEARS:
        raw = list(scan[year])
        rows = [parent.normalize_event(row, year) for row in raw]
        req(len(rows) == len(raw), f"event normalization changed {year} event count")
        ids = {str(e["id"]) for e in rows}
        req(len(ids) == len(rows), f"duplicate accessible event IDs in {year}")
        ids_by_year[year] = ids
    req(not ids_by_year[2022].intersection(ids_by_year[2023]), "annual accessible ID sets overlap")
    req(parent_prelabel["events_by_year"] == {"2022": len(ids_by_year[2022]), "2023": len(ids_by_year[2023])}, "current GMN event counts differ from promoted parent")

    parent_candidates = [dict(x) for x in parent_prelabel["successor_candidates"]]
    annual = {int(k): tuple(float(v) for v in vals) for k, vals in parent_prelabel["annual_recurrent_stability"].items()}
    successor_candidates = rank_candidates(parent_candidates, annual)

    req(canonical_membership(successor_candidates) == canonical_membership(parent_candidates), "ECDF ranker changed parent candidate membership")
    all_accessible_ids = ids_by_year[2022] | ids_by_year[2023]
    req(all(str(eid) in all_accessible_ids for c in successor_candidates for eid in c["event_ids"]), "candidate contains non-accessible event")
    parent_order_sha = order_hash(parent_candidates)
    successor_order_sha = order_hash(successor_candidates)
    mechanism_active = successor_order_sha != parent_order_sha

    prelabel = {
        "scientific_role": "PRELABEL_FROZEN_ECDF_RECURRENT_RANK_HDBSCAN_V1",
        "events_by_year": {"2022": len(ids_by_year[2022]), "2023": len(ids_by_year[2023])},
        "parent_prelabel_sha256": PARENT_PRELABEL_SHA,
        "parent_candidate_count": len(parent_candidates),
        "successor_candidate_count": len(successor_candidates),
        "candidate_membership_exactly_identical": True,
        "parent_order_sha256": parent_order_sha,
        "successor_order_sha256": successor_order_sha,
        "mechanism_active": mechanism_active,
        "successor_candidates": successor_candidates,
        "ranking_rule": [
            "descending min(midrank ECDF annual EOM 2022, midrank ECDF annual EOM 2023)",
            "descending max(midrank ECDF annual EOM 2022, midrank ECDF annual EOM 2023)",
            "descending promoted-parent recurrent stability",
            "descending ordinary HDBSCAN stability",
            "descending member count",
            "ascending promoted-parent family ID",
        ],
        "protocol_git_blob": PROTOCOL_BLOB,
        "ranker_git_blob": RANKER_BLOB,
        "synthetic_audit_run": SYNTHETIC_AUDIT_RUN,
        "synthetic_audit_artifact": SYNTHETIC_AUDIT_ARTIFACT,
        "synthetic_audit_result_sha256": SYNTHETIC_AUDIT_RESULT_SHA,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "asfn_access": False,
        "amos_scientific_access": False,
        "efn_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    prelabel_path = a.output / "ECDF_RECURRENT_RANK_HDBSCAN_V1_PRELABEL.json"
    prelabel_path.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    prelabel_sha = sha(prelabel_path)

    # Truth-informed parent result and sealed GMN shower labels are read only
    # after the complete successor ordering has been persisted and hash-frozen.
    parent_result = json.loads(a.parent_result_json.read_text())
    req(parent_result["verdict"] == "PASS_RECURRENT_EOM_HDBSCAN_V1_GMN_DEVELOPMENT", "promoted parent no longer PASS")
    hidden = hidden_sealed
    reproduced_parent_metrics = {str(y): parent.metrics(parent_candidates, hidden, ids_by_year[y]) for y in YEARS}
    req(reproduced_parent_metrics == parent_result["successor_metrics"], "promoted recurrent-EOM metrics failed exact reproduction")
    successor_metrics = {str(y): parent.metrics(successor_candidates, hidden, ids_by_year[y]) for y in YEARS}
    annual_gates = {str(y): parent.annual_gate(reproduced_parent_metrics[str(y)], successor_metrics[str(y)]) for y in YEARS}
    strict_100 = any(
        int(successor_metrics[str(y)]["recovered_at_100"]) > int(reproduced_parent_metrics[str(y)]["recovered_at_100"])
        for y in YEARS
    )
    passed = bool(
        strict_100
        and mechanism_active
        and canonical_membership(successor_candidates) == canonical_membership(parent_candidates)
        and all(all(g.values()) for g in annual_gates.values())
    )
    verdict = "PASS_ECDF_RECURRENT_RANK_HDBSCAN_V1_GMN_DEVELOPMENT" if passed else "FAIL_ECDF_RECURRENT_RANK_HDBSCAN_V1_GMN_DEVELOPMENT"

    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_DEVELOPMENT_ONLY",
        "prelabel_sha256": prelabel_sha,
        "events_by_year": prelabel["events_by_year"],
        "parent_result_sha256": PARENT_RESULT_SHA,
        "parent_prelabel_sha256": PARENT_PRELABEL_SHA,
        "parent_metrics_exactly_reproduced": True,
        "parent_candidate_count": len(parent_candidates),
        "successor_candidate_count": len(successor_candidates),
        "candidate_membership_exactly_identical": True,
        "parent_order_sha256": parent_order_sha,
        "successor_order_sha256": successor_order_sha,
        "mechanism_active": mechanism_active,
        "strict_recovered_at_100_improvement_some_year": strict_100,
        "parent_metrics": reproduced_parent_metrics,
        "successor_metrics": successor_metrics,
        "annual_gates": annual_gates,
        "synthetic_audit_run": SYNTHETIC_AUDIT_RUN,
        "synthetic_audit_artifact": SYNTHETIC_AUDIT_ARTIFACT,
        "synthetic_audit_result_sha256": SYNTHETIC_AUDIT_RESULT_SHA,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "asfn_access": False,
        "amos_scientific_access": False,
        "efn_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "post_result_parameter_search": False,
    }
    result_path = a.output / "ECDF_RECURRENT_RANK_HDBSCAN_V1_GMN_DEVELOPMENT.json"
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
