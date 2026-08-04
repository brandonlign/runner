#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urljoin, urlparse

import requests

PAGES = {
    "v2016": "https://www.astro.sk/~ne/IAUMDC/PhV2016/video.html",
    "v2020": "https://www.astro.sk/~ne/IAUMDC/PhVR2020/video.html",
}
BASENAMES = (
    "CAMS_California_v2.xlsx",
    "CAMS_BeNeLux_v2.xlsx",
    "CAMS_California_v2.1l",
    "CAMS_BeNeLux_v2.1l",
    "CAMS_by_date_v2.1l",
    "document.pdf",
)
HREF_RE = re.compile(r"href\s*=\s*([\"'])(.*?)\1", re.IGNORECASE | re.DOTALL)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def safe_name(name: str) -> bool:
    path = PurePosixPath(name)
    return not path.is_absolute() and ".." not in path.parts and not name.startswith(("/", "\\"))


def fetch(session: requests.Session, url: str) -> tuple[bytes, str, str | None]:
    response = session.get(url, timeout=300, allow_redirects=True)
    response.raise_for_status()
    return response.content, response.url, response.headers.get("content-type")


def extract_links(page_raw: bytes, final_page_url: str) -> dict[str, list[str]]:
    text = page_raw.decode("latin-1")
    links = {name: [] for name in BASENAMES}
    for _, href in HREF_RE.findall(text):
        href = href.strip()
        basename = PurePosixPath(unquote(urlparse(href).path)).name
        if basename in links:
            links[basename].append(urljoin(final_page_url, href))
    return links


def audit_xlsx(raw: bytes) -> dict:
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
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
    names = {item["name"] for item in members}
    worksheets = sorted(
        name for name in names if re.fullmatch(r"xl/worksheets/sheet[0-9]+\.xml", name)
    )
    gates = {
        "zip_crc": bad is None,
        "safe_member_paths": all(safe_name(item["name"]) for item in members),
        "content_types_present": "[Content_Types].xml" in names,
        "workbook_xml_present": "xl/workbook.xml" in names,
        "worksheet_member_present": bool(worksheets),
    }
    return {
        "members": members,
        "worksheet_member_names": worksheets,
        "member_content_opened": False,
        "gates": gates,
    }


