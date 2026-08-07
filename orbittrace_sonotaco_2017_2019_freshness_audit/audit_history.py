#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

YEARS = (2017, 2019)
SELF_PATH_PREFIXES = (
    "orbittrace_sonotaco_2017_2019_freshness_audit/",
    ".github/workflows/orbittrace-sonotaco-2017-2019-freshness-audit.yml",
)
PATTERNS = {
    2017: [r"sonotaco[^\n]{0,40}2017", r"2017[^\n]{0,40}sonotaco", r"017a\.zip", r"SNMv3/017"],
    2019: [r"sonotaco[^\n]{0,40}2019", r"2019[^\n]{0,40}sonotaco", r"019a\.zip", r"SNMv3/019"],
}


def run(*args: str) -> str:
    return subprocess.check_output(args, text=True, errors="replace")


def commit_paths(commit: str) -> list[str]:
    text = run("git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit)
    return [line.strip() for line in text.splitlines() if line.strip()]


def self_only_commit(commit: str) -> bool:
    paths = commit_paths(commit)
    return bool(paths) and all(any(p == prefix or p.startswith(prefix) for prefix in SELF_PATH_PREFIXES) for p in paths)


def grep_commits(pattern: str) -> list[dict[str, object]]:
    # -G searches patch text across all reachable history. We inspect the exact
    # matching commit/path payload afterwards and ignore only this audit's own files.
    raw = run("git", "log", "--all", "--format=%H", "-i", "-G", pattern)
    commits = []
    for sha in dict.fromkeys(line.strip() for line in raw.splitlines() if line.strip()):
        if self_only_commit(sha):
            continue
        subject = run("git", "show", "-s", "--format=%s", sha).strip()
        paths = commit_paths(sha)
        nonself = [p for p in paths if not any(p == prefix or p.startswith(prefix) for prefix in SELF_PATH_PREFIXES)]
        # Capture only textual diff lines containing the pattern, bounded to make
        # the audit artifact compact. This is provenance, not scientific data.
        diff = run("git", "show", "--format=", "--no-ext-diff", "--unified=0", sha, "--", *nonself) if nonself else ""
        rx = re.compile(pattern, re.I)
        matches = []
        for line in diff.splitlines():
            if rx.search(line):
                matches.append(line[:500])
                if len(matches) >= 20:
                    break
        commits.append({"sha": sha, "subject": subject, "paths": nonself[:50], "matches": matches})
    return commits


def branch_hits(year: int) -> list[str]:
    names = run("git", "for-each-ref", "--format=%(refname:short)", "refs/remotes/origin", "refs/heads")
    result = []
    for name in names.splitlines():
        lower = name.lower()
        if str(year) in lower and "sonotaco" in lower:
            result.append(name.strip())
    return sorted(set(result))


def main() -> None:
    out = Path("output")
    out.mkdir(exist_ok=True)
    result: dict[str, object] = {
        "verdict": None,
        "catalogue_access": False,
        "scientific_score_access": False,
        "target_information_access": False,
        "years": {},
    }
    clean = True
    for year in YEARS:
        pattern_results = {}
        all_commits = set()
        for pattern in PATTERNS[year]:
            hits = grep_commits(pattern)
            pattern_results[pattern] = hits
            all_commits.update(h["sha"] for h in hits)
        branches = branch_hits(year)
        # A branch name counts only when it explicitly combines SonotaCo + year.
        exposed = bool(all_commits or branches)
        clean = clean and not exposed
        result["years"][str(year)] = {
            "prior_sonotaco_exposure_found": exposed,
            "matching_commit_count": len(all_commits),
            "matching_sonotaco_year_branches": branches,
            "pattern_results": pattern_results,
        }
    result["verdict"] = (
        "PASS_SONOTACO_2017_2019_REPO_FRESHNESS_AUDIT"
        if clean
        else "FAIL_SONOTACO_2017_2019_REPO_FRESHNESS_AUDIT"
    )
    Path("output/sonotaco_2017_2019_freshness_audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
