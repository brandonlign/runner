#!/usr/bin/env python3
"""Full-repository provenance audit for SAAMER 2022/2023; no catalogue access."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

OUT = Path("output")
OUT.mkdir(exist_ok=True)
SELF_PREFIXES = (
    "orbittrace_saamer_2022_2023_freshness_audit/",
    ".github/workflows/orbittrace-saamer-2022-2023-freshness-audit",
)


def run(*args: str) -> str:
    return subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL)


def refs() -> list[str]:
    return [
        value for value in run("git", "for-each-ref", "--format=%(refname)", "refs/remotes/origin").splitlines()
        if value and not value.endswith("/HEAD")
    ]


def grep_ref(ref: str, pattern: str) -> list[dict]:
    proc = subprocess.run(["git", "grep", "-n", "-I", "-E", pattern, ref, "--"], text=True, capture_output=True)
    if proc.returncode not in (0, 1):
        raise RuntimeError(proc.stderr)
    prefix = ref + ":"
    result: list[dict] = []
    for line in proc.stdout.splitlines():
        if not line.startswith(prefix):
            continue
        parts = line[len(prefix):].split(":", 2)
        if len(parts) != 3:
            continue
        path, line_number, text = parts
        if path.startswith(SELF_PREFIXES):
            continue
        result.append({"ref": ref, "path": path, "line": int(line_number), "text": text[:1200]})
    return result


def dedup(rows: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for row in rows:
        key = (row["path"], row["line"], row["text"])
        if key not in seen:
            seen.add(key)
            out.append(row)
    return out


def collect(rs: list[str], patterns: list[str]) -> list[dict]:
    rows: list[dict] = []
    for ref in rs:
        for pattern in patterns:
            rows.extend(grep_ref(ref, pattern))
    return dedup(rows)


def main() -> int:
    rs = refs()

    # Candidate-year patterns are intentionally year-specific so the now-spent
    # SAAMER 2020/2021 external-validation work does not contaminate this audit.
    candidate_patterns = [
        r"iaumdcSAAMER2022|iaumdcSAAMER2023",
        r"SAA(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)2022\.dat",
        r"SAA(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)2023\.dat",
        r"SAAMER[^\n]{0,80}(2022|2023)|(2022|2023)[^\n]{0,80}SAAMER",
    ]
    candidate_hits = collect(rs, candidate_patterns)

    # Classification is deliberately strict. Bibliographic/general date prose may
    # be separated only when the text contains no candidate archive/member token,
    # no parser/result/data language, and no scientific-variable/value context.
    suspicious: list[dict] = []
    provenance_only: list[dict] = []
    archive_token = re.compile(r"iaumdcSAAMER202[23]|SAA(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)202[23]\.dat", re.I)
    science_token = re.compile(r"archive|download|parser|row|meteor|result|score|cluster|family|RA|DEC|\bLS\b|\bVg\b|\bq\b|\be\b|\bi\b|arg|nod", re.I)
    for hit in candidate_hits:
        text = hit["text"]
        if archive_token.search(text) or science_token.search(text):
            hit["classification"] = "potential_data_or_scientific_exposure"
            suspicious.append(hit)
        else:
            hit["classification"] = "provenance_or_bibliographic_only"
            provenance_only.append(hit)

    # Positive controls: the just-consumed 2020/2021 SAAMER pair must be detected
    # as actual scientific use, and SonotaCo 2023 remains an independent spent-survey control.
    spent_saamer = collect(rs, [
        r"iaumdcSAAMER2020|iaumdcSAAMER2021",
        r"SAAMER 2020-2021 external validation|SAAMER 2020–2021 external validation",
    ])
    spent_saamer_actual = any(
        "orbittrace_label_free_v6_saamer_external/" in hit["path"]
        or "orbittrace-label-free-v6-saamer-2020-2021-external" in hit["path"]
        for hit in spent_saamer
    )
    spent_sonotaco = collect(rs, [r"SNMv3/023a", r"sonotaco[^\n]{0,80}2023|2023[^\n]{0,80}sonotaco"])
    spent_sonotaco_actual = any(
        "sonotaco-2023" in hit["path"].lower() or "sonotaco_2023" in hit["path"].lower()
        for hit in spent_sonotaco
    )

    verdict = (
        "PASS_SAAMER_2022_2023_REPO_SCIENTIFIC_FRESHNESS_AUDIT"
        if not suspicious and spent_saamer_actual and spent_sonotaco_actual
        else "FAIL_SAAMER_2022_2023_REPO_SCIENTIFIC_FRESHNESS_AUDIT"
    )
    result = {
        "verdict": verdict,
        "refs_scanned": len(rs),
        "candidate_years": [2022, 2023],
        "candidate_hits": candidate_hits,
        "candidate_hit_count": len(candidate_hits),
        "potential_exposure_hits": suspicious,
        "potential_exposure_hit_count": len(suspicious),
        "provenance_or_bibliographic_hits": provenance_only,
        "catalogue_access_this_audit": False,
        "scientific_value_access_this_audit": False,
        "label_access_this_audit": False,
        "target_information_access": False,
        "positive_controls": {
            "saamer_2020_2021_spent_detected": spent_saamer_actual,
            "sonotaco_2023_spent_detected": spent_sonotaco_actual,
        },
        "claim_boundary": (
            "A pass establishes repository-history scientific freshness for the exact SAAMER 2022/2023 annual archives only. "
            "No SAAMER 2022/2023 archive is downloaded or parsed by this audit."
        ),
    }
    (OUT / "saamer_2022_2023_repo_freshness_audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    if verdict.startswith("FAIL_"):
        raise SystemExit(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
