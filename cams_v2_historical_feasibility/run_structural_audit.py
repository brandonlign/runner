#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from io import BytesIO
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urljoin, urlparse

import requests

PAGES = {
    "v2016": "https://www.astro.sk/~ne/IAUMDC/PhV2016/video.html",
    "v2020": "https://www.astro.sk/~ne/IAUMDC/PhVR2020/video.html",
}
BASENAMES = ("CAMS_California_v2.zip", "CAMS_BeNeLux_v2.zip", "reading.f")
HREF_RE = re.compile(r"href\s*=\s*([\"'])(.*?)\1", re.IGNORECASE | re.DOTALL)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def safe_member(name: str) -> bool:
    path = PurePosixPath(name)
    return not path.is_absolute() and ".." not in path.parts and not name.startswith(("/", "\\"))


def fetch(session: requests.Session, url: str) -> tuple[bytes, str, str | None]:
    response = session.get(url, timeout=300, allow_redirects=True)
    response.raise_for_status()
    return response.content, response.url, response.headers.get("content-type")


def href_map(page_raw: bytes, page_url: str) -> dict[str, list[str]]:
    text = page_raw.decode("latin-1")
    found = {name: [] for name in BASENAMES}
    for _, href in HREF_RE.findall(text):
        href = href.strip()
        basename = PurePosixPath(unquote(urlparse(href).path)).name
        if basename in found:
            found[basename].append(urljoin(page_url, href))
    return found


def audit_zip(raw: bytes) -> dict:
    with zipfile.ZipFile(BytesIO(raw)) as archive:
        bad = archive.testzip()
        infos = archive.infolist()
        members = [
            {
                "name": info.filename,
                "bytes": info.file_size,
                "compressed_bytes": info.compress_size,
                "is_directory": info.is_dir(),
            }
            for info in infos
        ]
    nonempty_files = [item for item in members if not item["is_directory"] and item["bytes"] > 0]
    gates = {
        "zip_crc": bad is None,
        "safe_member_paths": all(safe_member(item["name"]) for item in members),
        "nonempty_data_member_present": bool(nonempty_files),
    }
    return {"members": members, "gates": gates}


def build_result() -> dict:
    session = requests.Session()
    pages: dict[str, dict] = {}
    resources: dict[str, dict[str, dict]] = {}

    for page_name, page_url in PAGES.items():
        raw, final_url, content_type = fetch(session, page_url)
        links = href_map(raw, final_url)
        pages[page_name] = {
            "requested_url": page_url,
            "final_url": final_url,
            "bytes": len(raw),
            "sha256": sha256(raw),
            "content_type": content_type,
            "href_match_counts": {name: len(links[name]) for name in BASENAMES},
            "gates": {f"exact_one_href_{name}": len(links[name]) == 1 for name in BASENAMES},
        }
        resources[page_name] = {}
        for basename in BASENAMES:
            if len(links[basename]) != 1:
                raise RuntimeError(f"{page_name}: expected one href for {basename}, found {links[basename]}")
            resource_raw, resource_final, resource_type = fetch(session, links[basename][0])
            item = {
                "basename": basename,
                "resolved_url": links[basename][0],
                "final_url": resource_final,
                "bytes": len(resource_raw),
                "sha256": sha256(resource_raw),
                "content_type": resource_type,
            }
            if basename.endswith(".zip"):
                item["zip"] = audit_zip(resource_raw)
            else:
                source_text = resource_raw.decode("latin-1")
                upper = source_text.upper()
                token_gates = {
                    "contains_CAMS": "CAMS" in upper,
                    "contains_READ": "READ" in upper,
                    "contains_SHOWER_or_STREAM": "SHOWER" in upper or "STREAM" in upper,
                }
                item["reader_summary"] = {
                    "line_count": len(source_text.splitlines()),
                    "token_gates": token_gates,
                }
            resources[page_name][basename] = item

    identical = {
        basename: resources["v2016"][basename]["sha256"] == resources["v2020"][basename]["sha256"]
        for basename in BASENAMES
    }
    page_gates = all(all(page["gates"].values()) for page in pages.values())
    zip_gates = all(
        all(resources[page_name][basename]["zip"]["gates"].values())
        for page_name in PAGES
        for basename in BASENAMES
        if basename.endswith(".zip")
    )
    reader_gates = all(
        all(resources[page_name]["reading.f"]["reader_summary"]["token_gates"].values())
        for page_name in PAGES
    )
    gates = {
        "both_official_pages_retrieved": len(pages) == 2,
        "exact_one_href_for_each_resource_on_each_page": page_gates,
        "version_2016_and_2020_resources_identical": all(identical.values()),
        "all_zip_integrity_and_path_gates_pass": zip_gates,
        "reader_source_token_gates_pass": reader_gates,
        "meteor_data_member_content_not_opened": True,
        "sonotaco_2024_not_read": True,
        "camsv3_2016_values_not_read": True,
    }
    verdict = "PASS_HISTORICAL_CAMSV2_STRUCTURAL_FEASIBILITY" if all(gates.values()) else "KILL_HISTORICAL_CAMSV2_STRUCTURAL_FEASIBILITY"
    return {
        "method": "Historical CAMS Database 2.0 structural feasibility",
        "pages": pages,
        "resources": resources,
        "cross_version_resource_identity": identical,
        "meteor_data_member_content_opened": False,
        "label_values_read": False,
        "scientific_values_read": False,
        "sonotaco_2024_read": False,
        "camsv3_2016_values_read": False,
        "gates": gates,
        "verdict": verdict,
    }


def write_outputs(out: Path, result: dict) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "historical_camsv2_structural_feasibility.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    report = [
        "# Historical CAMS Database 2.0 structural feasibility",
        "",
        f"**Verdict:** `{result['verdict']}`",
        "",
    ]
    if "resources" in result:
        for basename in BASENAMES:
            left = result["resources"]["v2016"][basename]
            report.extend(
                [
                    f"## {basename}",
                    "",
                    f"- bytes: {left['bytes']}",
                    f"- SHA-256: `{left['sha256']}`",
                    f"- identical across Version 2016/2020 pages: {result['cross_version_resource_identity'][basename]}",
                    "",
                ]
            )
    if result.get("error"):
        report.extend(["## Execution error", "", f"`{result['error']}`", ""])
    report.extend(["## Frozen gates", ""])
    report.extend(f"- {name}: {passed}" for name, passed in result.get("gates", {}).items())
    report.extend(
        [
            "",
            "No meteor-record member was opened for content inspection. No label, geometry, score, event identifier, SonotaCo 2024 value, or CAMSv3 2016 value was read.",
        ]
    )
    (out / "RESULT.md").write_text("\n".join(report) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    out = Path(args.output)
    try:
        result = build_result()
    except Exception as exc:
        result = {
            "method": "Historical CAMS Database 2.0 structural feasibility",
            "error": f"{type(exc).__name__}: {exc}",
            "meteor_data_member_content_opened": False,
            "label_values_read": False,
            "scientific_values_read": False,
            "sonotaco_2024_read": False,
            "camsv3_2016_values_read": False,
            "gates": {"execution_completed": False},
            "verdict": "KILL_HISTORICAL_CAMSV2_STRUCTURAL_FEASIBILITY",
        }
    write_outputs(out, result)
    print(json.dumps({"verdict": result["verdict"], "gates": result.get("gates"), "error": result.get("error")}, indent=2))
    if result["verdict"] != "PASS_HISTORICAL_CAMSV2_STRUCTURAL_FEASIBILITY":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
