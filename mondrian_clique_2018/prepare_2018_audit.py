#!/usr/bin/env python3
"""Derive and run the frozen one-year 2018 audit from the exact PR #14 source."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BASE_SOURCE = Path("real_shower_meta_stage0/audit_real_shower_data.py")
EXPECTED_BLOB = "4a029051230f7c6e99b09e911f8a9e5228a58783"
DERIVED_SOURCE = Path("/tmp/audit_2018_data.py")


def main() -> None:
    blob = subprocess.check_output(
        ["git", "hash-object", str(BASE_SOURCE)], text=True
    ).strip()
    if blob != EXPECTED_BLOB:
        raise RuntimeError(f"base audit blob mismatch: {blob}")

    source = BASE_SOURCE.read_text(encoding="utf-8")
    replacements = {
        'OUT_DIR = ROOT / "results" / "data_audit"':
            'OUT_DIR = Path("mondrian_clique_2018/results/data_audit")',
        "YEARS = (2019, 2021, 2023, 2025)": "YEARS = (2018,)",
        '''        profile["eligible"] = bool(
            profile["quality_events"] >= 200
            and profile["represented_years"] >= 3
            and profile["years_ge_20"] >= 3
        )''': '''        profile["eligible"] = bool(
            profile["quality_events"] >= 200
            and profile["represented_years"] == 1
            and profile["years_ge_20"] == 1
        )''',
        'profile["strong"] = bool(profile["quality_events"] >= 1000 and profile["represented_years"] == 4)':
            'profile["strong"] = bool(profile["quality_events"] >= 300 and profile["represented_years"] == 1)',
        '"strong_showers_at_least_12": len(strong) >= 12':
            '"strong_showers_at_least_8": len(strong) >= 8',
        '"multi_shower_complex_units_at_least_6": len(multi_shower_complexes) >= 6':
            '"multi_shower_complex_units_at_least_2": len(multi_shower_complexes) >= 2',
        '"quality_sporadics_at_least_200000": total_sporadic_quality >= 200_000':
            '"quality_sporadics_at_least_50000": total_sporadic_quality >= 50_000',
        "GhostStream was excluded. Data came from 48 official GMN monthly trajectory summaries and the IAU MDC shower file.":
            "Fresh confirmation data came from 12 official 2018 GMN monthly trajectory summaries and the IAU MDC shower file.",
    }

    for old, new in replacements.items():
        count = source.count(old)
        if count != 1:
            raise RuntimeError(
                f"expected exactly one source occurrence for {old!r}; got {count}"
            )
        source = source.replace(old, new)

    DERIVED_SOURCE.write_text(source, encoding="utf-8")
    subprocess.run(
        [sys.executable, "-m", "py_compile", str(DERIVED_SOURCE)], check=True
    )
    print(f"derived audit bytes: {DERIVED_SOURCE.stat().st_size}")
    subprocess.run([sys.executable, str(DERIVED_SOURCE)], check=True)


if __name__ == "__main__":
    main()
