#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

EXPECTED_SCHEMA = "ORBITTRACE_RECURRENT_EOM_PAPER_EVIDENCE_V1"
EXPECTED_KERNEL = "30ac3fa3bc47910370df528fcf3ae8ecb6277b47"


def load_evidence(path: Path) -> dict:
    obj = json.loads(path.read_text())
    if obj.get("schema") != EXPECTED_SCHEMA:
        raise RuntimeError(f"unexpected evidence schema: {obj.get('schema')}")
    if obj.get("selected_kernel_git_blob") != EXPECTED_KERNEL:
        raise RuntimeError("selected recurrent-EOM kernel pin changed")
    if obj.get("selected_method") != "recurrent-EOM HDBSCAN v1":
        raise RuntimeError("selected method changed")
    if obj.get("protected_interval_inclusive") != [20.0, 55.0]:
        raise RuntimeError("protected interval changed")
    for key in (
        "target_information_access",
        "target_region_events_accessed",
        "maarsy_scientific_access",
        "dms_scientific_access",
    ):
        if obj.get(key) is not False:
            raise RuntimeError(f"firewall flag not false: {key}")
    return obj


def write_gmn_csv(e: dict, out: Path) -> None:
    rows = []
    for year in ("2022", "2023"):
        y = e["gmn_development"]["metrics"][year]
        for method_key, method_label in (("ordinary_eom", "Ordinary EOM"), ("recurrent_eom", "Recurrent-EOM")):
            m = y[method_key]
            rows.append({
                "year": year,
                "method": method_label,
                "recovered_at_25": m["recovered_at_25"],
                "recovered_at_50": m["recovered_at_50"],
                "recovered_at_100": m["recovered_at_100"],
                "recovered_at_500": m["recovered_at_500"],
                "top100_dominant_precision": m["top100_dominant_precision"],
                "mrr": m["mrr"],
                "qualified_matches": m["qualified_matches"],
                "fragmentation_median_top500": m["fragmentation_median_top500"],
            })
    path = out / "gmn_ordinary_vs_recurrent.csv"
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)


def write_sonotaco_csv(e: dict, out: Path) -> None:
    rows = []
    for p in e["sonotaco_exposed_benchmark"]["panels"]:
        rows.append({
            "route": p["route"],
            "year": p["year"],
            "budget": p["budget"],
            "recurrent_macro_f1": p["recurrent_macro_f1"],
            "recurrent_recovered": p["recurrent_recovered"],
            "v31_macro_f1": p["v31_macro_f1"],
            "v31_recovered": p["v31_recovered"],
            "literature_macro_f1": p["literature_macro_f1"],
            "literature_recovered": p["literature_recovered"],
            "delta_f1_vs_v31": p["recurrent_macro_f1"] - p["v31_macro_f1"],
            "delta_recovered_vs_v31": p["recurrent_recovered"] - p["v31_recovered"],
            "delta_f1_vs_literature": p["recurrent_macro_f1"] - p["literature_macro_f1"],
            "delta_recovered_vs_literature": p["recurrent_recovered"] - p["literature_recovered"],
        })
    path = out / "sonotaco_recurrent_vs_v31_literature.csv"
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)


def save(fig, out: Path, stem: str) -> None:
    fig.tight_layout()
    fig.savefig(out / f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(out / f"{stem}.png", dpi=240, bbox_inches="tight")
    plt.close(fig)


def plot_gmn(e: dict, out: Path) -> None:
    metrics = ("recovered_at_50", "recovered_at_100")
    labels = ("Recovered @50", "Recovered @100")
    years = ("2022", "2023")
    x = np.arange(len(metrics))
    width = 0.18
    fig, ax = plt.subplots(figsize=(7.4, 4.5))
    offsets = (-1.5, -0.5, 0.5, 1.5)
    series = []
    for yi, year in enumerate(years):
        for method_key, method_label in (("ordinary_eom", "Ordinary EOM"), ("recurrent_eom", "Recurrent-EOM")):
            vals = [e["gmn_development"]["metrics"][year][method_key][m] for m in metrics]
            series.append((year, method_label, vals))
    for off, (year, method, vals) in zip(offsets, series):
        bars = ax.bar(x + off * width, vals, width, label=f"{year} {method}")
        ax.bar_label(bars, padding=2, fontsize=8)
    ax.set_xticks(x, labels)
    ax.set_ylabel("Recovered known showers")
    ax.set_title("Target-excluded GMN: ordinary EOM vs recurrent-EOM")
    ax.legend(frameon=False, fontsize=8, ncol=2)
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, out, "figure_gmn_recovery")


