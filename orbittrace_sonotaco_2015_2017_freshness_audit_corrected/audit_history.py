#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

CANDIDATE_YEARS = (2015, 2017)
POSITIVE_CONTROL_YEAR = 2016
YEARS = CANDIDATE_YEARS + (POSITIVE_CONTROL_YEAR,)
RESERVATION_WORDS = (
    "untouched", "reserved", "not accessed", "no performance access",
    "does not authorize", "must not be accessed", "prospective reservation",
)


def run(*args: str) -> str:
    return subprocess.check_output(args, text=True, errors="replace")


def changed_paths(commit: str) -> list[str]:
    text = run("git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit)
    return [line.strip() for line in text.splitlines() if line.strip()]


def is_provenance_audit_path(path: str) -> bool:
    lower = path.lower()
    return "freshness_audit" in lower or "freshness-audit" in lower


def branch_names() -> list[str]:
    text = run("git", "for-each-ref", "--format=%(refname:short)", "refs/remotes/origin", "refs/heads")
    return sorted(set(line.strip() for line in text.splitlines() if line.strip()))


def grep_commits(pattern: str, *, include_audit_paths: bool) -> list[dict[str, object]]:
    raw = run("git", "log", "--all", "--format=%H", "-i", "-G", pattern)
    rx = re.compile(pattern, re.I)
    out = []
    for sha in dict.fromkeys(line.strip() for line in raw.splitlines() if line.strip()):
        paths = changed_paths(sha)
        if include_audit_paths:
            paths = [p for p in paths if is_provenance_audit_path(p)]
        else:
            paths = [p for p in paths if not is_provenance_audit_path(p)]
        if not paths:
            continue
        diff = run("git", "show", "--format=", "--no-ext-diff", "--unified=0", sha, "--", *paths)
        matches = [line[:700] for line in diff.splitlines() if rx.search(line)][:30]
        if not matches:
            continue
        out.append({
            "sha": sha,
            "subject": run("git", "show", "-s", "--format=%s", sha).strip(),
            "paths": paths[:80],
            "matches": matches,
        })
    return out


def audit_year(year: int, branches: list[str]) -> dict[str, object]:
    yy = year % 100
    exact_patterns = {
        "archive_zip": rf"{yy:03d}a\.zip",
        "archive_path": rf"SNMv3/{yy:03d}",
        "archive_member": rf"{yy:03d}a/[^\n]*{year}",
        "parser_symbol": rf"parse_sonotaco_{year}",
        "event_id": rf"SNM{year}:",
        "year_specific_result": rf"SONOTACO_{year}[^\n]*(RESULT|PROSPECTIVE|VALIDATION|CONFIRMATION)",
        "year_specific_source": rf"sonotaco[-_]{year}[^\n]*(parser|confirmation|validation|prospective|source)",
    }

    exact_hits = {}
    ignored_audit_hits = {}
    for name, pattern in exact_patterns.items():
        exact_hits[name] = grep_commits(pattern, include_audit_paths=False)
        ignored_audit_hits[name] = grep_commits(pattern, include_audit_paths=True)

    semantic_patterns = (
        rf"sonotaco[^\n]{{0,60}}{year}",
        rf"{year}[^\n]{{0,60}}sonotaco",
    )
    semantic_hits = []
    audit_semantic_hits = []
    for pattern in semantic_patterns:
        semantic_hits.extend(grep_commits(pattern, include_audit_paths=False))
        audit_semantic_hits.extend(grep_commits(pattern, include_audit_paths=True))

    def dedupe(hits: list[dict[str, object]]) -> list[dict[str, object]]:
        uniq = {}
        for hit in hits:
            uniq[(str(hit["sha"]), tuple(str(x) for x in hit["matches"]))] = hit
        return list(uniq.values())

    semantic_hits = dedupe(semantic_hits)
    audit_semantic_hits = dedupe(audit_semantic_hits)

    reservation_only = []
    ambiguous_semantic = []
    for hit in semantic_hits:
        joined = " ".join(str(x).lower() for x in hit["matches"])
        if any(word in joined for word in RESERVATION_WORDS):
            reservation_only.append(hit)
        else:
            ambiguous_semantic.append(hit)

    sonotaco_year_branches = []
    ignored_audit_branches = []
    for branch in branches:
        lower = branch.lower()
        if "sonotaco" not in lower or str(year) not in lower:
            continue
        if "freshness-audit" in lower or "freshness_audit" in lower:
            ignored_audit_branches.append(branch)
        else:
            sonotaco_year_branches.append(branch)

    exact_commit_shas = sorted({hit["sha"] for hits in exact_hits.values() for hit in hits})
    prior_access_found = bool(exact_commit_shas or sonotaco_year_branches)
    return {
        "prior_actual_access_found": prior_access_found,
        "classification": "EXPOSED" if prior_access_found else "NO_ACTUAL_ACCESS_FOUND_IN_REPO_HISTORY",
        "exact_access_commit_count": len(exact_commit_shas),
        "matching_sonotaco_year_branches": sorted(sonotaco_year_branches),
        "exact_access_hits": exact_hits,
        "reservation_only_mentions": reservation_only,
        "ambiguous_semantic_mentions": ambiguous_semantic,
        "ignored_provenance_audit_hits": ignored_audit_hits,
        "ignored_provenance_audit_semantic_mentions": audit_semantic_hits,
        "ignored_provenance_audit_branches": sorted(ignored_audit_branches),
    }


def main() -> None:
    out = Path("output")
    out.mkdir(exist_ok=True)
    branches = branch_names()
    years = {str(year): audit_year(year, branches) for year in YEARS}

    positive_control_detected = bool(years[str(POSITIVE_CONTROL_YEAR)]["prior_actual_access_found"])
    candidates_clean = all(not years[str(year)]["prior_actual_access_found"] for year in CANDIDATE_YEARS)
    verdict = (
        "PASS_CORRECTED_SONOTACO_2015_2017_REPO_FRESHNESS_AUDIT"
        if positive_control_detected and candidates_clean
        else "FAIL_CORRECTED_SONOTACO_2015_2017_REPO_FRESHNESS_AUDIT"
    )
    result = {
        "verdict": verdict,
        "candidate_years": list(CANDIDATE_YEARS),
        "positive_control_year": POSITIVE_CONTROL_YEAR,
        "positive_control_detected": positive_control_detected,
        "catalogue_access": False,
        "scientific_score_access": False,
        "shower_label_access": False,
        "excluded_interval_access": False,
        "target_information_access": False,
        "implementation_correction": (
            "Freshness/provenance-audit paths are excluded from actual data-access classification but their hits remain serialized separately."
        ),
        "years": years,
        "interpretation_rule": (
            "Actual exposure requires an exact year-specific archive/member/parser/event-id/result/source marker in a non-freshness-audit path, "
            "or a non-freshness-audit SonotaCo+year branch. Reservation prose and provenance-audit code do not count as archive/data access."
        ),
    }
    (out / "corrected_sonotaco_2015_2017_freshness_audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
