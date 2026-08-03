#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import requests

OUT = Path(__file__).resolve().parent / "results"
CACHE = Path(__file__).resolve().parent / "cache"
URL = "https://ceresiaumdc.ta3.sk/downloads/lists_shw_data/streamfulldata.json"

# Restricted to widely used canonical associations. This whitelist is a data-quality
# control for the Stage-0 proxy only; it is not a claim that every association is
# dynamically proven or unique.
CANONICAL_PARENT_PATTERNS = {
    "109P/Swift-Tuttle": [r"109P/Swift[- ]Tuttle"],
    "1P/Halley": [r"1P/Halley"],
    "(3200) Phaethon": [r"\(?3200\)?\s*Phaethon"],
    "(196256) 2003 EH1": [r"\(?196256\)?.*2003\s*EH1", r"2003\s*EH1"],
    "55P/Tempel-Tuttle": [r"55P/(?:Tempel|Temple)[- ]Tuttle"],
    "21P/Giacobini-Zinner": [r"21P/Giacobini[- ]Zinner"],
    "C/1861 G1 (Thatcher)": [r"C/1861\s*G1.*Thatcher", r"C/1861\s*G1"],
    "8P/Tuttle": [r"8P/Tuttle"],
    "169P/NEAT": [r"169P/NEAT"],
    "3D/Biela": [r"3D/Biela"],
    "7P/Pons-Winnecke": [r"7P/Pons[- ]Winnecke"],
    "73P/Schwassmann-Wachmann 3": [r"73P/Schwassmann[- ]Wachmann\s*3", r"73P/.*SW3"],
    "209P/LINEAR": [r"209P/LINEAR"],
    "289P/Blanpain": [r"289P/Blanpain"],
    "26P/Grigg-Skjellerup": [r"26P/Grigg[- ]Skjellerup"],
    "45P/Honda-Mrkos-Pajdusakova": [r"45P/Honda[- ]Mrkos[- ]Pajdusakova"],
    "C/1911 N1 (Kiess)": [r"C/1911\s*N1.*Kiess", r"C/1911\s*N1"],
    "C/1917 F1 (Mellish)": [r"C/1917\s*F1.*Mellish", r"C/1917\s*F1"],
}

REQUIRED_ORBIT = ("q", "e", "peri", "node", "inc")
REQUIRED_GEO = ("LoS", "Ra", "De", "Vg")


def download() -> tuple[dict[str, Any], dict[str, Any]]:
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / "streamfulldata.json"
    response = requests.get(URL, timeout=300)
    response.raise_for_status()
    raw = response.content
    path.write_bytes(raw)
    return response.json(), {
        "url": URL,
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "content_type": response.headers.get("content-type"),
    }


def text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).replace("\u00a0", " ").split())


def canonical_parent(raw: str) -> str | None:
    for canonical, patterns in CANONICAL_PARENT_PATTERNS.items():
        if any(re.search(pattern, raw, flags=re.I) for pattern in patterns):
            return canonical
    return None


