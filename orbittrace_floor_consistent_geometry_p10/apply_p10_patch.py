#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

EXPECTED_P9_SHA256 = "58330c61cf4039f07e80a9746d00eb7281b4e28e674a131d6333e6378695ae31"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def replace_once(text: str, before: str, after: str, label: str) -> str:
    count = text.count(before)
    if count != 1:
        raise RuntimeError(f"P10 patch anchor {label} count={count}")
    return text.replace(before, after, 1)


SUPPORT_ANCHOR = '''            maximal_rows = []
            for seed_row in np.asarray(xp, dtype=np.float64):
                dominated_by_worse_seed = np.any(
                    np.all(xp >= seed_row[None, :], axis=1)
                    & np.any(xp > seed_row[None, :], axis=1)
                )
                if not bool(dominated_by_worse_seed):
                    maximal_rows.append(seed_row)
            joint_seed_support = np.unique(np.asarray(maximal_rows, dtype=np.float64), axis=0)
            require(joint_seed_support.ndim == 2 and joint_seed_support.shape[1] == 2 and len(joint_seed_support) >= 1, "P5 invalid joint seed-support frontier")
            joint_seed_support = joint_seed_support[np.lexsort((joint_seed_support[:, 1], joint_seed_support[:, 0]))]
            seed_supported = np.zeros(len(xp), dtype=bool)
            for support_row in joint_seed_support:
                seed_supported |= np.all(xp <= support_row[None, :], axis=1)
            require(np.all(seed_supported), "P5 held-out recurrent seed excluded by joint support frontier")
'''
SUPPORT_REPL = '''            inherited_maximal_rows = []
            for seed_row in np.asarray(xp, dtype=np.float64):
                inherited_dominated = np.any(
                    np.all(xp >= seed_row[None, :], axis=1)
                    & np.any(xp > seed_row[None, :], axis=1)
                )
                if not bool(inherited_dominated):
                    inherited_maximal_rows.append(seed_row)
            inherited_joint_seed_support = np.unique(np.asarray(inherited_maximal_rows, dtype=np.float64), axis=0)
            require(inherited_joint_seed_support.ndim == 2 and inherited_joint_seed_support.shape[1] == 2 and len(inherited_joint_seed_support) >= 1, "P10 invalid inherited P5 support frontier")
            inherited_joint_seed_support = inherited_joint_seed_support[np.lexsort((inherited_joint_seed_support[:, 1], inherited_joint_seed_support[:, 0]))]

            geometry_retained_seed_mask = np.asarray(pp >= membership_floor, dtype=bool)
            require(geometry_retained_seed_mask.shape == (len(xp),), "P10 invalid geometry-retained seed mask")
            geometry_retained_seed_rows = np.asarray(xp[geometry_retained_seed_mask], dtype=np.float64)
            geometry_retained_seed_probabilities = np.asarray(pp[geometry_retained_seed_mask], dtype=np.float64)
            require(len(geometry_retained_seed_rows) >= 1, "P10 retained-seed geometry became empty")
            require(np.all(geometry_retained_seed_probabilities >= membership_floor), "P10 retained a seed below the exact P8 membership floor")
            require(len(geometry_retained_seed_rows) >= len(xp) - membership_floor_rank + 1, "P10 retained fewer seeds than the P8 order statistic permits")
            if membership_floor_rank == 1:
                require(len(geometry_retained_seed_rows) == len(xp), "P10 changed rank-one seed set")

            maximal_rows = []
            for seed_row in geometry_retained_seed_rows:
                dominated_by_worse_seed = np.any(
                    np.all(geometry_retained_seed_rows >= seed_row[None, :], axis=1)
                    & np.any(geometry_retained_seed_rows > seed_row[None, :], axis=1)
                )
                if not bool(dominated_by_worse_seed):
                    maximal_rows.append(seed_row)
            joint_seed_support = np.unique(np.asarray(maximal_rows, dtype=np.float64), axis=0)
            require(joint_seed_support.ndim == 2 and joint_seed_support.shape[1] == 2 and len(joint_seed_support) >= 1, "P10 invalid floor-consistent retained-seed support frontier")
            joint_seed_support = joint_seed_support[np.lexsort((joint_seed_support[:, 1], joint_seed_support[:, 0]))]
            retained_seed_supported = np.zeros(len(geometry_retained_seed_rows), dtype=bool)
            for support_row in joint_seed_support:
                retained_seed_supported |= np.all(geometry_retained_seed_rows <= support_row[None, :], axis=1)
            require(np.all(retained_seed_supported), "P10 retained held-out seed excluded by retained-seed support frontier")
            if membership_floor_rank == 1:
                require(np.array_equal(joint_seed_support, inherited_joint_seed_support), "P10 rank-one joint geometry changed from inherited P5 frontier")
'''

