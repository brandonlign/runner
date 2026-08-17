#!/usr/bin/env python3
from __future__ import annotations
import argparse, copy, hashlib, json
from pathlib import Path

ORIGINAL_PRELABEL_SHA256 = "95f8a57718a30b2c7e85016d505276d72cccb9e4ac1d6eb29f13067efc73dd0c"
EXPECTED_SCHEMA = "ORBITTRACE_ANNUAL_DENSITY_BIFILTRATION_GMN_RANKING_V1_PRELABEL"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_projection(obj):
    """Return the complete scientific payload with evaluator-only family_id removed."""
    out = copy.deepcopy(obj)
    for subset in out["subsets"]:
        for row in subset["recurrent_candidates"]:
            row.pop("family_id", None)
        for row in subset["bifiltration_candidates"]:
            row.pop("family_id", None)
    return out


def dump(path: Path, obj) -> str:
    raw=(json.dumps(obj, indent=2, sort_keys=True, allow_nan=False)+"\n").encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    a=ap.parse_args()

    original_sha=sha256(a.input)
    if original_sha != ORIGINAL_PRELABEL_SHA256:
        raise RuntimeError(f"original prelabel SHA mismatch: {original_sha}")
    src=json.loads(a.input.read_text())
    if src.get("schema") != EXPECTED_SCHEMA:
        raise RuntimeError("wrong prelabel schema")
    if src.get("shower_truth_used") is not False:
        raise RuntimeError("original prelabel truth flag changed")

    adapted=copy.deepcopy(src)
    added=0
    for subset in adapted["subsets"]:
        d=int(subset["denominator"]); b=int(subset["bucket"])
        for rank,row in enumerate(subset["bifiltration_candidates"],1):
            if "family_id" in row:
                raise RuntimeError("bifiltration row unexpectedly already has family_id")
            # Evaluator adapter only. parent.metrics copies this field but truth() never reads it.
            row["family_id"] = f"BIF_D{d}_B{b}_R{rank}_{row['family_hash']}"
            added += 1

    # Prove the repair changes no scientific field, membership, order, budget, or comparator row.
    if canonical_projection(adapted) != canonical_projection(src):
        raise RuntimeError("repair changed scientific payload")
    for s0,s1 in zip(src["subsets"], adapted["subsets"]):
        if int(s0["equal_budget_k"]) != int(s1["equal_budget_k"]):
            raise RuntimeError("K changed")
        if s0["recurrent_candidates"] != s1["recurrent_candidates"]:
            raise RuntimeError("recurrent comparator changed")
        for r0,r1 in zip(s0["bifiltration_candidates"],s1["bifiltration_candidates"]):
            if r0["event_ids"] != r1["event_ids"] or r0["rank"] != r1["rank"] or r0["family_hash"] != r1["family_hash"]:
                raise RuntimeError("bifiltration membership/order changed")

    adapted_sha=dump(a.output, adapted)
    report={
      "schema":"ORBITTRACE_BIFILTRATION_GMN_RANKING_V1_ENGINEERING_REPAIR1",
      "scientific_change":False,
      "repair":"add evaluator-only family_id to frozen bifiltration rows",
      "original_run_id":32037435314,
      "original_prelabel_artifact_id":9291169452,
      "original_prelabel_artifact_digest":"sha256:af497634e100883b0448737465e27b4e523ffa85f48979c829125e95acfc58ac",
      "original_prelabel_sha256":original_sha,
      "adapted_prelabel_sha256":adapted_sha,
      "family_ids_added":added,
      "memberships_changed":False,
      "candidate_order_changed":False,
      "equal_budgets_changed":False,
      "comparator_changed":False,
      "truth_used_by_repair":False,
    }
    dump(a.report, report)
    print(json.dumps(report,indent=2,sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
