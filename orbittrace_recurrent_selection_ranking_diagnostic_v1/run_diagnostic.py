#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import hdbscan
import numpy as np
from hdbscan._hdbscan_tree import compute_stability

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "orbittrace_recurrent_eom_hdbscan_v1"))
import recurrent_eom as reom  # noqa: E402

YEARS = (2013, 2014)
ROUTES = ("sugar", "hdbscan")
BUDGETS = (10, 14, 20, 40, 43, 50, 100)
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
    X = np.column_stack((np.cos(sol), np.sin(sol), np.sin(lon)*np.cos(lat), np.cos(lon)*np.cos(lat), np.sin(lat), vg/72.0))
    req(X.shape == (len(rows), 6) and np.all(np.isfinite(X)), "invalid GEO6")
    return X


def member_hash(ids: list[str]) -> str:
    return hashlib.sha256("|".join(sorted(ids)).encode()).hexdigest()


def catalogue_from_labels(
    rows: list[dict[str, Any]], labels: np.ndarray, nodes: tuple[int, ...],
    ordinary: dict[float, float], recurrent: dict[float, float] | None,
) -> list[dict[str, Any]]:
    pos = sorted(int(x) for x in np.unique(labels) if int(x) >= 0)
    req(pos == list(range(len(nodes))), "compact-label/node mapping changed")
    out=[]
    for lab,node in enumerate(nodes):
        idx=np.flatnonzero(labels==lab)
        ids=sorted(str(rows[int(i)]["id"]) for i in idx)
        row={
            "node_id": int(node),
            "member_hash": member_hash(ids),
            "member_count": len(ids),
            "ordinary_stability": float(ordinary[float(node)]),
        }
        if recurrent is not None:
            row["recurrent_stability"] = float(recurrent[float(node)])
        out.append(row)
    if recurrent is None:
        out.sort(key=lambda x:(-x["ordinary_stability"],-x["member_count"],x["member_hash"]))
    else:
        out.sort(key=lambda x:(-x["recurrent_stability"],-x["ordinary_stability"],-x["member_count"],x["member_hash"]))
    for rank,row in enumerate(out,1): row["rank"]=rank
    return out


def compare_catalogues(ordinary: list[dict[str,Any]], recurrent: list[dict[str,Any]]) -> dict[str,Any]:
    ord_rank={r["member_hash"]:int(r["rank"]) for r in ordinary}
    rec_rank={r["member_hash"]:int(r["rank"]) for r in recurrent}
    ord_set=set(ord_rank); rec_set=set(rec_rank)
    budgets={}
    for k in BUDGETS:
        o=[r["member_hash"] for r in ordinary[:k]]
        r=[x["member_hash"] for x in recurrent[:k]]
        so,sr=set(o),set(r)
        budgets[str(k)]={
            "ordinary_count": len(o),
            "recurrent_count": len(r),
            "set_overlap": len(so&sr),
            "same_set": so==sr,
            "same_rank_positions": sum(a==b for a,b in zip(o,r)),
            "recurrent_topk_absent_from_ordinary_full": sum(h not in ord_set for h in r),
            "ordinary_topk_absent_from_recurrent_full": sum(h not in rec_set for h in o),
            "recurrent_topk_memberships": [
                {"recurrent_rank":i+1,"ordinary_rank":ord_rank.get(h),"absent_from_ordinary":h not in ord_set}
                for i,h in enumerate(r)
            ],
        }
    common=ord_set&rec_set
    shifts=sorted(
        ({"member_hash":h,"ordinary_rank":ord_rank[h],"recurrent_rank":rec_rank[h],"rank_delta_recurrent_minus_ordinary":rec_rank[h]-ord_rank[h]} for h in common),
        key=lambda z:(abs(z["rank_delta_recurrent_minus_ordinary"]),-z["ordinary_rank"]),reverse=True
    )
    return {
        "ordinary_candidate_count":len(ordinary),
        "recurrent_candidate_count":len(recurrent),
        "full_exact_membership_overlap":len(common),
        "ordinary_only_memberships":len(ord_set-rec_set),
        "recurrent_only_memberships":len(rec_set-ord_set),
        "budgets":budgets,
        "largest_common_membership_rank_shifts":shifts[:50],
    }


def route(rows_root:Path, route_name:str)->dict[str,Any]:
    rows=[]
    for y in YEARS:
        p=rows_root/f"{route_name}_{y}.json"
        req(p.exists(),f"missing {p}")
        req(sha256(p)==ROW_SHA[(route_name,y)],f"row hash drift {route_name} {y}")
        part=json.loads(p.read_text()); req(len(part)==EXPECTED[(route_name,y)],"row count drift")
        rows.extend(part)
    X=geo_matrix(rows); years=np.asarray([int(r["year"]) for r in rows],dtype=np.int64)
    model=hdbscan.HDBSCAN(min_cluster_size=10,min_samples=10,metric="euclidean",cluster_selection_method="eom",cluster_selection_epsilon=0.0,allow_single_cluster=False,prediction_data=False).fit(X)
    tree=model.condensed_tree_._raw_tree
    ordinary=compute_stability(tree)
    ordinary_nodes=reom.selected_eom_nodes(tree,ordinary)
    ordinary_labels=reom.eom_labels(tree,ordinary)
    req(sorted(tuple(np.flatnonzero(model.labels_==lab)) for lab in np.unique(model.labels_) if int(lab)>=0)==sorted(tuple(np.flatnonzero(ordinary_labels==lab)) for lab in np.unique(ordinary_labels) if int(lab)>=0),"ordinary custom extraction mismatch")
    recurrent,annual=reom.recurrent_stability(tree,years)
    recurrent_nodes=reom.selected_eom_nodes(tree,recurrent)
    recurrent_labels=reom.eom_labels(tree,recurrent)
    ordcat=catalogue_from_labels(rows,ordinary_labels,ordinary_nodes,ordinary,None)
    reccat=catalogue_from_labels(rows,recurrent_labels,recurrent_nodes,ordinary,recurrent)
    return {
        "event_count":len(rows),
        "events_by_year":{str(y):int(np.sum(years==y)) for y in YEARS},
        "comparison":compare_catalogues(ordcat,reccat),
        "truth_accessed":False,
        "shower_label_fields_accessed":False,
    }


def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--rows-root",type=Path,required=True); ap.add_argument("--output",type=Path,required=True); a=ap.parse_args()
    a.output.mkdir(parents=True,exist_ok=True); install_hdb_compat()
    result={
        "schema":"ORBITTRACE_RECURRENT_SELECTION_RANKING_DIAGNOSTIC_V1",
        "scientific_role":"ZERO_LABEL_DECOMPOSITION_OF_ORDINARY_VS_RECURRENT_EOM",
        "routes":{r:route(a.rows_root,r) for r in ROUTES},
        "truth_accessed":False,
        "shower_label_fields_accessed":False,
        "successor_selection_authorized":False,
    }
    out=a.output/"RESULT.json"; out.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({r:result["routes"][r]["comparison"] for r in ROUTES},indent=2,sort_keys=True))
    return 0

if __name__=="__main__": raise SystemExit(main())