def finite_number(value: Any) -> bool:
    if value is None or value == "":
        return False
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return number == number and abs(number) < 1e9


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    payload, download_meta = download()
    rows = []
    parent_raw_counter = Counter()
    for shower in payload.get("data", []):
        shower_status = text(shower.get("s"))
        shower_number = text(shower.get("IAUNo"))
        code = text(shower.get("Code"))
        name = text(shower.get("Name"))
        for solution in shower.get("solution", []) or []:
            solution_status = text(solution.get("s")) or shower_status
            raw_parent = text(solution.get("Parent body") or solution.get("Origin"))
            if raw_parent:
                parent_raw_counter[raw_parent] += 1
            parent = canonical_parent(raw_parent)
            row = {
                "parent": parent,
                "parent_raw": raw_parent,
                "shower_status": shower_status,
                "solution_status": solution_status,
                "iau_no": shower_number,
                "code": code,
                "name": name,
                "adno": text(solution.get("AdNo")),
                "N": int(float(solution.get("N"))) if finite_number(solution.get("N")) else None,
                "group": text(solution.get("Group")),
                "lookup": text(solution.get("LT") or solution.get("L-T")),
                **{field: solution.get(field) for field in (*REQUIRED_GEO, "dRa", "dDe", "S_LoR", "LaR", "a", *REQUIRED_ORBIT)},
            }
            row["complete_orbit"] = all(finite_number(row[field]) for field in REQUIRED_ORBIT)
            row["complete_geo"] = all(finite_number(row[field]) for field in REQUIRED_GEO)
            row["established"] = solution_status.strip() == "1" or shower_status.strip() == "1"
            row["enough_members"] = row["N"] is not None and row["N"] >= 20
            row["eligible"] = bool(parent and row["complete_orbit"] and row["complete_geo"] and row["established"] and row["enough_members"])
            rows.append(row)

    eligible = [row for row in rows if row["eligible"]]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in eligible:
        grouped[row["parent"]].append(row)

    parent_summary = []
    for parent, parent_rows in sorted(grouped.items()):
        showers = sorted({row["code"] or row["name"] for row in parent_rows})
        lookup_count = sum(bool(row["lookup"]) for row in parent_rows)
        parent_summary.append({
            "parent": parent,
            "solutions": len(parent_rows),
            "distinct_showers": len(showers),
            "showers": showers,
            "member_total": sum(row["N"] or 0 for row in parent_rows),
            "solutions_with_lookup_filename": lookup_count,
            "multi_branch": len(showers) >= 2,
        })

    usable_for_pair_learning = [item for item in parent_summary if item["solutions"] >= 2]
    usable_for_branch_test = [item for item in parent_summary if item["multi_branch"]]
    gate = {
        "minimum_parent_groups": 10,
        "minimum_multi_solution_parents": 8,
        "minimum_multi_branch_parents": 2,
        "parent_groups": len(parent_summary),
        "multi_solution_parents": len(usable_for_pair_learning),
        "multi_branch_parents": len(usable_for_branch_test),
    }
    gate["passed"] = (
        gate["parent_groups"] >= gate["minimum_parent_groups"]
        and gate["multi_solution_parents"] >= gate["minimum_multi_solution_parents"]
        and gate["multi_branch_parents"] >= gate["minimum_multi_branch_parents"]
    )
    verdict = "MDC_PROXY_DATA_GATE_PASS" if gate["passed"] else "MDC_PROXY_DATA_GATE_NO_GO"

    output = {
        "verdict": verdict,
        "download": download_meta,
        "mdc_version": payload.get("version"),
        "mdc_count": payload.get("count"),
        "selection": {
            "established_only": True,
            "minimum_reported_members": 20,
            "complete_geocentric_parameters": list(REQUIRED_GEO),
            "complete_orbital_parameters": list(REQUIRED_ORBIT),
            "canonical_parent_whitelist": list(CANONICAL_PARENT_PATTERNS),
        },
        "gate": gate,
        "parent_summary": parent_summary,
        "eligible_solutions": eligible,
        "top_unmapped_parent_strings": parent_raw_counter.most_common(100),
        "claim_boundary": (
            "A pass authorizes only a surrogate Stage-0 falsification test. MDC parent bodies are proposed literature associations, "
            "mean-shower solutions are not individual meteors, and perturbing those means is not a forward dynamical simulation."
        ),
    }
    (OUT / "mdc_proxy_feasibility.json").write_text(json.dumps(output, indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        "# MDC parent-disjoint proxy feasibility",
        "",
        f"**Verdict:** `{verdict}`",
        "",
        f"- MDC release: **{payload.get('version')}**",
        f"- Eligible canonical parent groups: **{len(parent_summary)}**",
        f"- Parent groups with at least two eligible solutions: **{len(usable_for_pair_learning)}**",
        f"- Parent groups with at least two distinct shower branches: **{len(usable_for_branch_test)}**",
        "",
        "## Eligible groups",
        "",
        "| Parent | Solutions | Showers | Reported members |",
        "|---|---:|---:|---:|",
    ]
    for item in parent_summary:
        lines.append(f"| {item['parent']} | {item['solutions']} | {item['distinct_showers']} | {item['member_total']} |")
    lines.extend([
        "",
        "## Interpretation boundary",
        "",
        "This is a proxy-data audit, not a dynamical validation. Published mean solutions and proposed parent associations can test whether the learning formulation is immediately hopeless, but they cannot establish a calibrated physical probability of common origin.",
    ])
    (OUT / "MDC_PROXY_FEASIBILITY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": verdict, "gate": gate, "parents": parent_summary}, indent=2))


if __name__ == "__main__":
    main()
