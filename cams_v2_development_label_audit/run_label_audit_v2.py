#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

import run_label_audit as v1


def parse_development_member_v2(stream) -> dict:
    year_counts: Counter[int] = Counter()
    totals: Counter[str] = Counter()
    token_counts: Counter[str] = Counter()
    token_phases: dict[str, list[float]] = defaultdict(list)
    background_bins: Counter[int] = Counter()
    record_number = 0
    label_decodes = 0
    blind_label_decodes = 0
    missing_sh_header_records = 0

    while record_number < v1.DEVELOPMENT_RECORDS:
        seen: Counter[str] = Counter()
        year_value: float | None = None
        phase_value: float | None = None
        shower_present = False
        shower_opaque: str | None = None

        while True:
            header = v1.read_required_line(
                stream, f"record {record_number + 1} field header"
            )
            padded = header.ljust(8)
            flag = padded[:4]
            qnt = padded[4:6]
            if flag == "   &":
                break

            seen[flag] += 1
            value_line: str | None = None
            if flag == "ANo:" and qnt != " 1":
                value_line = None
            else:
                value_line = v1.read_required_line(
                    stream, f"record {record_number + 1} value for {flag!r}"
                )

            if flag == "Yr :":
                if qnt != " 1" or value_line is None:
                    raise RuntimeError(
                        f"record {record_number + 1}: missing Yr value"
                    )
                year_value = v1.parse_numeric(
                    value_line, "Yr", record_number + 1
                )
            elif flag == "LS :":
                if qnt != " 1" or value_line is None:
                    raise RuntimeError(
                        f"record {record_number + 1}: missing LS value"
                    )
                phase_value = v1.parse_numeric(
                    value_line, "LS", record_number + 1
                )
            elif flag == "Sh :":
                shower_present = qnt == " 1"
                if shower_present:
                    if value_line is None:
                        raise RuntimeError(
                            f"record {record_number + 1}: missing Sh value line"
                        )
                    shower_opaque = value_line[:2].ljust(2)
                else:
                    shower_opaque = None

        record_number += 1
        totals["parsed_records"] += 1

        for required_flag in ("Yr :", "LS :"):
            if seen[required_flag] != 1:
                raise RuntimeError(
                    f"record {record_number}: expected exactly one "
                    f"{required_flag!r}, found {seen[required_flag]}"
                )
        if seen["Sh :"] > 1:
            raise RuntimeError(
                f"record {record_number}: expected at most one 'Sh :', "
                f"found {seen['Sh :']}"
            )
        if seen["Sh :"] == 0:
            missing_sh_header_records += 1
            shower_present = False
            shower_opaque = None

        if year_value is None or phase_value is None:
            raise RuntimeError(f"record {record_number}: incomplete Yr/LS state")
        year_rounded = int(round(year_value))
        if (
            abs(year_value - year_rounded) > 1e-9
            or year_rounded not in (2010, 2011)
        ):
            raise RuntimeError(
                f"record {record_number}: development year outside 2010-2011"
            )
        year_counts[year_rounded] += 1

        if not (0.0 <= phase_value < 360.0):
            totals["invalid_phase"] += 1
            continue
        if v1.BLIND_LO <= phase_value <= v1.BLIND_HI:
            totals["blind_excluded"] += 1
            continue

        totals["post_boundary"] += 1
        label_decodes += 1
        if (
            not shower_present
            or shower_opaque is None
            or shower_opaque == "  "
        ):
            totals["background"] += 1
            phase_bin = int(math.floor(phase_value / 10.0)) % 36
            if phase_bin not in v1.PARTIAL_BLIND_BINS:
                background_bins[phase_bin] += 1
            continue

        token = shower_opaque.strip(" ")
        if v1.LABEL_RE.fullmatch(token):
            totals["mapped"] += 1
            token_counts[token] += 1
            token_phases[token].append(phase_value)
        else:
            totals["unsupported"] += 1

    if record_number != v1.DEVELOPMENT_RECORDS:
        raise RuntimeError(
            f"parsed {record_number} records, expected {v1.DEVELOPMENT_RECORDS}"
        )

    total_support = {
        str(threshold): sum(count >= threshold for count in token_counts.values())
        for threshold in (4, 8, 12, 20)
    }
    window_max = {
        token: v1.max_circular_window_count(phases, 20.0)
        for token, phases in token_phases.items()
    }
    window_support = {
        str(threshold): sum(count >= threshold for count in window_max.values())
        for threshold in (4, 6, 8, 12)
    }
    phase_bin_support = {
        str(threshold): sum(count >= threshold for count in background_bins.values())
        for threshold in (128, 256, 512)
    }

    label_like = totals["mapped"] + totals["unsupported"]
    mapping_fraction = totals["mapped"] / label_like if label_like else 0.0
    unsupported_fraction = (
        totals["unsupported"] / totals["post_boundary"]
        if totals["post_boundary"]
        else 1.0
    )

    return {
        "parser_version": "v2",
        "sole_parser_change": (
            "zero Sh headers means absent/background; one allowed; duplicates fatal"
        ),
        "development_records_parsed": record_number,
        "year_counts": {
            str(year): year_counts[year] for year in sorted(year_counts)
        },
        "records_with_omitted_sh_field": missing_sh_header_records,
        "invalid_phase_rows": totals["invalid_phase"],
        "blind_interval_rows": totals["blind_excluded"],
        "post_boundary_rows": totals["post_boundary"],
        "background_rows": totals["background"],
        "mapped_label_rows": totals["mapped"],
        "unsupported_rows": totals["unsupported"],
        "mapping_fraction_among_label_like": mapping_fraction,
        "unsupported_fraction_of_post_boundary": unsupported_fraction,
        "distinct_mapped_tokens": len(token_counts),
        "total_support_counts": total_support,
        "circular_20deg_window_support_counts": window_support,
        "background_10deg_bin_support_counts": phase_bin_support,
        "label_decodes_after_boundary": label_decodes,
        "blind_label_decodes": blind_label_decodes,
        "token_identities_emitted": False,
        "detailed_phase_bins_emitted": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    out = Path(args.output)

    v1.parse_development_member = parse_development_member_v2
    try:
        result = v1.build_result()
        result["method"] = (
            "Historical CAMS Database 2.0 aggregate-only "
            "development-label audit parser v2"
        )
        result["parser_version"] = "v2"
        result["sole_parser_change"] = (
            "omitted Sh field is absent/background per reading.f initialization"
        )
    except Exception as exc:
        result = {
            "method": (
                "Historical CAMS Database 2.0 aggregate-only "
                "development-label audit parser v2"
            ),
            "parser_version": "v2",
            "sole_parser_change": (
                "omitted Sh field is absent/background per reading.f initialization"
            ),
            "error": f"{type(exc).__name__}: {exc}",
            "requested_urls": [v1.ARCHIVE_URL],
            "geometry_values_decoded": False,
            "detector_scores_computed": False,
            "reserved_label_values_decoded": False,
            "sonotaco_2024_read": False,
            "camsv3_2016_values_read": False,
            "gates": {"execution_completed": False},
            "verdict": "KILL_HISTORICAL_CAMSV2_DEVELOPMENT_LABEL_INTERFACE",
        }

    v1.write_outputs(out, result)
    print(
        json.dumps(
            {
                "verdict": result["verdict"],
                "parser_version": result.get("parser_version"),
                "audit": result.get("audit"),
                "gates": result.get("gates"),
                "error": result.get("error"),
            },
            indent=2,
        )
    )
    if result["verdict"] != "PASS_HISTORICAL_CAMSV2_DEVELOPMENT_LABEL_INTERFACE":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
