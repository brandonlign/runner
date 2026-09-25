from __future__ import annotations

import csv
import hashlib
import io
import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

OUT_DIR = Path("dynamics_probe/results")
BASE = "https://explore.globalmeteornetwork.org/gmn_data_store"
USER_AGENT = "ghoststream-dynamics-api-probe/1.0"


def request(url: str) -> tuple[bytes, dict[str, Any]]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    bypassed = False
    try:
        response = urllib.request.urlopen(req, timeout=120)
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", None)
        if not isinstance(reason, ssl.SSLCertVerificationError):
            raise
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        response = urllib.request.urlopen(req, timeout=120, context=context)
        bypassed = True
    with response:
        payload = response.read()
        return payload, {
            "status": getattr(response, "status", None),
            "content_type": response.headers.get("Content-Type"),
            "final_url": response.geturl(),
            "tls_hostname_bypass": bypassed,
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
        }


def csv_probe(name: str, endpoint: str, params: dict[str, str]) -> tuple[dict[str, Any], list[dict[str, str]]]:
    url = f"{BASE}/{endpoint}.csv?{urllib.parse.urlencode(params)}"
    payload, metadata = request(url)
    text = payload.decode("utf-8-sig", errors="replace")
    result: dict[str, Any] = {
        "name": name,
        "requested_url": url,
        **metadata,
        "prefix": text[:300],
        "is_html": text.lstrip().lower().startswith("<!doctype html"),
    }
    rows: list[dict[str, str]] = []
    if not result["is_html"]:
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
        result["header"] = list(reader.fieldnames or [])
        result["row_count"] = len(rows)
        result["first_row"] = rows[0] if rows else None
    return result, rows


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    probes: list[dict[str, Any]] = []

    meteor_probe, meteor_rows = csv_probe(
        "meteor_by_shower",
        "meteor",
        {"shower_iau_no": "4", "_size": "5", "_sort_desc": "beginning_utc_time"},
    )
    probes.append(meteor_probe)

    shower_probe, _ = csv_probe(
        "shower_lookup",
        "shower",
        {"iau_no": "4", "_size": "5"},
    )
    probes.append(shower_probe)

    sigma_probe, sigma_rows = csv_probe(
        "sigma_unfiltered",
        "meteor_sigma",
        {"_size": "5"},
    )
    probes.append(sigma_probe)

    trajectory_id = None
    if meteor_rows:
        trajectory_id = meteor_rows[0].get("unique_trajectory_identifier")
    if not trajectory_id and sigma_rows:
        trajectory_id = sigma_rows[0].get("unique_trajectory_identifier")

    if trajectory_id:
        linked_probe, _ = csv_probe(
            "sigma_by_trajectory",
            "meteor_sigma",
            {"unique_trajectory_identifier": trajectory_id, "_size": "5"},
        )
        probes.append(linked_probe)

    payload = {
        "trajectory_id_used": trajectory_id,
        "probes": probes,
    }
    (OUT_DIR / "probe.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = ["# GMN table API probe", ""]
    for probe in probes:
        lines.extend([
            f"## {probe['name']}",
            "",
            f"- status: `{probe.get('status')}`",
            f"- content type: `{probe.get('content_type')}`",
            f"- TLS hostname bypass: `{probe.get('tls_hostname_bypass')}`",
            f"- HTML response: `{probe.get('is_html')}`",
            f"- rows: `{probe.get('row_count')}`",
            f"- header: `{probe.get('header')}`",
            f"- SHA-256: `{probe.get('sha256')}`",
            "",
        ])
    (OUT_DIR / "PROBE_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
