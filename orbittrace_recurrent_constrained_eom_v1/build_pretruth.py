#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import hdbscan
import numpy as np
from hdbscan._hdbscan_tree import compute_stability

import rc_eom

YEARS = (2013, 2014)
ROUTES = ("sugar", "hdbscan")
MIN_CLUSTER_SIZE = 10
MIN_SAMPLES = 10
ROW_SHA = {
    ("sugar", 2013): "47fb0b700fbf710c7b061eead343016bd8d182756eb0c7f406507c5739e4c4f8",
    ("sugar", 2014): "bc83c113e9a14b1c6e1ef460ca9a40e05df77f3a449fec6064f8910add04c912",
    ("hdbscan", 2013): "2433b556d4a859580ef5431d2307ef34c8fa4c15d42841a2ec7b0c11e5f1f158",
    ("hdbscan", 2014): "206692292b2ca252777e40c13c367880740d8e2576d27615f7ea94b7790e3f55",
}
EXPECTED = {
    ("sugar", 2013): 18638,
    ("sugar", 2014): 15400,
    ("hdbscan", 2013): 16028,
    ("hdbscan", 2014): 13283,
}


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def install_hdb_compat() -> None:
    import hdbscan.hdbscan_ as hi
    from sklearn.utils import check_array as sk_check_array

    def compat(*args: Any, **kwargs: Any) -> Any:
        if "ensure_all_finite" in kwargs:
            kwargs["force_all_finite"] = kwargs.pop("ensure_all_finite")
        return sk_check_array(*args, **kwargs)

    hi.check_array = compat


def geo_matrix(rows: list[dict[str, Any]]) -> np.ndarray:
    sol = np.radians(np.asarray([float(r["sol"]) % 360.0 for r in rows], dtype=float))
    lon = np.radians(np.asarray([float(r["sun_lon"]) for r in rows], dtype=float))
    lat = np.radians(np.asarray([float(r["ecl_lat"]) for r in rows], dtype=float))
    vg = np.asarray([float(r["vg"]) for r in rows], dtype=float)
    X = np.column_stack((
        np.cos(sol),
        np.sin(sol),
        np.sin(lon) * np.cos(lat),
        np.cos(lon) * np.cos(lat),
        np.sin(lat),
        vg / 72.0,
    ))
    req(X.shape == (len(rows), 6) and np.all(np.isfinite(X)), "invalid GEO6 matrix")
    return X


def canonical_from_labels(labels: np.ndarray) -> list[tuple[int, ...]]:
    return sorted(
        tuple(np.flatnonzero(labels == lab).tolist())
        for lab in sorted(int(x) for x in np.unique(labels) if int(x) >= 0)
    )


def canonical_from_memberships(memberships: dict[int, tuple[int, ...]]) -> list[tuple[int, ...]]:
    return sorted(tuple(v) for v in memberships.values())


def family_id(prefix: str, ids: list[str]) -> str:
    payload = prefix + "|" + "|".join(sorted(ids))
    return prefix + hashlib.sha256(payload.encode()).hexdigest()[:16]


