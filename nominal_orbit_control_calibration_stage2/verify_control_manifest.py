from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

TARGET_KEYS = ("a", "q", "e", "inc", "peri", "node", "sol", "ra", "dec", "vg")
CATALOGUE_MAP = {
    "a": "a",
    "q": "q",
    "e": "e",
    "inc": "inc",
    "peri": "peri",
    "node": "node",
    "sol": "LoS",
    "ra": "Ra",
    "dec": "De",
    "vg": "Vg",
}


def finite(value: Any) -> float | None:
    try:
        parsed = float(value)
    except Exception:
        return None
    return parsed if math.isfinite(parsed) else None


def build_selection(catalogue: dict[str, Any]) -> list[dict[str, Any]]:
    eligible: list[dict[str, Any]] = []
    for shower in catalogue["data"]:
        code = str(shower.get("Code") or "").strip()
        if code == "NOP":
            continue
        iau_number = str(shower.get("IAUNo") or "").strip()
        for solution in shower.get("solution", []):
            lookup_filename = str(solution.get("LT") or "").strip()
            try:
                membership = int(float(solution.get("N")))
            except Exception:
                continue
            if str(solution.get("s") or "").strip() != "1":
                continue
            if not lookup_filename or lookup_filename.lower() == "lookuptablefilename":
                continue
            if not 50 <= membership <= 2000:
                continue
            target = {
                key: finite(solution.get(catalogue_key))
                for key, catalogue_key in CATALOGUE_MAP.items()
            }
            if any(value is None for value in target.values()):
                continue
            speed = float(target["vg"])
            inclination = float(target["inc"])
            if speed < 30 and inclination < 60:
                stratum = "slow_low"
            elif 30 <= speed < 50 and inclination < 60:
                stratum = "mid_low"
            elif 30 <= speed < 50 and inclination >= 60:
                stratum = "mid_high"
            elif speed >= 50 and inclination >= 60:
                stratum = "fast_high"
            else:
                continue
            amendment = str(solution.get("AdNo") or "").zfill(3)
            identity = f"{iau_number}:{code}:{amendment}:{lookup_filename}"
            selection_hash = hashlib.sha256(identity.encode("utf-8")).hexdigest()
            eligible.append(
                {
                    "identity": identity,
                    "selection_sha256": selection_hash,
                    "stratum": stratum,
                    "iau_number": iau_number,
                    "code": code,
                    "solution": amendment,
                    "lookup_filename": lookup_filename,
                    "catalogue_n": membership,
                    "target": target,
                }
            )

    selected: list[dict[str, Any]] = []
    for stratum in ("slow_low", "mid_low", "mid_high", "fast_high"):
        seen_codes: set[str] = set()
        for record in sorted(
            (item for item in eligible if item["stratum"] == stratum),
            key=lambda item: item["selection_sha256"],
        ):
            if record["code"] in seen_codes:
                continue
            selected.append(record)
            seen_codes.add(record["code"])
            if len(seen_codes) == 3:
                break
    return selected


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalogue", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    catalogue = json.loads(args.catalogue.read_text(encoding="utf-8"))
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    expected = build_selection(catalogue)
    actual = manifest["controls"]

    checks = {
        "catalogue_version_matches": str(catalogue.get("version")) == str(manifest.get("catalogue_version")),
        "exactly_12_expected": len(expected) == 12,
        "exactly_12_manifest": len(actual) == 12,
        "identities_match": [item["identity"] for item in expected] == [item["identity"] for item in actual],
        "selection_hashes_match": [item["selection_sha256"] for item in expected]
        == [item["selection_sha256"] for item in actual],
        "lookup_filenames_match": [item["lookup_filename"] for item in expected]
        == [item["lookup_filename"] for item in actual],
        "catalogue_memberships_match": [item["catalogue_n"] for item in expected]
        == [item["catalogue_n"] for item in actual],
    }
    target_mismatches: list[dict[str, Any]] = []
    for expected_item, actual_item in zip(expected, actual):
        for key in TARGET_KEYS:
            expected_value = float(expected_item["target"][key])
            actual_value = float(actual_item["target"][key])
            if abs(expected_value - actual_value) > 1e-12:
                target_mismatches.append(
                    {
                        "identity": expected_item["identity"],
                        "key": key,
                        "expected": expected_value,
                        "actual": actual_value,
                    }
                )
    checks["targets_match"] = not target_mismatches
    passed = all(checks.values())
    payload = {
        "catalogue_version": catalogue.get("version"),
        "checks": checks,
        "target_mismatches": target_mismatches,
        "expected_selection": expected,
        "manifest_selection": actual,
        "passed": passed,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not passed:
        raise RuntimeError("Frozen control manifest does not reproduce from the exact catalogue snapshot")
    print("Verified frozen 12-control selection against catalogue", catalogue.get("version"))


if __name__ == "__main__":
    main()
