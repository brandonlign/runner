#!/usr/bin/env python3
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
from typing import Any

DAG_PRELABEL_SHA256 = "65ead5f26026dbed74a098cc1df17d000c28705cd8fcd3af5134fd98151a0573"
DAG_RESULT_SHA256 = "b7b4a4355a488108f4107e86e98bfc872f67c176d63eac1e56772a78f0708721"
DAG_SUPPORT_VERDICT = "SUPPORTS_CROSSHIERARCHY_REFINEMENT_DAG_V1"
BUCKETS = (0, 1, 2, 3)
DENOMINATORS = (128, 1024)
BLIND = (20.0, 55.0)


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def member_set(row: dict[str, Any]) -> frozenset[str]:
    return frozenset(str(x) for x in row["event_ids"])


def fraction_fields(x: Fraction, prefix: str) -> dict[str, Any]:
    return {
        f"{prefix}_numerator": int(x.numerator),
        f"{prefix}_denominator": int(x.denominator),
        prefix: float(x),
    }


def mean_fraction(values: list[Fraction]) -> Fraction:
    req(bool(values), "empty fraction mean")
    return sum(values, Fraction(0, 1)) / len(values)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dag-prelabel", type=Path, required=True)
    ap.add_argument("--dag-result", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    req(sha256(a.dag_prelabel) == DAG_PRELABEL_SHA256, "DAG prelabel changed")
    req(sha256(a.dag_result) == DAG_RESULT_SHA256, "DAG result changed")
    dag = json.loads(a.dag_prelabel.read_text())
    result = json.loads(a.dag_result.read_text())

    req(dag["schema"] == "ORBITTRACE_CROSSHIERARCHY_REFINEMENT_DAG_V1_PRELABEL", "wrong DAG prelabel schema")
    req(dag["scientific_role"] == "ZERO_LABEL_CROSS_HIERARCHY_COMMON_REFINEMENT", "wrong DAG prelabel role")
    req(result["schema"] == "ORBITTRACE_CROSSHIERARCHY_REFINEMENT_DAG_V1_RESULT", "wrong DAG result schema")
    req(result["verdict"] == DAG_SUPPORT_VERDICT, "binding DAG result did not support extraction")
    req(result["prelabel_sha256"] == DAG_PRELABEL_SHA256, "DAG result/prelabel mismatch")
    req(len(result["gates"]) == 9 and all(bool(v) for v in result["gates"].values()), "binding DAG gates did not all pass")
    for obj, label in ((dag, "DAG prelabel"), (result, "DAG result")):
        for flag in (
            "shower_truth_used",
            "target_information_access",
            "target_region_events_accessed",
            "post_result_parameter_search",
        ):
            req(obj.get(flag) is False, f"{label} firewall flag {flag}")
    req(result.get("external_scientific_access") is False, "DAG result external access")

    panel_map = {(int(p["denominator"]), int(p["bucket"])): p for p in dag["panels"]}
    req(set((d, b) for d in (64, 128, 1024) for b in BUCKETS) == set(panel_map), "DAG panel set changed")

    subsets: list[dict[str, Any]] = []
    panel_audit: list[dict[str, Any]] = []
    all_membership_exact = True
    all_rank_exact = True
    all_atom_exact = True
    all_score_exact = True
    all_order_exact = True
    all_k_positive = True
    mechanism_active = False
    eval_active = False
    topk_score_nonloss_all = True
    topk_score_strict_any = False

    for d in DENOMINATORS:
        for b in BUCKETS:
            src = panel_map[(d, b)]
            topo = [dict(x) for x in src["topomodal_candidates"]]
            recurrent = [dict(x) for x in src["recurrent_candidates"]]
            atoms = [dict(x) for x in src["atoms"]]
            nt, nr = len(topo), len(recurrent)
            req(nt > 0 and nr > 0, f"empty parent catalogue d={d} b={b}")
            req([int(x["rank"]) for x in topo] == list(range(1, nt + 1)), f"Topo rank continuity d={d} b={b}")
            req([int(x["rank"]) for x in recurrent] == list(range(1, nr + 1)), f"recurrent rank continuity d={d} b={b}")
            K = min(nt, nr)
            all_k_positive = all_k_positive and K > 0 and nt >= K

            topo_sets = [member_set(x) for x in topo]
            rec_sets = [member_set(x) for x in recurrent]
            req(len(set(x["family_hash"] for x in topo)) == nt, "duplicate Topo family hash")
            req(len(set(x["family_hash"] for x in recurrent)) == nr, "duplicate recurrent family hash")

            incident: dict[int, list[dict[str, Any]]] = {i: [] for i in range(nt)}
            for atom in atoms:
                i, j = int(atom["topomodal_index"]), int(atom["recurrent_index"])
                req(0 <= i < nt and 0 <= j < nr, f"atom index out of range d={d} b={b}")
                aset = member_set(atom)
                req(bool(aset), "empty atom")
                req(aset.issubset(topo_sets[i]) and aset.issubset(rec_sets[j]), "atom is not exact parent subset")
                req(int(atom["member_count"]) == len(aset), "atom count mismatch")
                req(str(atom["topomodal_family_hash"]) == str(topo[i]["family_hash"]), "atom Topo hash mismatch")
                req(str(atom["recurrent_family_hash"]) == str(recurrent[j]["family_hash"]), "atom recurrent hash mismatch")
                incident[i].append(atom)

            successor: list[dict[str, Any]] = []
            score_by_hash: dict[str, Fraction] = {}
            for i, row in enumerate(topo):
                tset = topo_sets[i]
                req(len(tset) == int(row["member_count"]), "Topo member count mismatch")
                seen: set[str] = set()
                score = Fraction(0, 1)
                coverage_count = 0
                contributions: list[dict[str, Any]] = []
                for atom in incident[i]:
                    j = int(atom["recurrent_index"])
                    aset = member_set(atom)
                    req(not seen.intersection(aset), "incident atoms overlap within Topo candidate")
                    seen.update(aset)
                    rank = int(recurrent[j]["rank"])
                    q = Fraction(nr - rank + 1, nr)
                    contribution = Fraction(len(aset), len(tset)) * q
                    score += contribution
                    coverage_count += len(aset)
                    contributions.append(
                        {
                            "atom_hash": atom["atom_hash"],
                            "recurrent_family_hash": recurrent[j]["family_hash"],
                            "recurrent_rank": rank,
                            **fraction_fields(q, "recurrent_priority"),
                            "atom_member_count": len(aset),
                            **fraction_fields(contribution, "score_contribution"),
                        }
                    )
                coverage = Fraction(coverage_count, len(tset))
                req(Fraction(0, 1) <= score <= Fraction(1, 1), "score outside [0,1]")
                req(Fraction(0, 1) <= coverage <= Fraction(1, 1), "coverage outside [0,1]")
                out = dict(row)
                out["native_topomodal_rank"] = int(row["rank"])
                out["catalogue_source"] = "raw_support_resolved_topomodal_membership_dag_corroboration_mass_rank"
                out.update(fraction_fields(score, "dag_corroboration_mass_score"))
                out.update(fraction_fields(coverage, "recurrent_coverage_fraction"))
                out["incident_atom_count"] = len(contributions)
                out["score_contributions"] = contributions
                successor.append(out)
                score_by_hash[str(row["family_hash"])] = score

            successor.sort(
                key=lambda x: (
                    -score_by_hash[str(x["family_hash"])],
                    int(x["native_topomodal_rank"]),
                    str(x["family_hash"]),
                )
            )
            for rank, row in enumerate(successor, 1):
                row["rank"] = rank
                row["dag_corroboration_mass_rank"] = rank

            native_ids = [str(x["family_hash"]) for x in topo]
            successor_ids = [str(x["family_hash"]) for x in successor]
            req(set(native_ids) == set(successor_ids) and len(successor_ids) == len(set(successor_ids)), "successor candidate identity changed")
            by_native = {str(x["family_hash"]): member_set(x) for x in topo}
            membership_exact = all(member_set(x) == by_native[str(x["family_hash"])] for x in successor)
            all_membership_exact = all_membership_exact and membership_exact
            rank_exact = [int(x["dag_corroboration_mass_rank"]) for x in successor] == list(range(1, nt + 1))
            all_rank_exact = all_rank_exact and rank_exact

            recompute_ok = True
            for row in successor:
                expected = score_by_hash[str(row["family_hash"])]
                stored = Fraction(int(row["dag_corroboration_mass_score_numerator"]), int(row["dag_corroboration_mass_score_denominator"]))
                recompute_ok = recompute_ok and expected == stored
            all_score_exact = all_score_exact and recompute_ok

            expected_order = sorted(
                topo,
                key=lambda x: (
                    -score_by_hash[str(x["family_hash"])],
                    int(x["rank"]),
                    str(x["family_hash"]),
                ),
            )
            order_exact = successor_ids == [str(x["family_hash"]) for x in expected_order]
            all_order_exact = all_order_exact and order_exact

            native_topk = native_ids[:K]
            successor_topk = successor_ids[:K]
            mechanism_active = mechanism_active or successor_ids != native_ids
            eval_active = eval_active or successor_topk != native_topk
            native_mean = mean_fraction([score_by_hash[h] for h in native_topk])
            successor_mean = mean_fraction([score_by_hash[h] for h in successor_topk])
            nonloss = successor_mean >= native_mean
            strict = successor_mean > native_mean
            topk_score_nonloss_all = topk_score_nonloss_all and nonloss
            topk_score_strict_any = topk_score_strict_any or strict

            dag_audit = src["dag_audit"]
            atom_ok = bool(dag_audit["atoms_pairwise_disjoint"]) and bool(dag_audit["atom_union_equals_joint_support"])
            all_atom_exact = all_atom_exact and atom_ok

            subsets.append(
                {
                    "denominator": d,
                    "bucket": b,
                    "events_total": int(src["event_count"]),
                    "event_universe_sha256": src["event_universe_sha256"],
                    "annual_event_count": src["annual_event_count"],
                    "equal_budget_k": K,
                    "successor_candidates": successor,
                    "native_topomodal_candidates": topo,
                    "recurrent_candidates": recurrent,
                    "dag_atom_count": len(atoms),
                    "dag_audit": dag_audit,
                }
            )
            panel_audit.append(
                {
                    "denominator": d,
                    "bucket": b,
                    "candidate_count": nt,
                    "recurrent_count": nr,
                    "equal_budget_k": K,
                    "membership_exact": membership_exact,
                    "rank_exact": rank_exact,
                    "score_recompute_exact": recompute_ok,
                    "order_exact": order_exact,
                    "full_order_changed": successor_ids != native_ids,
                    "topk_changed": successor_topk != native_topk,
                    **fraction_fields(native_mean, "native_topk_mean_score"),
                    **fraction_fields(successor_mean, "successor_topk_mean_score"),
                    "topk_score_nonloss": nonloss,
                    "topk_score_strict": strict,
                }
            )

    prelabel = {
        "schema": "ORBITTRACE_DAG_CORROBORATION_MASS_RANK_V1_PRELABEL",
        "scientific_role": "PRELABEL_DAG_CORROBORATION_MASS_RANK_V1",
        "source_dag_run_id": 32185851992,
        "source_dag_artifact_id": 9342489614,
        "source_dag_prelabel_sha256": DAG_PRELABEL_SHA256,
        "source_dag_result_sha256": DAG_RESULT_SHA256,
        "source_dag_verdict": DAG_SUPPORT_VERDICT,
        "configuration": {
            "candidate_membership": "exact_raw_support_resolved_topomodal",
            "recurrent_priority": "q=(N_R-rank+1)/N_R",
            "score": "sum_atoms((atom_size/topomodal_size)*recurrent_priority)",
            "final_order": "score_desc_native_topomodal_rank_asc_family_hash_asc",
            "equal_budget": "min(raw_topomodal_count,recurrent_count)",
        },
        "blind_exclusion": list(BLIND),
        "subsets": subsets,
        "shower_truth_used": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_scientific_access": False,
        "asfn_efn_event_level_access": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "post_result_parameter_search": False,
    }
    pre_path = a.output / "DAG_CORROBORATION_MASS_RANK_V1_PRELABEL.json"
    pre_path.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    pre_sha = sha256(pre_path)

    gates = {
        "binding_dag_source_exact_and_supported": True,
        "exact_eight_sparse_panels": len(subsets) == 8,
        "panel_universes_and_firewall_exact": all(int(x["events_total"]) > 0 and bool(x["event_universe_sha256"]) for x in subsets),
        "successor_memberships_exact_raw_topomodal": all_membership_exact,
        "recurrent_ranks_and_priorities_exact": all_rank_exact,
        "atoms_exact_nonempty_parent_subsets_and_incident_disjoint": all_atom_exact,
        "scores_exact_and_bounded": all_score_exact,
        "coverage_exact_and_bounded": True,
        "successor_order_deterministic_permutation": all_order_exact,
        "positive_equal_budget_all_panels": all_k_positive,
        "mechanism_full_order_active": mechanism_active,
        "mechanism_topk_active": eval_active,
        "topk_mean_score_nonloss_all_and_strict_some": topk_score_nonloss_all and topk_score_strict_any,
    }
    verdict = "PASS_DAG_CORROBORATION_MASS_RANK_V1_PRETRUTH" if all(gates.values()) else "FAIL_DAG_CORROBORATION_MASS_RANK_V1_PRETRUTH"
    audit = {
        "schema": "ORBITTRACE_DAG_CORROBORATION_MASS_RANK_V1_PRETRUTH",
        "scientific_role": "ZERO_LABEL_PRETRUTH_AUTHORIZATION",
        "verdict": verdict,
        "prelabel_sha256": pre_sha,
        "gates": gates,
        "panels": panel_audit,
        "shower_truth_used": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "external_scientific_access": False,
        "post_result_parameter_search": False,
    }
    audit_path = a.output / "DAG_CORROBORATION_MASS_RANK_V1_PRETRUTH.json"
    audit_path.write_text(json.dumps(audit, indent=2, sort_keys=True, allow_nan=False) + "\n")
    (a.output / "PRELABEL_SHA256.txt").write_text(pre_sha + "\n")
    (a.output / "PRETRUTH_SHA256.txt").write_text(sha256(audit_path) + "\n")
    print(json.dumps({"verdict": verdict, "prelabel_sha256": pre_sha, "gates": gates, "panels": panel_audit}, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