def plot_sonotaco(e: dict, out: Path) -> None:
    panels = e["sonotaco_exposed_benchmark"]["panels"]
    names = [f"{p['route']}\n{p['year']}" for p in panels]
    recurrent = [p["recurrent_macro_f1"] for p in panels]
    v31 = [p["v31_macro_f1"] for p in panels]
    literature = [p["literature_macro_f1"] for p in panels]
    x = np.arange(len(panels))
    width = 0.25
    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    b1 = ax.bar(x - width, recurrent, width, label="Recurrent-EOM")
    b2 = ax.bar(x, v31, width, label="v31")
    b3 = ax.bar(x + width, literature, width, label="Frozen literature comparator")
    for bars in (b1, b2, b3):
        ax.bar_label(bars, fmt="%.3f", padding=2, fontsize=7, rotation=90)
    ax.set_xticks(x, names)
    ax.set_ylabel("Matched-budget macro-F1")
    ax.set_title("Exposed SonotaCo benchmark: recurrent-EOM vs controls")
    ax.legend(frameon=False, fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    ymax = max(recurrent + v31 + literature)
    ax.set_ylim(0, ymax * 1.22)
    save(fig, out, "figure_sonotaco_macro_f1")


def write_summary(e: dict, out: Path) -> None:
    g = e["gmn_development"]
    s = e["sonotaco_exposed_benchmark"]
    d = e["density_sync_direct_comparison"]
    text = f"""# Generated OrbitTrace paper-output summary

Generated exclusively from `ORBITTRACE_PAPER_EVIDENCE.json`; no event-level catalogue is read.

- Selected method: **{e['selected_method']}**
- Recurrent-EOM kernel: `{e['selected_kernel_git_blob']}`
- GMN development verdict: `{g['verdict']}`
- GMN binding run/artifact: `{g['run']}` / `{g['artifact']}`
- SonotaCo exposed benchmark verdict: `{s['verdict']}`
- SonotaCo v31 superiority panels: **{s['v31_superiority_panels']}/4**
- SonotaCo literature superiority panels: **{s['literature_superiority_panels']}/4**
- Density-sync direct verdict: `{d['verdict']}`
- Density-sync selection outcome: **{d['selection']}**
- Cross-survey external validation claim: **{e['limitations']['cross_survey_external_validation_claim']}**

`figure_gmn_recovery.*` visualizes the preregistered fixed-budget GMN recovery comparison.  
`figure_sonotaco_macro_f1.*` visualizes the four matched-budget exposed SonotaCo macro-F1 comparisons.  
The CSV files preserve all plotted values and associated recovery counts.
"""
    (out / "README.md").write_text(text)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    e = load_evidence(args.evidence)
    write_gmn_csv(e, args.output)
    write_sonotaco_csv(e, args.output)
    plot_gmn(e, args.output)
    plot_sonotaco(e, args.output)
    write_summary(e, args.output)
    print(json.dumps({
        "verdict": "PASS_ORBITTRACE_PAPER_OUTPUT_GENERATION_V1",
        "selected_method": e["selected_method"],
        "gmn_verdict": e["gmn_development"]["verdict"],
        "sonotaco_v31_wins": e["sonotaco_exposed_benchmark"]["v31_superiority_panels"],
        "sonotaco_literature_wins": e["sonotaco_exposed_benchmark"]["literature_superiority_panels"],
        "density_sync_direct_verdict": e["density_sync_direct_comparison"]["verdict"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
