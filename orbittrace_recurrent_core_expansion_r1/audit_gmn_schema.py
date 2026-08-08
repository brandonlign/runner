#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import re
from pathlib import Path

from gmn_python_api import data_directory as dd

MONTH = "2022-01"
KNOWN_MARKERS = (
    "unique trajectory identifier",
    "sol lon",
    "solar longitude",
    "lamgeo",
    "betgeo",
    "vgeo",
)
ORBIT_TERMS = (
    "perihelion",
    "eccentric",
    "inclination",
    "argument",
    "ascending",
    "node",
    "semimajor",
    "semi-major",
    "q au",
    "omega",
)


def sanitize(line: str) -> str:
    line = line.strip().lstrip("\ufeff")
    line = re.sub(r"\s+", " ", line)
    # Headers are expected to be textual. Refuse to emit lines that look like data rows.
    numeric_tokens = re.findall(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?(?:[Ee][-+]?\d+)?(?![A-Za-z])", line)
    if len(numeric_tokens) > 3:
        raise RuntimeError("candidate schema line contains too many numeric tokens; refusing to emit")
    if len(line) > 4000:
        raise RuntimeError("candidate schema line unexpectedly long")
    return line


def main() -> int:
    out = Path("output_schema")
    out.mkdir(parents=True, exist_ok=True)
    text = dd.get_monthly_file_content_by_date(MONTH)
    payload = text.encode("utf-8")

    matches: list[str] = []
    for raw in text.splitlines():
        low = raw.lower()
        if sum(marker in low for marker in KNOWN_MARKERS) >= 2:
            matches.append(sanitize(raw))
        elif any(marker in low for marker in KNOWN_MARKERS) and any(term in low for term in ORBIT_TERMS):
            matches.append(sanitize(raw))
    matches = sorted(set(x for x in matches if x))
    if not matches:
        raise RuntimeError("no recognizable GMN schema/header line found without row parsing")

    joined = "\n".join(matches).lower()
    result = {
        "verdict": "PASS_GMN_SCHEMA_ONLY_ORBIT_COLUMN_AUDIT",
        "month": MONTH,
        "raw_bytes": len(payload),
        "raw_sha256": hashlib.sha256(payload).hexdigest(),
        "gmn_python_api_version": importlib.metadata.version("gmn-python-api"),
        "trajectory_dataframe_parser_invoked": False,
        "event_row_values_parsed": False,
        "shower_label_values_accessed": False,
        "orbittrace_target_accessed": False,
        "target_region_event_accessed": False,
        "schema_lines": matches,
        "schema_mentions": {
            "perihelion": "perihelion" in joined or bool(re.search(r"(?:^|[^a-z])q(?:[^a-z]|$)", joined)),
            "eccentricity": "eccentric" in joined,
            "inclination": "inclination" in joined or bool(re.search(r"(?:^|[^a-z])incl(?:[^a-z]|$)", joined)),
            "perihelion_argument": "argument" in joined or "omega" in joined,
            "ascending_node": "ascending" in joined or "node" in joined,
        },
    }
    (out / "gmn_schema_only_orbit_column_audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (out / "GMN_SCHEMA_ONLY_ORBIT_COLUMN_AUDIT.md").write_text(
        "# GMN schema-only orbit-column audit\n\n"
        f"Verdict: **`{result['verdict']}`**\n\n"
        + "\n".join(f"- `{line}`" for line in matches)
        + "\n\nNo event row or shower-label value was parsed. No OrbitTrace target information was accessed.\n"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
