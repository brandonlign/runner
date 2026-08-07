#!/usr/bin/env python3
"""Zero-data full-remote-ref freshness audit for Harvard Radar 1968/1969.

This script contacts only git remote branch history already present in the repository.
It never contacts a meteor catalogue or opens meteor data.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

OUT = Path("output")
OUT.mkdir(exist_ok=True)

TERMS = (
    "har6869",
    "Harvard Radar Meteor Project",
    "Harvard 1968-1969",
    "Harvard 1968–1969",
    "EAR-A-VARGBDET-5-METORB-V1.0",
    "meteoroid.steel.orbits",
    "Steel Meteoroid Orbits",
    "Meteoroid Orbits V1.0",
)
SELF_PREFIXES = (
    "orbittrace_harvard_1968_1969_freshness_audit/",
    ".github/workflows/orbittrace-harvard-1968-1969-freshness-audit",
)
POSITIVE_PATHS = {
    "amor_external_history_detected": "orbittrace_v8_amor_1996_1998_external/",
    "ukmon_external_history_detected": "orbittrace_label_free_v6_ukmon_2024_2025_external/",
}


def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, capture_output=True, check=check, errors="replace")


def refs() -> list[str]:
    p = run(["git", "for-each-ref", "--format=%(refname)", "refs/remotes/origin"])
    return [x for x in p.stdout.splitlines() if x and not x.endswith("/HEAD")]


def grep_ref(ref: str) -> list[dict]:
    args = ["git", "grep", "-n", "-I", "-F"]
    for term in TERMS:
        args += ["-e", term]
    args += [ref, "--"]
    p = run(args, check=False)
    if p.returncode not in (0, 1):
        raise RuntimeError(p.stderr)
    prefix = ref + ":"
    hits = []
    for raw in p.stdout.splitlines():
        if not raw.startswith(prefix):
            continue
        rest = raw[len(prefix):]
        try:
            path, line_s, text = rest.split(":", 2)
            line = int(line_s)
        except Exception:
            continue
        if path.startswith(SELF_PREFIXES):
            continue
        matched = [term for term in TERMS if term in text]
        hits.append({
            "ref": ref,
            "path": path,
            "line": line,
            "text": text[:1600],
            "matched_terms": matched,
        })
    return hits


def positive_controls(rs: list[str]) -> dict[str, bool]:
    found = {k: False for k in POSITIVE_PATHS}
    for ref in rs:
        p = run(["git", "ls-tree", "-r", "--name-only", ref], check=False)
        if p.returncode != 0:
            continue
        paths = p.stdout.splitlines()
        for key, prefix in POSITIVE_PATHS.items():
            if any(path.startswith(prefix) for path in paths):
                found[key] = True
    return found


def dedup(rows: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for row in rows:
        key = (row["path"], row["line"], row["text"])
        if key not in seen:
            seen.add(key)
            out.append(row)
    return out


def main() -> int:
    rs = refs()
    all_hits: list[dict] = []
    for ref in rs:
        all_hits.extend(grep_ref(ref))
    hits = dedup(all_hits)
    controls = positive_controls(rs)
    passed = (not hits) and all(controls.values())
    verdict = (
        "PASS_HARVARD_1968_1969_REPO_SCIENTIFIC_FRESHNESS_AUDIT"
        if passed else
        "FAIL_HARVARD_1968_1969_REPO_SCIENTIFIC_FRESHNESS_AUDIT"
    )
    result = {
        "verdict": verdict,
        "refs_scanned": len(rs),
        "candidate": "Harvard Radar Meteor Project 1968-1969 / har6869.tab",
        "fixed_search_terms": list(TERMS),
        "potential_exposure_hit_count": len(hits),
        "potential_exposure_hits": hits,
        "positive_controls": controls,
        "catalogue_contacted": False,
        "scientific_record_access": False,
        "source_label_access": False,
        "orbittrace_target_information_access": False,
        "claim_boundary": (
            "Full remote-branch repository-history freshness audit only. The selected Harvard 1968-1969 candidate was chosen from public catalogue metadata before this audit. "
            "No NASA/PDS/SBN/IAU meteor endpoint or scientific event table was contacted or opened. A pass authorizes a separately frozen structure/interface audit only."
        ),
    }
    (OUT / "harvard_1968_1969_repo_freshness_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    if not passed:
        raise SystemExit(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
