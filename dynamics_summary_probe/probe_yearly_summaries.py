from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path
from typing import Any

OUT_DIR = Path("dynamics_summary_probe/results")
USER_AGENT = "ghoststream-gmn-summary-probe/1.0"
YEARS = (2019, 2023, 2025)
BYTE_LIMIT = 1_500_000
URL_TEMPLATE = "https://globalmeteornetwork.org/data/traj_summary_data/traj_summary_yearly_{year}.txt"


def probe(year: int) -> dict[str, Any]:
    url = URL_TEMPLATE.format(year=year)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=180) as response:
        payload = response.read(BYTE_LIMIT)
        metadata = {
            "status": getattr(response, "status", None),
            "content_type": response.headers.get("Content-Type"),
            "content_length": response.headers.get("Content-Length"),
            "final_url": response.geturl(),
        }
    text = payload.decode("utf-8-sig", errors="replace")
    lines = text.splitlines()
    nonempty = [line for line in lines if line.strip()]
    marker_lines = [
        line
        for line in lines[:300]
        if any(marker in line.lower() for marker in ("iau", "shower", "sigma", "trajectory", "beginning"))
    ]
    return {
        "year": year,
        "url": url,
        **metadata,
        "bytes_read": len(payload),
        "sha256_prefix_bytes": hashlib.sha256(payload).hexdigest(),
        "line_count": len(lines),
        "first_40_nonempty_lines": nonempty[:40],
        "marker_lines_first_300": marker_lines[:80],
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    probes = [probe(year) for year in YEARS]
    payload = {"byte_limit": BYTE_LIMIT, "probes": probes}
    (OUT_DIR / "probe.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = ["# Official GMN yearly-summary probe", ""]
    for item in probes:
        lines.extend([
            f"## {item['year']}",
            "",
            f"- status: `{item['status']}`",
            f"- content type: `{item['content_type']}`",
            f"- declared length: `{item['content_length']}`",
            f"- bytes inspected: `{item['bytes_read']}`",
            f"- lines inspected: `{item['line_count']}`",
            f"- marker lines: `{item['marker_lines_first_300'][:10]}`",
            "",
        ])
    report = "\n".join(lines)
    (OUT_DIR / "PROBE_REPORT.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