RECORD_ANCHOR = '''                "joint_seed_support": joint_seed_support.tolist(),
                "joint_seed_support_rule": "componentwise-maximal held-out recurrent-seed [d_obs,d_orb] vectors; candidate must be <= one actual support vector in both coordinates",
                "joint_seed_support_float64_sha256": hashlib.sha256(np.ascontiguousarray(joint_seed_support, dtype="<f8").tobytes()).hexdigest(),
                "positive_scores_float64_sha256": hashlib.sha256(np.ascontiguousarray(pp, dtype="<f8").tobytes()).hexdigest(),
'''
RECORD_REPL = '''                "joint_seed_support": joint_seed_support.tolist(),
                "joint_seed_support_rule": "componentwise-maximal held-out recurrent-seed [d_obs,d_orb] vectors retained only when same-fold seed probability >= exact P8 membership_floor",
                "joint_seed_support_float64_sha256": hashlib.sha256(np.ascontiguousarray(joint_seed_support, dtype="<f8").tobytes()).hexdigest(),
                "p10_inherited_joint_seed_support_float64_sha256": hashlib.sha256(np.ascontiguousarray(inherited_joint_seed_support, dtype="<f8").tobytes()).hexdigest(),
                "p10_inherited_joint_seed_support_count": int(len(inherited_joint_seed_support)),
                "p10_geometry_retained_seed_count": int(len(geometry_retained_seed_rows)),
                "p10_geometry_dropped_seed_count": int(len(xp) - len(geometry_retained_seed_rows)),
                "p10_geometry_retained_seed_probability_float64_sha256": hashlib.sha256(np.ascontiguousarray(geometry_retained_seed_probabilities, dtype="<f8").tobytes()).hexdigest(),
                "p10_geometry_rule": "held-out seed may define P5 joint geometry iff same-fold seed probability >= exact P8 membership_floor; P4 coordinate envelope unchanged",
                "p10_rank_one_frontier_exactly_inherited": bool(membership_floor_rank != 1 or np.array_equal(joint_seed_support, inherited_joint_seed_support)),
                "positive_scores_float64_sha256": hashlib.sha256(np.ascontiguousarray(pp, dtype="<f8").tobytes()).hexdigest(),
'''

PAYLOAD_ANCHOR = '''        "p8_order_statistic_tuning": False,
        "no_known_shower_truth_used": True,
'''
PAYLOAD_REPL = '''        "p8_order_statistic_tuning": False,
        "p10_floor_consistent_retained_seed_geometry": "P5 joint support recomputed only from held-out recurrent seeds whose same-fold probability >= exact P8 membership_floor",
        "p10_geometry_tuning": False,
        "no_known_shower_truth_used": True,
'''

MEMBERSHIP_NAMES = (
    ('"p9_membership_pretruth.sha256"', '"p10_membership_pretruth.sha256"'),
    ('"p9_expanded_families.json.gz"', '"p10_expanded_families.json.gz"'),
    ('"p9_decisions_pretruth.sha256"', '"p10_decisions_pretruth.sha256"'),
    ('"p9_decisions_pretruth.json.gz"', '"p10_decisions_pretruth.json.gz"'),
)

