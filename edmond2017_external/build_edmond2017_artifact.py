from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import urllib.request
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

YEAR = 2017
ARCHIVE_URL = "https://ceres.ta3.sk/iaumdcdb/dataDBs/video_offline/iaumdcedmond2017.csv.zip"
USER_AGENT = "ghoststream-edmond2017-external-gate/1.0"
BLIND_MIN = 20.0
BLIND_MAX = 55.0
WINDOW = 10.0
EPISODE_SIZE = 128
MIN_QC = 10.0
MIN_LABEL_EVENTS = 20
MIN_LOCAL_MEMBERS = 12

REQUIRED_COLUMNS = (
    "_#",
    "_sol",
    "_ra_t",
    "_dc_t",
    "_vg",
    "_stream",
    "_Qc",
    "_Y_ut",
    "_M_ut",
    "_D_ut",
    "_h_ut",
    "_m_ut",
    "_s_ut",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--archive", type=Path)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def as_float(value: str | None) -> float | None:
    text = (value or "").strip().replace("−", "-")
    if not text or text.lower() in {"nan", "none", "null", "na", "..."}:
        return None
    try:
        result = float(text)
    except ValueError:
        return None
    return result if math.isfinite(result) else None


def wrap180(value: float) -> float:
    return (value + 180.0) % 360.0 - 180.0


def normalize_stream(value: str | None) -> str | None:
    text = (value or "").strip()
    if not text:
        return None
    normalized = text.strip("_").strip().upper()
    return normalized or None


def download(path: Path) -> dict[str, Any]:
    request = urllib.request.Request(
        ARCHIVE_URL,
        headers={"User-Agent": USER_AGENT, "Accept": "*/*"},
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    total = 0
    with urllib.request.urlopen(request, timeout=900) as response, path.open("wb") as output:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            output.write(chunk)
            digest.update(chunk)
            total += len(chunk)
        return {
            "url": ARCHIVE_URL,
            "bytes": total,
            "sha256": digest.hexdigest(),
            "content_type": response.headers.get("Content-Type"),
            "last_modified": response.headers.get("Last-Modified"),
        }


def local_count(values: list[float], center: float) -> int:
    return sum(abs(wrap180(value - center)) <= WINDOW for value in values)


def parse_archive(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    member_records: list[dict[str, Any]] = []
    with zipfile.ZipFile(path) as bundle:
        members = [
            item
            for item in bundle.infolist()
            if not item.is_dir() and item.filename.lower().endswith(".csv")
        ]
        if not members:
            raise RuntimeError("EDMOND 2017 archive contains no CSV member")
        for member in members:
            with bundle.open(member) as raw:
                text = (line.decode("utf-8-sig", errors="replace") for line in raw)
                reader = csv.DictReader(text)
                headers = reader.fieldnames or []
                missing = [column for column in REQUIRED_COLUMNS if column not in headers]
                if missing:
                    raise RuntimeError(
                        f"Archive member {member.filename} missing required columns: {missing}"
                    )
                member_count = 0
                for index, raw_row in enumerate(reader):
                    year_value = as_float(raw_row.get("_Y_ut"))
                    if year_value is None or int(round(year_value)) != YEAR:
                        continue
                    member_count += 1
                    rows.append(
                        {
                            "member": member.filename,
                            "row_index": index + 2,
                            "raw": raw_row,
                        }
                    )
                member_records.append(
                    {
                        "member": member.filename,
                        "compressed_bytes": member.compress_size,
                        "uncompressed_bytes": member.file_size,
                        "headers": headers,
                        "year_rows": member_count,
                    }
                )
    return rows, {"members": member_records}


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    archive_path = args.archive or (args.output / "iaumdcedmond2017.csv.zip")
    if args.archive is None:
        source = download(archive_path)
    else:
        source = {
            "url": str(args.archive),
            "bytes": archive_path.stat().st_size,
            "sha256": sha256(archive_path),
            "content_type": None,
            "last_modified": None,
        }

    raw_rows, schema = parse_archive(archive_path)
    raw_year_rows = len(raw_rows)
    geometry_complete = 0
    quality_rows = 0
    unlabeled_excluded = 0
    blind_excluded = 0
    candidate_rows: list[dict[str, Any]] = []
    raw_label_counts: Counter[str] = Counter()

    for record in raw_rows:
        raw = record["raw"]
        sol = as_float(raw.get("_sol"))
        ra = as_float(raw.get("_ra_t"))
        dec = as_float(raw.get("_dc_t"))
        vg = as_float(raw.get("_vg"))
        qc = as_float(raw.get("_Qc"))
        if None in (sol, ra, dec, vg):
            continue
        geometry_complete += 1
        assert sol is not None and ra is not None and dec is not None and vg is not None
        if not (
            0.0 <= sol < 360.0
            and 0.0 <= ra < 360.0
            and -90.0 <= dec <= 90.0
            and 5.0 <= vg <= 80.0
        ):
            continue
        if qc is None or qc < MIN_QC:
            continue
        quality_rows += 1
        stream = normalize_stream(raw.get("_stream"))
        if stream is None:
            unlabeled_excluded += 1
            continue
        if BLIND_MIN <= sol <= BLIND_MAX:
            blind_excluded += 1
            continue
        event_id = (raw.get("_#") or "").strip() or f"{record['member']}:{record['row_index']}"
        is_sporadic = stream == "SPO"
        if not is_sporadic:
            raw_label_counts[stream] += 1
        candidate_rows.append(
            {
                "id": f"EDMOND2017:{event_id}",
                "year": YEAR,
                "sol": sol,
                "ra": ra,
                "dec": dec,
                "vg": vg,
                "stream": stream,
                "is_sporadic": is_sporadic,
                "qc": qc,
            }
        )

    sporadic_rows = [row for row in candidate_rows if row["is_sporadic"]]
    sporadic_sols = [float(row["sol"]) for row in sporadic_rows]
    by_stream: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        if not row["is_sporadic"]:
            by_stream[str(row["stream"])].append(row)

    supported_bins: list[int] = []
    maximum_background_by_bin: dict[str, int] = {}
    for phase_bin in range(36):
        centers = [value for value in sporadic_sols if int(value // 10.0) == phase_bin]
        best = max((local_count(sporadic_sols, center) for center in centers), default=0)
        maximum_background_by_bin[str(phase_bin)] = best
        if best >= EPISODE_SIZE:
            supported_bins.append(phase_bin)

    feasible_streams: list[str] = []
    stream_profiles: dict[str, Any] = {}
    for stream, members in sorted(by_stream.items()):
        member_sols = [float(row["sol"]) for row in members]
        feasible_centers = 0
        best_local_members = 0
        best_local_background = 0
        for center in member_sols:
            local_members = local_count(member_sols, center)
            local_background = local_count(sporadic_sols, center)
            best_local_members = max(best_local_members, local_members)
            best_local_background = max(best_local_background, local_background)
            if local_members >= MIN_LOCAL_MEMBERS and local_background >= EPISODE_SIZE - 4:
                feasible_centers += 1
        eligible = len(members) >= MIN_LABEL_EVENTS and feasible_centers > 0
        if eligible:
            feasible_streams.append(stream)
        stream_profiles[stream] = {
            "events": len(members),
            "best_local_members": best_local_members,
            "best_local_background": best_local_background,
            "feasible_centers": feasible_centers,
            "eligible": eligible,
            "strong": eligible and len(members) >= 100,
        }

    label_map = {
        stream: index + 1 for index, stream in enumerate(sorted(feasible_streams))
    }
    selected_events: list[dict[str, Any]] = []
    for row in candidate_rows:
        if row["is_sporadic"]:
            selected_events.append(
                {
                    "id": row["id"],
                    "year": YEAR,
                    "sol": row["sol"],
                    "ra": row["ra"],
                    "dec": row["dec"],
                    "vg": row["vg"],
                    "iau": -1,
                    "code": "SPO",
                    "complex_key": "SPORADIC",
                }
            )
        elif row["stream"] in label_map:
            stream = str(row["stream"])
            selected_events.append(
                {
                    "id": row["id"],
                    "year": YEAR,
                    "sol": row["sol"],
                    "ra": row["ra"],
                    "dec": row["dec"],
                    "vg": row["vg"],
                    "iau": label_map[stream],
                    "code": stream,
                    "complex_key": f"EDMOND:{stream}",
                }
            )

    selected_events.sort(
        key=lambda row: (int(row["iau"]), float(row["sol"]), str(row["id"]))
    )
    selected_sporadic = sum(int(row["iau"]) == -1 for row in selected_events)
    selected_labeled = len(selected_events) - selected_sporadic
    eligible_label_counts = Counter(
        str(row["code"]) for row in selected_events if int(row["iau"]) > 0
    )
    max_label_share = max(eligible_label_counts.values(), default=0) / max(
        1, selected_labeled
    )
    strong_count = sum(
        bool(stream_profiles[stream]["strong"]) for stream in feasible_streams
    )
    geometry_completeness = geometry_complete / max(1, raw_year_rows)

    gates = {
        "archive_nonempty": source["bytes"] > 0,
        "schema_has_required_columns": all(
            all(column in member["headers"] for column in REQUIRED_COLUMNS)
            for member in schema["members"]
        ),
        "raw_2017_rows_at_least_10000": raw_year_rows >= 10_000,
        "geometry_completeness_at_least_0_95": geometry_completeness >= 0.95,
        "quality_rows_at_least_8000": quality_rows >= 8_000,
        "selected_sporadics_at_least_5000": selected_sporadic >= 5_000,
        "eligible_streams_at_least_20": len(feasible_streams) >= 20,
        "strong_streams_at_least_5": strong_count >= 5,
        "supported_10deg_bins_at_least_20": len(supported_bins) >= 20,
        "largest_stream_share_at_most_0_25": max_label_share <= 0.25,
    }

    verdict = (
        "PROCEED_TO_EDMOND2017_EXTERNAL_CONFIRMATION"
        if all(gates.values())
        else "KILL_EDMOND2017_DATA_GATE"
    )
    audit = {
        "verdict": verdict,
        "configuration": {
            "year": YEAR,
            "archive_url": ARCHIVE_URL,
            "blind_interval": [BLIND_MIN, BLIND_MAX],
            "quality_qc_minimum": MIN_QC,
            "sporadic_label": "_spo",
            "minimum_label_events": MIN_LABEL_EVENTS,
            "minimum_local_members": MIN_LOCAL_MEMBERS,
            "window_halfwidth_deg": WINDOW,
            "episode_size": EPISODE_SIZE,
        },
        "source": source,
        "archive_sha256": sha256(archive_path),
        "schema": schema,
        "counts": {
            "raw_2017_rows": raw_year_rows,
            "geometry_complete_rows": geometry_complete,
            "quality_rows": quality_rows,
            "unlabeled_excluded": unlabeled_excluded,
            "blind_interval_excluded": blind_excluded,
            "selected_events": len(selected_events),
            "selected_sporadics": selected_sporadic,
            "selected_labeled": selected_labeled,
            "raw_distinct_streams": len(raw_label_counts),
            "eligible_streams": len(feasible_streams),
            "strong_streams": strong_count,
            "supported_10deg_bins": len(supported_bins),
        },
        "geometry_completeness": geometry_completeness,
        "supported_10deg_bins": supported_bins,
        "maximum_background_by_bin": maximum_background_by_bin,
        "eligible_stream_codes": sorted(feasible_streams),
        "label_map": label_map,
        "stream_profiles": stream_profiles,
        "largest_eligible_stream_share": max_label_share,
        "gates": gates,
    }

    with gzip.open(
        args.output / "selected_events.jsonl.gz", "wt", encoding="utf-8"
    ) as handle:
        for event in selected_events:
            handle.write(
                json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n"
            )
    (args.output / "audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True)
    )
    (args.output / "EDMOND2017_DATA_GATE.md").write_text(
        "# EDMOND 2017 external data gate\n\n"
        f"- verdict: **{verdict}**\n"
        f"- raw 2017 rows: **{raw_year_rows:,}**\n"
        f"- quality rows: **{quality_rows:,}**\n"
        f"- selected sporadics: **{selected_sporadic:,}**\n"
        f"- selected labeled: **{selected_labeled:,}**\n"
        f"- eligible / strong stream codes: **{len(feasible_streams)} / {strong_count}**\n"
        f"- supported 10-degree bins: **{len(supported_bins)}**\n"
        f"- geometry completeness: **{geometry_completeness:.6f}**\n"
        f"- largest eligible-stream share: **{max_label_share:.6f}**\n"
    )
    print(
        json.dumps(
            {"verdict": verdict, "counts": audit["counts"], "gates": gates},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
