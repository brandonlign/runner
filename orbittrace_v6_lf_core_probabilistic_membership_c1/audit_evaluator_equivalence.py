#!/usr/bin/env python3
from __future__ import annotations

import ast
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np

YEARS = (2022, 2023)
TOP_K = 100
SHARED_KEYS = (
    "eligible_labels",
    "qualified_matches",
    "recovered_at_100",
    "recovered_at_500",
    "mrr",
    "median_rank",
    "macro_f1",
    "top100_dominant_precision",
    "per_label",
)


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def function_source(path: Path, name: str) -> str:
    text = path.read_text()
    tree = ast.parse(text)
    matches = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name]
    require(len(matches) == 1, f"expected one {name} in {path}")
    source = ast.get_source_segment(text, matches[0])
    require(source is not None, f"cannot extract {name}")
    return source


def load_exact_evaluators(v6_path: Path, v8_mult_path: Path):
    # Execute only the exact frozen evaluator functions in a tiny synthetic namespace.
    # No catalogue, target data, or detector execution is involved.
    v6_ns: dict[str, Any] = {
        "Counter": Counter,
        "defaultdict": defaultdict,
        "np": np,
        "Any": Any,
    }
    exec(function_source(v6_path, "evaluate_families_v6"), v6_ns)

    v8_ns: dict[str, Any] = {
        "Counter": Counter,
        "defaultdict": defaultdict,
        "np": np,
        "Any": Any,
        "YEARS": YEARS,
        "TOP_K": TOP_K,
        "require": require,
    }
    exec(function_source(v8_mult_path, "eligible_labels"), v8_ns)
    exec(function_source(v8_mult_path, "evaluate_order"), v8_ns)
    return v6_ns["evaluate_families_v6"], v8_ns["evaluate_order"]


def family(fid: str, ids: list[str]) -> dict[str, Any]:
    return {"family_id": fid, "event_ids": list(ids), "event_count": len(ids)}


def deterministic_case() -> tuple[dict[str, str], list[dict[str, Any]], list[dict[str, Any]]]:
    labels: dict[str, str] = {}
    ids_by_label: dict[str, list[str]] = {}
    for label_index, label in enumerate(("AAA", "BBB", "CCC", "DDD", "EEE", "FFF"), start=1):
        ids: list[str] = []
        # Six events/year makes every named shower eligible; later families exercise
        # overlap, precision, rank, and best-F1 tie semantics.
        for year in YEARS:
            for index in range(6):
                eid = f"{year}{label_index:02d}{index:04d}"
                labels[eid] = label
                ids.append(eid)
        ids_by_label[label] = ids
    for year in YEARS:
        for index in range(80):
            labels[f"{year}99{index:04d}"] = "SPORADIC"

    primary = [
        family("VF0001", ids_by_label["AAA"][:10]),
        family("VF0002", ids_by_label["BBB"][:8] + [f"202299{n:04d}" for n in range(2)]),
        family("VF0003", ids_by_label["CCC"][:4] + [f"202399{n:04d}" for n in range(8)]),
        family("VF0004", ids_by_label["DDD"][:6] + ids_by_label["EEE"][:6]),
        family("VF0005", ids_by_label["EEE"][6:12]),
    ]
    # Push top-100 averaging through a >100-family universe with pure sporadic tails.
    for rank in range(6, 116):
        year = YEARS[rank % 2]
        primary.append(family(f"VF{rank:04d}", [f"{year}99{(rank + j) % 80:04d}" for j in range(4)]))
    rescue = [family("RF0001", ids_by_label["FFF"][:8])]
    return labels, primary, rescue


def generated_case(case_index: int) -> tuple[dict[str, str], list[dict[str, Any]], list[dict[str, Any]]]:
    rng = np.random.default_rng(1000 + case_index)
    labels: dict[str, str] = {}
    all_ids: list[str] = []
    shower_names = [f"S{index:02d}" for index in range(12)]
    for shower_index, label in enumerate(shower_names):
        for year in YEARS:
            count = int(rng.integers(3, 12))
            for index in range(count):
                eid = f"{year}{shower_index:02d}{case_index:02d}{index:03d}"
                labels[eid] = label
                all_ids.append(eid)
    for year in YEARS:
        for index in range(180):
            eid = f"{year}99{case_index:02d}{index:03d}"
            labels[eid] = "SPORADIC"
            all_ids.append(eid)

    primary: list[dict[str, Any]] = []
    id_array = np.asarray(all_ids, dtype=object)
    for rank in range(1, 126):
        size = int(rng.integers(4, 24))
        chosen = rng.choice(id_array, size=size, replace=False).tolist()
        primary.append(family(f"VF{rank:04d}", [str(value) for value in chosen]))
    rescue: list[dict[str, Any]] = []
    for rank in range(1, 8):
        size = int(rng.integers(4, 14))
        chosen = rng.choice(id_array, size=size, replace=False).tolist()
        rescue.append(family(f"RF{rank:04d}", [str(value) for value in chosen]))
    return labels, primary, rescue


def compare(v6_eval, v8_eval, labels, primary, rescue, tag: str) -> None:
    v6 = v6_eval(labels, primary, rescue, YEARS)
    order = [str(row["family_id"]) for row in primary]
    v8 = v8_eval(labels, primary, order)
    for key in SHARED_KEYS:
        require(key in v6 and key in v8, f"missing shared endpoint {key} in {tag}")
        if key in {"mrr", "macro_f1", "top100_dominant_precision"}:
            require(abs(float(v6[key]) - float(v8[key])) <= 1e-15, f"float endpoint mismatch {tag} {key}: {v6[key]} vs {v8[key]}")
        else:
            require(v6[key] == v8[key], f"endpoint mismatch {tag} {key}: {v6[key]} vs {v8[key]}")
    require(v6["v3_family_count"] == len(primary), f"v6 family count mismatch {tag}")
    require(v6["rescue_only_family_count"] == len(rescue), f"v6 rescue count mismatch {tag}")


def main() -> int:
    v6_path = Path("/tmp/v6_exact.py")
    v8_mult_path = Path("exact-v8/orbittrace_sparse_support_multiplicity_v5/run_holdout.py")
    require(v6_path.is_file(), "exact v6 source missing")
    require(v8_mult_path.is_file(), "exact v8 multiplicity evaluator source missing")
    v6_eval, v8_eval = load_exact_evaluators(v6_path, v8_mult_path)

    compare(v6_eval, v8_eval, *deterministic_case(), tag="deterministic")
    for index in range(25):
        compare(v6_eval, v8_eval, *generated_case(index), tag=f"generated-{index:02d}")

    print("PASS_C1_LF_PRIMARY_EVALUATOR_EXACT_ENDPOINT_EQUIVALENCE")
    print("cases=26 shared_endpoints=" + ",".join(SHARED_KEYS))
    print("rescue_only_affects_nonshared_v6_rescue_diagnostic=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