GATE_ANCHOR = '''        "p9_only_bidirectionally_reliable_families_can_propose": all(
            bool(reliability[f"{p['family_id']}|{p['source_year']}|{p['target_year']}"]["reliable"])
            and bool(reliability[f"{p['family_id']}|{p['target_year']}|{p['source_year']}"]["reliable"])
            and bool(p.get("p9_bidirectional_reliability", False))
            for ps in proposals_by_event.values() for p in ps
        ),
        "expansion_nonvacuous": len(assignments) > 0,
'''
GATE_REPL = '''        "p9_only_bidirectionally_reliable_families_can_propose": all(
            bool(reliability[f"{p['family_id']}|{p['source_year']}|{p['target_year']}"]["reliable"])
            and bool(reliability[f"{p['family_id']}|{p['target_year']}|{p['source_year']}"]["reliable"])
            and bool(p.get("p9_bidirectional_reliability", False))
            for ps in proposals_by_event.values() for p in ps
        ),
        "p10_geometry_uses_only_floor_retained_seeds": all(
            int(r["p10_geometry_retained_seed_count"]) >= int(r["seed_count"]) - int(r["membership_floor_rank"]) + 1
            and int(r["p10_geometry_retained_seed_count"]) <= int(r["seed_count"])
            for r in reliability.values()
        ),
        "p10_rank_one_seed_sets_and_frontiers_exactly_inherited": all(
            int(r["membership_floor_rank"]) != 1 or (
                int(r["p10_geometry_retained_seed_count"]) == int(r["seed_count"])
                and bool(r["p10_rank_one_frontier_exactly_inherited"])
                and str(r["joint_seed_support_float64_sha256"]) == str(r["p10_inherited_joint_seed_support_float64_sha256"])
            )
            for r in reliability.values()
        ),
        "p10_retained_seed_frontier_nonempty": all(len(r.get("joint_seed_support", [])) >= 1 for r in reliability.values()),
        "p10_every_surviving_proposal_supported_by_floor_retained_frontier": all(
            any(
                float(p["d_obs"]) <= float(s[0]) and float(p["d_orb"]) <= float(s[1])
                for s in reliability[f"{p['family_id']}|{p['source_year']}|{p['target_year']}"]["joint_seed_support"]
            )
            for ps in proposals_by_event.values() for p in ps
        ),
        "p10_no_non_bidirectionally_reliable_family_can_propose": all(
            bool(reliability[f"{p['family_id']}|{p['source_year']}|{p['target_year']}"]["reliable"])
            and bool(reliability[f"{p['family_id']}|{p['target_year']}|{p['source_year']}"]["reliable"])
            for ps in proposals_by_event.values() for p in ps
        ),
        "p10_geometry_change_nonvacuous": sum(int(r["p10_geometry_dropped_seed_count"]) for r in reliability.values()) > 0,
        "p10_exactly_50_reliable_rank_gt1_directions_changed_geometry": sum(
            bool(r["reliable"]) and int(r["membership_floor_rank"]) > 1 and int(r["p10_geometry_dropped_seed_count"]) > 0
            for r in reliability.values()
        ) == 50,
        "expansion_nonvacuous": len(assignments) > 0,
'''

VERDICT_ANCHOR = '''    verdict = (
        "PASS_BIDIRECTIONAL_RELIABILITY_MEMBERSHIP_P9_DEVELOPMENT"
        if all(gates.values())
        else "FAIL_BIDIRECTIONAL_RELIABILITY_MEMBERSHIP_P9_NO_GO"
    )
'''
VERDICT_REPL = '''    verdict = (
        "PASS_FLOOR_CONSISTENT_GEOMETRY_MEMBERSHIP_P10_DEVELOPMENT"
        if all(gates.values())
        else "FAIL_FLOOR_CONSISTENT_GEOMETRY_MEMBERSHIP_P10_NO_GO"
    )
'''

CLASS_ANCHOR = '''        "classification": "Exact P8 membership with nonseed halo growth allowed only for recurrent families whose two reciprocal cross-year directions both satisfy the inherited P3 reliability boolean; immutable promoted-v8 cores and rank",
'''
CLASS_REPL = '''        "classification": "Exact P9 bidirectional-reliability membership with P5 joint geometry recomputed from exactly the held-out recurrent seeds retained by the exact P8 membership floor; immutable promoted-v8 cores and rank",
'''

