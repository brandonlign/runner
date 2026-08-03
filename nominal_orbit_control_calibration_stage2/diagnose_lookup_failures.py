from __future__ import annotations

import argparse
import hashlib
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

BASE = "https://ceresiaumdc.ta3.sk/downloads/LuT/"
USER_AGENT = "ghoststream-control-lookup-diagnosis/1.1"
FILENAMES = ("257_ORS.csv", "388_CTA.csv", "0427FED_006.csv", "0394ACA_004.csv")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def candidate_urls(filename: str) -> list[str]:
    widths = [len(filename), 22] + list(range(18, 33))
    urls: list[str] = []
    seen: set[str] = set()
    for width in widths:
        padded = filename if width <= len(filename) else filename.ljust(width)
        url = urllib.parse.urljoin(BASE, urllib.parse.quote(padded, safe=""))
        if url not in seen:
            seen.add(url)
            urls.append(url)
    return urls


def request_once(url: str) -> tuple[bytes, dict[str, Any]]:
    opener = urllib.request.build_opener(NoRedirect)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "text/csv,*/*;q=0.5"},
    )
    try:
        with opener.open(request, timeout=20) as response:
            raw = response.read(64 * 1024 * 1024 + 1)
            return raw, {
                "url": url,
                "status": getattr(response, "status", 200),
                "reason": getattr(response, "reason", None),
                "final_url": response.geturl(),
                "headers": dict(response.headers.items()),
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "error": None,
            }
    except urllib.error.HTTPError as exc:
        raw = exc.read(64 * 1024 * 1024 + 1)
        return raw, {
            "url": url,
            "status": exc.code,
            "reason": exc.reason,
            "final_url": exc.geturl(),
            "headers": dict(exc.headers.items()),
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest() if raw else None,
            "error": f"HTTPError: {exc}",
        }
    except Exception as exc:
        return b"", {
            "url": url,
            "status": getattr(exc, "code", None),
            "reason": None,
            "final_url": None,
            "headers": {},
            "bytes": 0,
            "sha256": None,
            "error": f"{type(exc).__name__}: {exc}",
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    all_results: dict[str, Any] = {}

    for filename in FILENAMES:
        file_dir = args.output / filename.replace("/", "_")
        file_dir.mkdir(parents=True, exist_ok=True)
        attempts: list[dict[str, Any]] = []
        saved_hashes: set[str] = set()
        for index, url in enumerate(candidate_urls(filename)):
            raw, record = request_once(url)
            attempts.append(record)
            digest = record.get("sha256")
            if raw and digest not in saved_hashes:
                saved_hashes.add(str(digest))
                suffix = "csv" if "csv" in str(record.get("headers", {}).get("Content-Type", "")).lower() else "bin"
                (file_dir / f"response_{index:02d}_{record.get('status')}_{digest}.{suffix}").write_bytes(raw)
                preview = raw[:4000].decode("utf-8-sig", "replace")
                (file_dir / f"response_{index:02d}_{record.get('status')}_{digest}.preview.txt").write_text(
                    preview,
                    encoding="utf-8",
                )
        (file_dir / "attempts.json").write_text(
            json.dumps(attempts, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        all_results[filename] = attempts

    (args.output / "lookup_failure_diagnosis.json").write_text(
        json.dumps(all_results, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