def build_result() -> dict:
    session = requests.Session()
    pages: dict[str, dict] = {}
    resources: dict[str, dict[str, dict]] = {}

    for page_key, page_url in PAGES.items():
        page_raw, final_page_url, content_type = fetch(session, page_url)
        links = extract_links(page_raw, final_page_url)
        pages[page_key] = {
            "requested_url": page_url,
            "final_url": final_page_url,
            "bytes": len(page_raw),
            "sha256": digest(page_raw),
            "content_type": content_type,
            "href_match_counts": {name: len(links[name]) for name in BASENAMES},
            "gates": {f"exact_one_href_{name}": len(links[name]) == 1 for name in BASENAMES},
        }
        resources[page_key] = {}
        for basename in BASENAMES:
            if len(links[basename]) != 1:
                raise RuntimeError(f"{page_key}: expected one href for {basename}, found {links[basename]}")
            raw, final_url, resource_type = fetch(session, links[basename][0])
            item: dict = {
                "basename": basename,
                "resolved_url": links[basename][0],
                "final_url": final_url,
                "bytes": len(raw),
                "sha256": digest(raw),
                "content_type": resource_type,
            }
            if basename.endswith(".xlsx"):
                item["xlsx"] = audit_xlsx(raw)
            elif basename.endswith(".1l"):
                item["single_line"] = {
                    "nonempty": bool(raw),
                    "decoded": False,
                    "records_read": False,
                }
            elif basename == "document.pdf":
                item["pdf"] = {
                    "magic_ok": raw.startswith(b"%PDF-"),
                    "parsed": False,
                    "pages_read": False,
                }
            resources[page_key][basename] = item

    identity = {
        basename: resources["v2016"][basename]["sha256"] == resources["v2020"][basename]["sha256"]
        for basename in BASENAMES
    }
    xlsx_gates = all(
        all(resources[page][name]["xlsx"]["gates"].values())
        for page in PAGES
        for name in BASENAMES
        if name.endswith(".xlsx")
    )
    one_line_gates = all(
        resources[page][name]["single_line"]["nonempty"]
        for page in PAGES
        for name in BASENAMES
        if name.endswith(".1l")
    )
    pdf_gates = all(
        resources[page]["document.pdf"]["pdf"]["magic_ok"] for page in PAGES
    )
    gates = {
        "both_official_pages_retrieved": len(pages) == 2,
        "exact_one_href_for_all_resources": all(
            all(page["gates"].values()) for page in pages.values()
        ),
        "cross_version_resources_byte_identical": all(identity.values()),
        "xlsx_structural_gates_pass": xlsx_gates,
        "single_line_resources_nonempty": one_line_gates,
        "documentation_pdf_magic_valid": pdf_gates,
        "no_workbook_member_content_opened": True,
        "no_single_line_record_decoded": True,
        "no_pdf_page_parsed": True,
        "reserved_panels_not_read": True,
    }
    verdict = (
        "PASS_HISTORICAL_CAMSV2_TABULAR_STRUCTURAL_FEASIBILITY"
        if all(gates.values())
        else "KILL_HISTORICAL_CAMSV2_TABULAR_STRUCTURAL_FEASIBILITY"
    )
    return {
        "method": "Historical CAMS Database 2.0 tabular-interface structural feasibility",
        "pages": pages,
        "resources": resources,
        "cross_version_resource_identity": identity,
        "workbook_member_content_opened": False,
        "single_line_text_decoded": False,
        "single_line_records_read": False,
        "documentation_pdf_parsed": False,
        "meteor_values_read": False,
        "label_values_read": False,
        "later_california_records_read": False,
        "benelux_meteor_values_read": False,
        "sonotaco_2024_read": False,
        "camsv3_2016_values_read": False,
        "gates": gates,
        "verdict": verdict,
    }


def write_outputs(out: Path, result: dict) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "tabular_structural_feasibility.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    report = [
        "# Historical CAMS Database 2.0 tabular-interface structural feasibility",
        "",
        f"**Verdict:** `{result['verdict']}`",
        "",
    ]
    if "resources" in result:
        for basename in BASENAMES:
            item = result["resources"]["v2016"][basename]
            report.extend(
                [
                    f"## {basename}",
                    "",
                    f"- bytes: {item['bytes']}",
                    f"- SHA-256: `{item['sha256']}`",
                    f"- identical across archive pages: {result['cross_version_resource_identity'][basename]}",
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
            "No worksheet XML, cell, single-line text record, PDF page, meteor value, or label value was opened or decoded.",
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
            "method": "Historical CAMS Database 2.0 tabular-interface structural feasibility",
            "error": f"{type(exc).__name__}: {exc}",
            "workbook_member_content_opened": False,
            "single_line_text_decoded": False,
            "single_line_records_read": False,
            "documentation_pdf_parsed": False,
            "meteor_values_read": False,
            "label_values_read": False,
            "later_california_records_read": False,
            "benelux_meteor_values_read": False,
            "sonotaco_2024_read": False,
            "camsv3_2016_values_read": False,
            "gates": {"execution_completed": False},
            "verdict": "KILL_HISTORICAL_CAMSV2_TABULAR_STRUCTURAL_FEASIBILITY",
        }
    write_outputs(out, result)
    print(json.dumps({"verdict": result["verdict"], "gates": result.get("gates"), "error": result.get("error")}, indent=2))
    if result["verdict"] != "PASS_HISTORICAL_CAMSV2_TABULAR_STRUCTURAL_FEASIBILITY":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