CONFIG_ANCHOR = '''            "p9_bidirectional_reliability_rule": "both reciprocal P3 direction reliability booleans must be true before either direction may add nonseed members",
            "p9_new_numeric_thresholds": False,
            "p9_parameter_search": False,
'''
CONFIG_REPL = '''            "p9_bidirectional_reliability_rule": "both reciprocal P3 direction reliability booleans must be true before either direction may add nonseed members",
            "p9_new_numeric_thresholds": False,
            "p9_parameter_search": False,
            "p10_floor_consistent_geometry": "P5 joint support uses exactly held-out recurrent seeds with same-fold probability >= exact P8 membership_floor; P4 envelope remains full-seed",
            "p10_new_numeric_thresholds": False,
            "p10_geometry_tuning": False,
            "p10_parameter_search": False,
'''

METHOD_KEY_ANCHOR = '''        "p9": {k: v for k, v in p2_full.items() if k != "per_label"},
'''
METHOD_KEY_REPL = '''        "p10": {k: v for k, v in p2_full.items() if k != "per_label"},
'''
LARGE_KEY_ANCHOR = '''        "p9_large_shower": p2_large,
'''
LARGE_KEY_REPL = '''        "p10_large_shower": p2_large,
'''

DIAG_ANCHOR = '''            "p9_proposals_from_non_bidirectionally_reliable_families": sum(
                not (
                    bool(reliability[f"{p['family_id']}|{p['source_year']}|{p['target_year']}"]["reliable"])
                    and bool(reliability[f"{p['family_id']}|{p['target_year']}|{p['source_year']}"]["reliable"])
                )
                for ps in proposals_by_event.values() for p in ps
            ),
'''
DIAG_REPL = '''            "p9_proposals_from_non_bidirectionally_reliable_families": sum(
                not (
                    bool(reliability[f"{p['family_id']}|{p['source_year']}|{p['target_year']}"]["reliable"])
                    and bool(reliability[f"{p['family_id']}|{p['target_year']}|{p['source_year']}"]["reliable"])
                )
                for ps in proposals_by_event.values() for p in ps
            ),
            "p10_geometry_retained_seeds_total": sum(int(r["p10_geometry_retained_seed_count"]) for r in reliability.values()),
            "p10_geometry_dropped_seeds_total": sum(int(r["p10_geometry_dropped_seed_count"]) for r in reliability.values()),
            "p10_geometry_changed_directions": sum(int(r["p10_geometry_dropped_seed_count"]) > 0 for r in reliability.values()),
            "p10_geometry_changed_reliable_rank_gt1_directions": sum(
                bool(r["reliable"]) and int(r["membership_floor_rank"]) > 1 and int(r["p10_geometry_dropped_seed_count"]) > 0
                for r in reliability.values()
            ),
            "p10_retained_joint_support_vectors_total": sum(len(r.get("joint_seed_support", [])) for r in reliability.values()),
            "p10_inherited_joint_support_vectors_total": sum(int(r["p10_inherited_joint_seed_support_count"]) for r in reliability.values()),
'''

