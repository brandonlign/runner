#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

OUT = Path("output")
AUDIT_PREFIX = "orbittrace_adelaide_zero_data_freshness_audit_v1/"
WORKFLOW_PATH = ".github/workflows/orbittrace_adelaide_zero_data_freshness_audit_v1.yml"
CURRENT_BRANCH = "agent/orbittrace-adelaide-zero-data-freshness-audit-v1"
PATTERNS = (
    r"Adelaide",
    r"ade6061",
    r"ade6869",
    r"Adelaide radar",
    r"Adelaide Meteor",
    r"ade6061\.tab",
    r"ade6869\.tab",
)
POSITIVE = ("FRIPON", "UKMON")


def run(*args: str) -> str:
    return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT)


def historical_hits(pattern: str) -> list[dict[str, str]]:
    cmd = [
        "git", "log", "--all", "-i", f"-G{pattern}",
        "--pretty=format:COMMIT:%H", "--name-only", "--",
        ".", f":!{AUDIT_PREFIX}", f":!{WORKFLOW_PATH}",
    ]
    text = run(*cmd)
    hits: list[dict[str, str]] = []
    commit = ""
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("COMMIT:"):
            commit = line.split(":", 1)[1]
        elif line and commit:
            hits.append({"commit": commit, "path": line})
    seen = set()
    out = []
    for hit in hits:
        key = (hit["commit"], hit["path"])
        if key not in seen:
            seen.add(key)
            out.append(hit)
    return out


def ref_hits() -> list[str]:
    refs = run("git", "for-each-ref", "--format=%(refname)", "refs/heads", "refs/remotes", "refs/tags").splitlines()
    rx = re.compile("|".join(f"(?:{p})" for p in PATTERNS), re.I)
    return sorted({ref for ref in refs if CURRENT_BRANCH not in ref and rx.search(ref)})


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    hits = {pattern: historical_hits(pattern) for pattern in PATTERNS}
    positives = {pattern: historical_hits(re.escape(pattern)) for pattern in POSITIVE}
    refs = ref_hits()
    any_adelaide = any(hits[p] for p in PATTERNS) or bool(refs)
    positive_ok = all(bool(positives[p]) for p in POSITIVE)
    passed = (not any_adelaide) and positive_ok
    result = {
        "stage": "ADELAIDE_ZERO_DATA_REPO_FRESHNESS_AUDIT_V1",
        "verdict": "PASS_ADELAIDE_ZERO_DATA_REPO_FRESHNESS_AUDIT" if passed else "FAIL_ADELAIDE_ZERO_DATA_REPO_FRESHNESS_AUDIT",
        "adelaide_history_hits": hits,
        "adelaide_ref_hits": refs,
        "positive_control_hits": positives,
        "positive_controls_pass": positive_ok,
        "network_access": False,
        "adelaide_catalogue_access": False,
        "adelaide_label_access": False,
        "adelaide_event_value_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "claim_boundary": "A pass authorizes only a separately frozen official-PDS metadata/label-only audit before any Adelaide scientific table access.",
    }
    path = OUT / "ADELAIDE_ZERO_DATA_REPO_FRESHNESS_AUDIT_V1.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
