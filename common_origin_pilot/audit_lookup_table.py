#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd
import requests

OUT = Path(__file__).resolve().parent / "results"
CACHE = Path(__file__).resolve().parent / "cache"
DATASET_ID = "t2rrdtzd8h"
VERSION = 1
API_CANDIDATES = [
    f"https://api.data.mendeley.com/datasets/{DATASET_ID}/files?version={VERSION}",
    f"https://api.data.mendeley.com/datasets/{DATASET_ID}/versions/{VERSION}/files",
]


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def request_json(url: str) -> tuple[Any, dict[str, Any]]:
    response = requests.get(url, timeout=120, headers={"Accept": "application/json"})
    response.raise_for_status()
    return response.json(), {
        "url": url,
        "status": response.status_code,
        "content_type": response.headers.get("content-type"),
        "bytes": len(response.content),
        "sha256": sha256(response.content),
    }


def walk(value: Any, path: str = "") -> list[tuple[str, Any]]:
    found: list[tuple[str, Any]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            found.append((child_path, child))
            found.extend(walk(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_path = f"{path}[{index}]"
            found.extend(walk(child, child_path))
    return found


def records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("files", "data", "items", "results"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def text_values(record: dict[str, Any]) -> list[str]:
    values = []
    for _, value in walk(record):
        if isinstance(value, str):
            values.append(value)
    return values


def select_file(payload: Any) -> dict[str, Any]:
    candidates = records(payload)
    ranked = []
    for record in candidates:
        joined = " ".join(text_values(record)).lower()
        score = 0
        if "showerlookuptable" in re.sub(r"[^a-z0-9]+", "", joined):
            score += 100
        if "lookup" in joined:
            score += 20
        if ".txt" in joined or "text/plain" in joined:
            score += 5
        ranked.append((score, record))
    if not ranked:
        raise RuntimeError(f"No file records found in API payload type {type(payload).__name__}")
    ranked.sort(key=lambda item: item[0], reverse=True)
    if ranked[0][0] <= 0:
        raise RuntimeError(f"No lookup-table file identified. Records: {candidates[:3]}")
    return ranked[0][1]


def find_download_url(record: dict[str, Any]) -> tuple[str | None, str | None]:
    file_id = None
    for key in ("id", "file_id", "uuid"):
        value = record.get(key)
        if isinstance(value, str) and value:
            file_id = value
            break
    urls = []
    for path, value in walk(record):
        if isinstance(value, str) and value.startswith(("http://", "https://")):
            score = 0
            lowered = path.lower() + " " + value.lower()
            if "download" in lowered:
                score += 20
            if "content" in lowered:
                score += 5
            urls.append((score, value, path))
    urls.sort(reverse=True)
    return (urls[0][1] if urls else None), file_id


def download(record: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
    direct_url, file_id = find_download_url(record)
    attempts = []
    candidate_urls = []
    if direct_url:
        candidate_urls.append(direct_url)
    if file_id:
        candidate_urls.extend([
            f"https://api.data.mendeley.com/datasets/{DATASET_ID}/files/{file_id}/file_downloaded?version={VERSION}",
            f"https://api.data.mendeley.com/datasets/{DATASET_ID}/versions/{VERSION}/files/{file_id}/download",
        ])
    for url in dict.fromkeys(candidate_urls):
        try:
            response = requests.get(url, timeout=300, allow_redirects=True)
            attempts.append({
                "url": url,
                "final_url": response.url,
                "status": response.status_code,
                "content_type": response.headers.get("content-type"),
                "bytes": len(response.content),
            })
            response.raise_for_status()
            raw = response.content
            if len(raw) < 1000:
                continue
            if raw[:1] in (b"{", b"[") and b"error" in raw[:1000].lower():
                continue
            return raw, {
                "selected_url": url,
                "final_url": response.url,
                "content_type": response.headers.get("content-type"),
                "bytes": len(raw),
                "sha256": sha256(raw),
                "attempts": attempts,
            }
        except Exception as error:
            attempts[-1]["error"] = repr(error)
    raise RuntimeError(f"Lookup file download failed: {attempts}")


def parse_table(raw: bytes) -> tuple[pd.DataFrame, dict[str, Any]]:
    text = raw.decode("utf-8-sig", errors="replace")
    nonempty = [line for line in text.splitlines() if line.strip()]
    if not nonempty:
        raise RuntimeError("Lookup table is empty")
    sample = "\n".join(nonempty[:20])
    delimiter = None
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t| ")
        delimiter = dialect.delimiter
    except csv.Error:
        pass
    parse_attempts = []
    readers = []
    if delimiter and delimiter != " ":
        readers.append((f"delimiter={delimiter!r}", {"sep": delimiter}))
    readers.extend([
        ("whitespace", {"sep": r"\s+"}),
        ("comma", {"sep": ","}),
        ("semicolon", {"sep": ";"}),
        ("tab", {"sep": "\t"}),
    ])
    best = None
    for name, kwargs in readers:
        try:
            frame = pd.read_csv(io.StringIO(text), engine="python", comment="#", **kwargs)
            frame.columns = [str(column).strip() for column in frame.columns]
            score = len(frame.columns) * 100000 + len(frame)
            parse_attempts.append({"reader": name, "rows": len(frame), "columns": list(frame.columns)})
            if best is None or score > best[0]:
                best = (score, frame, name)
        except Exception as error:
            parse_attempts.append({"reader": name, "error": repr(error)})
    if best is None:
        raise RuntimeError(f"No parser succeeded: {parse_attempts}")
    frame = best[1]
    return frame, {
        "reader": best[2],
        "detected_delimiter": delimiter,
        "first_lines": nonempty[:10],
        "attempts": parse_attempts,
    }


def profile(frame: pd.DataFrame) -> dict[str, Any]:
    normalized = {str(column): re.sub(r"[^a-z0-9]+", "", str(column).lower()) for column in frame.columns}
    label_column = next((column for column, name in normalized.items() if name == "iau"), None)
    label_counts = None
    if label_column:
        values = pd.to_numeric(frame[label_column], errors="coerce")
        label_counts = {
            "non_null": int(values.notna().sum()),
            "unique": int(values.nunique()),
            "top": {str(int(key)): int(value) for key, value in values.value_counts().head(30).items()},
            "minimum": float(values.min()) if values.notna().any() else None,
            "maximum": float(values.max()) if values.notna().any() else None,
        }
    return {
        "rows": int(len(frame)),
        "columns": list(map(str, frame.columns)),
        "dtypes": {str(column): str(dtype) for column, dtype in frame.dtypes.items()},
        "label_column": label_column,
        "label_counts": label_counts,
        "null_fraction": {str(column): float(frame[column].isna().mean()) for column in frame.columns},
        "unique_values": {str(column): int(frame[column].nunique(dropna=True)) for column in frame.columns},
        "head": frame.head(20).where(pd.notna(frame.head(20)), None).to_dict(orient="records"),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    api_failures = []
    payload = None
    api_meta = None
    for url in API_CANDIDATES:
        try:
            payload, api_meta = request_json(url)
            break
        except Exception as error:
            api_failures.append({"url": url, "error": repr(error)})
    if payload is None:
        raise RuntimeError(f"All Mendeley file-list endpoints failed: {api_failures}")
    record = select_file(payload)
    raw, download_meta = download(record)
    (CACHE / "ShowerLookUpTable.txt").write_bytes(raw)
    frame, parse_meta = parse_table(raw)
    table_profile = profile(frame)

    required = {"lo", "l", "b", "vg", "iau"}
    normalized_columns = {re.sub(r"[^a-z0-9]+", "", str(column).lower()) for column in frame.columns}
    required_present = sorted(required & normalized_columns)
    has_source = any(name in normalized_columns for name in ("source", "network", "database", "db"))
    has_identifier = any(name in normalized_columns for name in ("id", "iid", "identifier", "meteorid"))
    schema_pass = required.issubset(normalized_columns) and table_profile["label_counts"] is not None and table_profile["label_counts"]["unique"] >= 8
    verdict = "LOOKUP_SCHEMA_PASS" if schema_pass else "LOOKUP_SCHEMA_NO_GO"
    payload_out = {
        "verdict": verdict,
        "dataset_id": DATASET_ID,
        "version": VERSION,
        "api": api_meta,
        "api_failures": api_failures,
        "selected_file_record": record,
        "download": download_meta,
        "parse": parse_meta,
        "profile": table_profile,
        "gate": {
            "required_columns": sorted(required),
            "required_present": required_present,
            "minimum_unique_labels": 8,
            "schema_passed": schema_pass,
            "has_source_column": has_source,
            "has_event_identifier": has_identifier,
            "requires_orbit_catalog_join": not (has_source and has_identifier),
        },
        "claim_boundary": "This audit tests only whether the published lookup table can support a labeled data join. Its shower assignments are operational labels, not proof of common parentage.",
    }
    (OUT / "lookup_table_audit.json").write_text(json.dumps(payload_out, indent=2, sort_keys=True, allow_nan=False), encoding="utf-8")
    lines = [
        "# Meteor shower lookup-table audit",
        "",
        f"**Verdict:** `{verdict}`",
        "",
        f"- Rows: **{table_profile['rows']:,}**",
        f"- Columns: `{', '.join(table_profile['columns'])}`",
        f"- Unique IAU labels: **{table_profile['label_counts']['unique'] if table_profile['label_counts'] else 0}**",
        f"- Source column present: **{has_source}**",
        f"- Event identifier present: **{has_identifier}**",
        f"- Full-orbit catalogue join required: **{not (has_source and has_identifier)}**",
        "",
        "## Interpretation boundary",
        "",
        "A schema pass only authorizes the next join/matching audit. It does not establish label correctness, parent-body identity, or learned-metric validity.",
    ]
    (OUT / "LOOKUP_TABLE_AUDIT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": verdict, "rows": table_profile["rows"], "columns": table_profile["columns"], "unique_labels": table_profile["label_counts"]["unique"] if table_profile["label_counts"] else 0, "requires_join": not (has_source and has_identifier)}, indent=2))


if __name__ == "__main__":
    main()
