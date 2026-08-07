#!/usr/bin/env python3
"""Full-repository zero-data freshness audit for reserved FRIPON 2018/2019."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

OUT = Path("output")
OUT.mkdir(exist_ok=True)
TARGET_YEARS = (2018, 2019)
SELF_PREFIXES = (
    "orbittrace_fripon_2018_2019_freshness_audit/",
    ".github/workflows/orbittrace-fripon-2018-2019-freshness-audit",
)
FRIPON_GREP = (
    r"FRIPON|Fireball Recovery and InterPlanetary Observation Network|"
    r"fireball\.fripon\.org|fripon_detections"
)
YEAR_LITERAL = re.compile(r"(?<!\d)(2018|2019)(?!\d)")
DATA_MARKERS = re.compile(
    r"fireball\.fripon\.org|"
    r"(?:list|display)_?multiple\.php|list_pipeline\.php|"
    r"fripon_detections|RadianRA|RadianDec|trajectory\s+VE|"
    r"multiple\s+id|pipeline\s+content|FRIPON\s+Data\s+release|"
    r"FRIPON[^\n]{0,80}(?:download|parser|API|database\s+web\s+frontend)",
    re.I,
)
PATH_EXPOSURE = re.compile(
    r"fripon.*(?:external|validation|parser|catalog|catalogue|data|interface|scientific|event)",
    re.I,
)


def run(*args: str) -> str:
    return subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL)


def refs() -> list[str]:
    return [
        x
        for x in run(
            "git", "for-each-ref", "--format=%(refname)", "refs/remotes/origin"
        ).splitlines()
        if x and not x.endswith("/HEAD")
    ]


def fripon_paths(ref: str) -> set[str]:
    p = subprocess.run(
        ["git", "grep", "-l", "-I", "-i", "-E", FRIPON_GREP, ref, "--"],
        text=True,
        capture_output=True,
    )
    if p.returncode not in (0, 1):
        raise RuntimeError(p.stderr)
    prefix = ref + ":"
    paths: set[str] = set()
    for line in p.stdout.splitlines():
        if not line.startswith(prefix):
            continue
        path = line[len(prefix) :]
        if path.startswith(SELF_PREFIXES):
            continue
        paths.add(path)
    return paths


def file_text(ref: str, path: str) -> str:
    p = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        text=True,
        capture_output=True,
        errors="replace",
    )
    return p.stdout if p.returncode == 0 else ""


def classify(ref: str, path: str, text: str) -> tuple[list[dict], list[dict]]:
    potential: list[dict] = []
    bibliography: list[dict] = []
    lines = text.splitlines()

    for i, line in enumerate(lines, 1):
        if YEAR_LITERAL.search(line):
            potential.append(
                {
                    "ref": ref,
                    "path": path,
                    "line": i,
                    "text": line[:1200],
                    "reason": "reserved_year_literal_in_FRIPON_related_file",
                }
            )
        if DATA_MARKERS.search(line):
            potential.append(
                {
                    "ref": ref,
                    "path": path,
                    "line": i,
                    "text": line[:1200],
                    "reason": "explicit_FRIPON_event_or_data_access_marker",
                }
            )

    if PATH_EXPOSURE.search(path):
        potential.append(
            {
                "ref": ref,
                "path": path,
                "line": 0,
                "text": "",
                "reason": "FRIPON_scientific_or_data_path",
            }
        )

    if not potential:
        snippets = [
            {"line": i, "text": line[:600]}
            for i, line in enumerate(lines, 1)
            if re.search(r"FRIPON|Fireball Recovery", line, re.I)
        ][:10]
        bibliography.append(
            {
                "ref": ref,
                "path": path,
                "classification": "generic_FRIPON_reference_without_reserved_year_or_data_access_marker",
                "snippets": snippets,
            }
        )
    return potential, bibliography


def dedup(rows: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for row in rows:
        key = (row.get("path"), row.get("line"), row.get("reason"), row.get("text"))
        if key not in seen:
            seen.add(key)
            out.append(row)
    return out


def dedup_bib(rows: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for row in rows:
        key = row["path"]
        if key not in seen:
            seen.add(key)
            out.append(row)
    return out


def main() -> int:
    rs = refs()
    potential: list[dict] = []
    bibliography: list[dict] = []
    occurrences = 0
    positive = {
        "spent_AMOR_external_ref_detected": any(
            "orbittrace-v8-amor-1996-1998-external" in r for r in rs
        ),
        "spent_UKMON_external_ref_detected": any(
            "orbittrace-label-free-v6-ukmon-2024-2025-external" in r for r in rs
        ),
    }

    for ref in rs:
        for path in fripon_paths(ref):
            occurrences += 1
            p, b = classify(ref, path, file_text(ref, path))
            potential.extend(p)
            bibliography.extend(b)

    potential = dedup(potential)
    bibliography = dedup_bib(bibliography)
    verdict = (
        "PASS_FRIPON_2018_2019_REPO_SCIENTIFIC_FRESHNESS_AUDIT"
        if not potential and all(positive.values())
        else "FAIL_FRIPON_2018_2019_REPO_SCIENTIFIC_FRESHNESS_AUDIT"
    )
    result = {
        "verdict": verdict,
        "candidate": "FRIPON",
        "reserved_years": [2018, 2019],
        "refs_scanned": len(rs),
        "fripon_related_file_occurrences_scanned": occurrences,
        "potential_exposure_hits": potential,
        "potential_exposure_hit_count": len(potential),
        "bibliographic_only_hits": bibliography,
        "bibliographic_only_file_count": len(bibliography),
        "positive_controls": positive,
        "catalogue_access_this_audit": False,
        "fripon_web_or_api_contacted": False,
        "scientific_value_access_this_audit": False,
        "event_identifier_access_this_audit": False,
        "label_access_this_audit": False,
        "orbittrace_target_information_access": False,
        "claim_boundary": (
            "Full remote-branch repository-history audit only. A pass reserves FRIPON 2018/2019 against prior OrbitTrace project use; it does not contact FRIPON and authorizes only a separately frozen pre-scientific structure/interface audit."
        ),
    }
    (OUT / "fripon_2018_2019_repo_freshness_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    if verdict.startswith("FAIL_"):
        raise SystemExit(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