JSON_ANCHOR = '''    (args.output / "bidirectional_reliability_membership_p9_development.json").write_text(json.dumps(result, indent=2) + "\\n")
'''
JSON_REPL = '''    (args.output / "floor_consistent_geometry_membership_p10_development.json").write_text(json.dumps(result, indent=2) + "\\n")
'''
MD_ANCHOR = '''    (args.output / "BIDIRECTIONAL_RELIABILITY_MEMBERSHIP_P9_DEVELOPMENT.md").write_text(
'''
MD_REPL = '''    (args.output / "FLOOR_CONSISTENT_GEOMETRY_MEMBERSHIP_P10_DEVELOPMENT.md").write_text(
'''
TITLE_ANCHOR = '''        "# OrbitTrace P9 bidirectional recurrent-reliability membership development\\n\\n"
'''
TITLE_REPL = '''        "# OrbitTrace P10 floor-consistent retained-seed joint-geometry membership development\\n\\n"
'''
SUMMARY_ANCHOR = '''f"- v8 -> P9 macro F1: **{baseline_full['macro_f1']:.6f} -> {p2_full['macro_f1']:.6f}**\\n"'''
SUMMARY_REPL = '''f"- v8 -> P10 macro F1: **{baseline_full['macro_f1']:.6f} -> {p2_full['macro_f1']:.6f}**\\n"'''
QUALIFIED_ANCHOR = '''f"- v8 -> P9 qualified: **{baseline_full['qualified_matches']} -> {p2_full['qualified_matches']}**\\n"'''
QUALIFIED_REPL = '''f"- v8 -> P10 qualified: **{baseline_full['qualified_matches']} -> {p2_full['qualified_matches']}**\\n"'''
RECOVERY_ANCHOR = '''f"- v8 -> P9 recovery@100: **{baseline_full['recovered_at_100']} -> {p2_full['recovered_at_100']}**\\n"'''
RECOVERY_REPL = '''f"- v8 -> P10 recovery@100: **{baseline_full['recovered_at_100']} -> {p2_full['recovered_at_100']}**\\n"'''
PRECISION_ANCHOR = '''f"- v8 -> P9 top100 precision: **{baseline_full['top100_dominant_precision']:.6f} -> {p2_full['top100_dominant_precision']:.6f}**\\n"'''
PRECISION_REPL = '''f"- v8 -> P10 top100 precision: **{baseline_full['top100_dominant_precision']:.6f} -> {p2_full['top100_dominant_precision']:.6f}**\\n"'''
PRINT_ANCHOR = '''    print((args.output / "BIDIRECTIONAL_RELIABILITY_MEMBERSHIP_P9_DEVELOPMENT.md").read_text(), flush=True)
'''
PRINT_REPL = '''    print((args.output / "FLOOR_CONSISTENT_GEOMETRY_MEMBERSHIP_P10_DEVELOPMENT.md").read_text(), flush=True)
'''


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply_p10_patch.py EXACT_P9 OUTPUT")
    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    raw = source.read_bytes()
    actual = digest(raw)
    if actual != EXPECTED_P9_SHA256:
        raise RuntimeError(f"exact P9 source SHA changed: {actual}")
    text = raw.decode("utf-8")
    for before, after, label in (
        (SUPPORT_ANCHOR, SUPPORT_REPL, "floor-consistent retained-seed joint geometry"),
        (RECORD_ANCHOR, RECORD_REPL, "P10 reliability geometry record"),
        (PAYLOAD_ANCHOR, PAYLOAD_REPL, "P10 crossfit declaration"),
        (GATE_ANCHOR, GATE_REPL, "P10 integrity gates"),
        (VERDICT_ANCHOR, VERDICT_REPL, "P10 verdict"),
        (CLASS_ANCHOR, CLASS_REPL, "P10 classification"),
        (CONFIG_ANCHOR, CONFIG_REPL, "P10 configuration"),
        (METHOD_KEY_ANCHOR, METHOD_KEY_REPL, "P10 result method key"),
        (LARGE_KEY_ANCHOR, LARGE_KEY_REPL, "P10 large-shower key"),
        (DIAG_ANCHOR, DIAG_REPL, "P10 diagnostics"),
        (JSON_ANCHOR, JSON_REPL, "P10 JSON filename"),
        (MD_ANCHOR, MD_REPL, "P10 markdown filename"),
        (TITLE_ANCHOR, TITLE_REPL, "P10 title"),
        (SUMMARY_ANCHOR, SUMMARY_REPL, "P10 summary label"),
        (QUALIFIED_ANCHOR, QUALIFIED_REPL, "P10 qualified summary label"),
        (RECOVERY_ANCHOR, RECOVERY_REPL, "P10 recovery summary label"),
        (PRECISION_ANCHOR, PRECISION_REPL, "P10 precision summary label"),
        (PRINT_ANCHOR, PRINT_REPL, "P10 print filename"),
    ):
        text = replace_once(text, before, after, label)
    for before, after in MEMBERSHIP_NAMES:
        text = replace_once(text, before, after, f"membership output rename {before}")
    if "OrbitTrace-April" in text or "target_coordinate" in text:
        raise RuntimeError("forbidden target-specific token introduced")
    output.write_text(text, encoding="utf-8")
    print(f"P10_INPUT_P9_SHA256={EXPECTED_P9_SHA256}")
    print(f"P10_OUTPUT_SHA256={digest(text.encode('utf-8'))}")
    print("P10_PATCH_SCOPE=exact P9 plus P5 joint geometry rebuilt only from held-out seeds meeting exact P8 membership floor; P4 envelope/bidirectional reliability/thresholds/rank unchanged; no parameter search")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
