from __future__ import annotations

import hashlib
import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

OUT_DIR = Path("dynamics_rest_probe/results")
BASE = "https://explore.globalmeteornetwork.org"
USER_AGENT = "ghoststream-gmn-rest-probe/1.0"


def request_json(path: str, params: dict[str, str]) -> tuple[dict[str, Any], dict[str, Any]]:
    url = f"{BASE}{path}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    bypassed = False
    try:
        response = urllib.request.urlopen(request, timeout=180)
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", None)
        if not isinstance(reason, ssl.SSLCertVerificationError):
            raise
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        response = urllib.request.urlopen(request, timeout=180, context=context)
        bypassed = True
    with response:
        payload = response.read()
        metadata = {
            "requested_url": url,
            "final_url": response.geturl(),
            "status": getattr(response, "status", None),
            "content_type": response.headers.get("Content-Type"),
            "last_modified": response.headers.get("last-modified"),
            "link": response.headers.get("Link"),
            "tls_hostname_bypass": bypassed,
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "prefix": payload[:300].decode("utf-8", errors="replace"),
        }
    return json.loads(payload), metadata


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results: dict[str, Any] = {}

    count_payload, count_meta = request_json(
        "/gmn_rest_api",
        {
            "sql": "SELECT shower_iau_no, COUNT(*) AS n FROM meteor WHERE shower_iau_no IN (4,6,7,10,13) GROUP BY shower_iau_no ORDER BY shower_iau_no",
            "data_shape": "objects",
            "data_format": "json",
        },
    )
    results["control_counts"] = {"metadata": count_meta, "payload": count_payload}

    summary_payload, summary_meta = request_json(
        "/gmn_rest_api/meteor_summary",
        {
            "where": "shower.iau_no = 10",
            "order_by": "meteor.beginning_utc_time DESC",
            "data_shape": "objects",
            "data_format": "json",
            "page": "1",
        },
    )
    results["quadrantid_summary_page"] = {"metadata": summary_meta, "payload": summary_payload}

    sporadic_payload, sporadic_meta = request_json(
        "/gmn_rest_api",
        {
            "sql": "SELECT COUNT(*) AS n FROM meteor WHERE shower_iau_no = -1",
            "data_shape": "objects",
            "data_format": "json",
        },
    )
    results["sporadic_count"] = {"metadata": sporadic_meta, "payload": sporadic_payload}

    (OUT_DIR / "probe.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    lines = ["# GMN documented REST API probe", ""]
    for name, result in results.items():
        payload = result["payload"]
        metadata = result["metadata"]
        rows = payload.get("rows", []) if isinstance(payload, dict) else []
        lines.extend([
            f"## {name}",
            "",
            f"- status: `{metadata['status']}`",
            f"- final URL: `{metadata['final_url']}`",
            f"- TLS hostname bypass: `{metadata['tls_hostname_bypass']}`",
            f"- last-modified: `{metadata['last_modified']}`",
            f"- rows returned: `{len(rows)}`",
            f"- ok: `{payload.get('ok') if isinstance(payload, dict) else None}`",
            f"- first row keys: `{list(rows[0]) if rows else []}`",
            "",
        ])
    report = "\n".join(lines)
    (OUT_DIR / "PROBE_REPORT.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
