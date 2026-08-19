#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

PRETRUTH_SHA = "6ae27f985340eaa41870ab4c4f8cd15d6a1cd97e03ef828254f4c24d7896176a"
CPP_SHA = "4eef6f1b70b5baee5d1983d2480c02d73569b12af868ec23bbb6009d6ca1fa37"


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows-root", type=Path, required=True)
    ap.add_argument("--structural-source", type=Path, required=True)
    ap.add_argument("--support-pretruth", type=Path, required=True)
    ap.add_argument("--baseline-runner", type=Path, required=True)
    ap.add_argument("--exact-cpp", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    req(sha(a.support_pretruth) == PRETRUTH_SHA, "sealed support pretruth changed")
    req(sha(a.exact_cpp) == CPP_SHA, "exact M2D scorer changed")
    pre = json.loads(a.support_pretruth.read_text())
    req(pre.get("scientific_role") == "ZERO_LABEL_SUPPORT_PRUNED_SONOTACO_COMMON_UNIVERSE_PRETRUTH", "wrong support pretruth role")
    req(pre.get("truth_used") is False and pre.get("shower_labels_accessed") is False, "support pretruth firewall")
    req(pre.get("post_result_parameter_search") is False and pre.get("configuration", {}).get("new_tuned_parameters") == [], "post-result tuning")
    candidates = list(pre["candidates"])
    req(len(candidates) == int(pre["candidate_count"]) == 907, "candidate count changed")

    base = load(a.baseline_runner, "spc_sonotaco_rank_base")
    structural = load(a.structural_source, "spc_sonotaco_rank_structural")
    req(float(structural.RADIUS) == 1.0 and int(structural.MIN_SUPPORT) == 4, "structural constants")
    pooled, ids_by_year, universe = base.merge_common(a.rows_root)
    events = sorted([base.support_event(r) for r in pooled], key=lambda e: e["id"])
    req(len(events) == 29246 and universe["common_counts"] == {"2013": 15988, "2014": 13258}, "common universe changed")

    with tempfile.TemporaryDirectory() as td_s:
        td = Path(td_s)
        binp, scoresp, exe = td / "input.bin", td / "scores.tsv", td / "exact"
        raw, d13, d14, cand_of, idx = base.build_binary(events, candidates, structural, binp)
        subprocess.run(["g++", "-O3", "-std=c++17", str(a.exact_cpp), "-o", str(exe)], check=True)
        subprocess.run([str(exe), str(binp), str(scoresp)], check=True)
        scores = base.parse_scores(scoresp)
        req(len(scores) == len(candidates), "missing accelerator scores")
        n = len(candidates)
        audits = []
        for ci in sorted(set([0, n // 4, n // 2, (3 * n) // 4, n - 1])):
            brute = base.brute_candidate(ci, candidates, raw, d13, d14, cand_of, idx)
            exact = scores[ci]
            req(abs(brute - exact) <= 1e-18, f"accelerator audit mismatch {ci}: {brute} {exact}")
            audits.append({"candidate": ci, "brute": brute, "accelerated": exact, "abs_diff": abs(brute - exact)})

    ranked = []
    for ci, c in enumerate(candidates):
        row = dict(c)
        row["internal_2d_mass"] = float(scores[ci])
        ranked.append(row)
    ranked.sort(key=lambda r: (-float(r["internal_2d_mass"]), -float(r["modal_contrast"]), str(r["family_hash"])))
    for i, row in enumerate(ranked, 1):
        row["internal_mass_rank"] = i

    payload = {
        "schema": "ORBITTRACE_M2D_SUPPORT_PRUNED_CUT_V1_SONOTACO_RANKED_PRETRUTH",
        "scientific_role": "ZERO_LABEL_EXACT_M2D_RANKING_OF_SEALED_SUPPORT_PRUNED_CANDIDATES",
        "universe": universe,
        "candidate_count": len(ranked),
        "candidates": ranked,
        "accelerator_audit": audits,
        "support_pretruth_sha256": PRETRUTH_SHA,
        "exact_cpp_sha256": CPP_SHA,
        "truth_artifact_downloaded": False,
        "truth_used": False,
        "shower_labels_accessed": False,
        "post_result_parameter_search": False,
    }
    out = a.output / "M2D_SUPPORT_PRUNED_CUT_V1_SONOTACO_RANKED_PRETRUTH.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"verdict": "M2D_RANKING_SEALED_AWAITING_TRUTH", "candidate_count": len(ranked), "sha256": sha(out), "top10": [{"rank": r["internal_mass_rank"], "members": r["member_count"], "m2d": r["internal_2d_mass"], "family_hash": r["family_hash"]} for r in ranked[:10]]}, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
