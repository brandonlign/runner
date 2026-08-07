#!/usr/bin/env python3
"""Conservative zero-data full-remote-ref freshness audit for Hissar 1968/1969."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

OUT = Path("output")
OUT.mkdir(exist_ok=True)
TERMS = (
    "Hissar", "HISSAR", "Hisar", "Dushanbe", "Narziev",
    "8916 radio-meteor", "8,916 radio-meteor",
    "1968-1969 sample of HISSAR", "1968-1969 sample of Hissar",
)
SELF = (
    "orbittrace_hissar_1968_1969_freshness_audit/",
    ".github/workflows/orbittrace-hissar-1968-1969-freshness-audit",
)
POSITIVE_PATHS = {
    "amor_history_detected": "orbittrace_v8_amor_1996_1998_external/",
    "ukmon_history_detected": "orbittrace_label_free_v6_ukmon_2024_2025_external/",
    "harvard_history_detected": "orbittrace_harvard_1968_1969_structure_audit/",
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
    rows = []
    for raw in p.stdout.splitlines():
        if not raw.startswith(prefix):
            continue
        rest = raw[len(prefix):]
        try:
            path, line_s, text = rest.split(":", 2)
            line = int(line_s)
        except Exception:
            continue
        if path.startswith(SELF):
            continue
        rows.append({
            "ref": ref,
            "path": path,
            "line": line,
            "text": text[:1800],
            "matched_terms": [t for t in TERMS if t in text],
        })
    return rows


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
    seen = set(); out = []
    for row in rows:
        key = (row["path"], row["line"], row["text"])
        if key not in seen:
            seen.add(key); out.append(row)
    return out


def main() -> int:
    rs = refs()
    hits = dedup([row for ref in rs for row in grep_ref(ref)])
    controls = positive_controls(rs)
    passed = (not hits) and all(controls.values())
    verdict = (
        "PASS_HISSAR_1968_1969_REPO_SCIENTIFIC_FRESHNESS_AUDIT"
        if passed else "FAIL_HISSAR_1968_1969_REPO_SCIENTIFIC_FRESHNESS_AUDIT"
    )
    result = {
        "verdict": verdict,
        "refs_scanned": len(rs),
        "candidate": "IAU MDC Hissar/Hisar radio-meteor sample 1968-1969",
        "fixed_search_terms": list(TERMS),
        "potential_exposure_hit_count": len(hits),
        "potential_exposure_hits": hits,
        "positive_controls": controls,
        "iau_mdc_contacted": False,
        "catalogue_form_submitted": False,
        "scientific_record_access": False,
        "source_label_access": False,
        "orbittrace_target_information_access": False,
        "claim_boundary": (
            "Conservative full-remote-ref repository-history audit only. Any textual Hissar/Hisar/Dushanbe marker outside this audit is reported as a raw hit, including metadata-only mentions. "
            "A raw FAIL may be semantically adjudicated in a separate zero-data stage but must remain preserved. No IAU MDC endpoint or meteor row is contacted here."
        ),
    }
    (OUT / "hissar_1968_1969_repo_freshness_audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    if not passed:
        raise SystemExit(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