def candidates(
    rows: list[dict[str, Any]],
    nodes: tuple[int, ...],
    memberships: dict[int, tuple[int, ...]],
    ordinary: dict[float, float],
    year_counts: dict[int, tuple[int, int]],
    prefix: str,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for node in nodes:
        idx = memberships[int(node)]
        ids = [str(rows[i]["id"]) for i in idx]
        years = [int(rows[i]["year"]) for i in idx]
        counts = (int(sum(y == YEARS[0] for y in years)), int(sum(y == YEARS[1] for y in years)))
        if int(node) in year_counts:
            req(counts == tuple(year_counts[int(node)]), f"annual descendant mismatch node={node}")
        out.append({
            "family_id": family_id(prefix, ids),
            "node_id": int(node),
            "event_ids": sorted(ids),
            "member_count": len(ids),
            "annual_member_count": {str(YEARS[0]): counts[0], str(YEARS[1]): counts[1]},
            "ordinary_stability": float(ordinary[float(node)]),
        })
    out.sort(key=lambda f: (-float(f["ordinary_stability"]), -int(f["member_count"]), str(f["family_id"])))
    for rank, row in enumerate(out, 1):
        row["rank"] = rank
    return out


def member_hashes(rows: list[dict[str, Any]]) -> list[str]:
    return [hashlib.sha256("|".join(sorted(map(str, r["event_ids"]))).encode()).hexdigest() for r in rows]


def audit_route(rows_root: Path, route: str) -> dict[str, Any]:
    pooled: list[dict[str, Any]] = []
    hashes: dict[str, str] = {}
    for year in YEARS:
        path = rows_root / f"{route}_{year}.json"
        req(path.exists(), f"missing {path}")
        digest = sha256(path)
        req(digest == ROW_SHA[(route, year)], f"row hash drift {route} {year}: {digest}")
        rows = json.loads(path.read_text())
        req(isinstance(rows, list) and len(rows) == EXPECTED[(route, year)], f"row-count drift {route} {year}")
        for row in rows:
            # Label-bearing fields may be physically present in the historical transport,
            # but this program never reads them. Only ID/year/GEO6 geometry is consumed.
            req(int(row["year"]) == year, f"row-year mismatch {route} {year}")
        pooled.extend(rows)
        hashes[str(year)] = digest

    req(len({str(r["id"]) for r in pooled}) == len(pooled), f"duplicate IDs on {route}")
    X = geo_matrix(pooled)
    years = np.asarray([int(r["year"]) for r in pooled], dtype=np.int64)

    model = hdbscan.HDBSCAN(
        min_cluster_size=MIN_CLUSTER_SIZE,
        min_samples=MIN_SAMPLES,
        metric="euclidean",
        cluster_selection_method="eom",
        cluster_selection_epsilon=0.0,
        allow_single_cluster=False,
        prediction_data=False,
    ).fit(X)
    tree = model.condensed_tree_._raw_tree
    ordinary = compute_stability(tree)

    ordinary_nodes = rc_eom.select_eom_nodes(tree, ordinary, None)
    ordinary_memberships = rc_eom.selected_memberships(tree, ordinary_nodes)
    req(
        canonical_from_memberships(ordinary_memberships) == canonical_from_labels(np.asarray(model.labels_, dtype=int)),
        f"manual ordinary-EOM extraction diverged from hdbscan on {route}",
    )

    rc_nodes, ordinary2, year_counts, eligible = rc_eom.recurrent_constrained_eom(tree, years)
    req(ordinary2 == ordinary, f"ordinary stability changed inside RC-EOM on {route}")
    rc_memberships = rc_eom.selected_memberships(tree, rc_nodes)

    ordinary_candidates = candidates(
        pooled, ordinary_nodes, ordinary_memberships, ordinary, year_counts, f"ORD-{route}-"
    )
    rc_candidates = candidates(
        pooled, rc_nodes, rc_memberships, ordinary, year_counts, f"RCEOM-{route}-"
    )
    req(all(min(v["annual_member_count"].values()) >= rc_eom.MIN_ANNUAL_SUPPORT for v in rc_candidates),
        f"ineligible RC-EOM candidate on {route}")

    ordinary_ineligible = [
        {
            "rank": int(row["rank"]),
            "node_id": int(row["node_id"]),
            "annual_member_count": row["annual_member_count"],
            "member_count": int(row["member_count"]),
        }
        for row in ordinary_candidates
        if not bool(eligible.get(int(row["node_id"]), False))
    ]
    ord_hash = member_hashes(ordinary_candidates)
    rc_hash = member_hashes(rc_candidates)
    overlap = {
        str(k): len(set(ord_hash[:k]).intersection(rc_hash[:k]))
        for k in (10, 20, 40, 50, 100)
    }
    return {
        "route": route,
        "row_sha256": hashes,
        "event_count": len(pooled),
        "events_by_year": {str(y): int(np.sum(years == y)) for y in YEARS},
        "ordinary_candidate_count": len(ordinary_candidates),
        "rc_eom_candidate_count": len(rc_candidates),
        "mechanism_active": ordinary_nodes != rc_nodes,
        "ordinary_selected_nodes": list(map(int, ordinary_nodes)),
        "rc_eom_selected_nodes": list(map(int, rc_nodes)),
        "ordinary_ineligible_selected_count": len(ordinary_ineligible),
        "ordinary_ineligible_selected": ordinary_ineligible,
        "ordinary_only_node_count": len(set(ordinary_nodes) - set(rc_nodes)),
        "rc_only_node_count": len(set(rc_nodes) - set(ordinary_nodes)),
        "topk_exact_membership_overlap": overlap,
        "ordinary_assigned_event_count": int(sum(len(x) for x in ordinary_memberships.values())),
        "rc_eom_assigned_event_count": int(sum(len(x) for x in rc_memberships.values())),
        "ordinary_candidates": ordinary_candidates,
        "rc_eom_candidates": rc_candidates,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    install_hdb_compat()

    routes = {route: audit_route(args.rows_root, route) for route in ROUTES}
    active = any(v["mechanism_active"] for v in routes.values())
    result = {
        "schema": "ORBITTRACE_RECURRENT_CONSTRAINED_EOM_V1_PRETRUTH",
        "scientific_role": "LABEL_FREE_ACTIVITY_AND_INVARIANCE_AUDIT_ON_EXACT_PAPER_INPUTS",
        "method": {
            "hierarchy": "pooled GEO6 HDBSCAN",
            "min_cluster_size": MIN_CLUSTER_SIZE,
            "min_samples": MIN_SAMPLES,
            "cluster_selection": "ordinary EOM maximized over nodes with >=4 members in each year",
            "annual_support": rc_eom.MIN_ANNUAL_SUPPORT,
            "ranking": "ordinary EOM stability",
        },
        "routes": routes,
        "mechanism_active_any_route": active,
        "truth_accessed": False,
        "shower_label_fields_accessed": False,
        "post_activity_method_change_authorized": False,
    }
    req(active, "RC-EOM is structurally inactive on both paper routes")
    out = args.output / "RC_EOM_V1_PRETRUTH.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "schema": result["schema"],
        "truth_accessed": False,
        "routes": {
            k: {
                "ordinary_candidates": v["ordinary_candidate_count"],
                "rc_candidates": v["rc_eom_candidate_count"],
                "ordinary_ineligible": v["ordinary_ineligible_selected_count"],
                "ordinary_only_nodes": v["ordinary_only_node_count"],
                "rc_only_nodes": v["rc_only_node_count"],
                "topk_overlap": v["topk_exact_membership_overlap"],
            }
            for k, v in routes.items()
        },
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
