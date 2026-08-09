#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

EXPECTED_P8_SHA256 = "d3bdcdaf18639e36cc02f5106b3a3c816f5e51eb19543f425717ba1c48a26470"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def replace_once(text: str, before: str, after: str, label: str) -> str:
    count = text.count(before)
    if count != 1:
        raise RuntimeError(f"P9 patch anchor {label} count={count}")
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
SUPPORT_REPL = '''            geometry_retained_seed_mask = np.asarray(pp >= membership_floor, dtype=bool)
            require(geometry_retained_seed_mask.shape == (len(xp),), "P9 invalid geometry-retained seed mask")
            geometry_retained_seed_rows = np.asarray(xp[geometry_retained_seed_mask], dtype=np.float64)
            geometry_retained_seed_probabilities = np.asarray(pp[geometry_retained_seed_mask], dtype=np.float64)
            require(len(geometry_retained_seed_rows) >= 1, "P9 retained-seed geometry became empty")
            require(np.all(geometry_retained_seed_probabilities >= membership_floor), "P9 retained a seed below the P8 membership floor")
            require(len(geometry_retained_seed_rows) >= len(xp) - membership_floor_rank + 1, "P9 retained fewer seeds than the P8 order statistic permits")
            if membership_floor_rank == 1:
                require(len(geometry_retained_seed_rows) == len(xp), "P9 changed rank-one geometry")
            maximal_rows = []
            for seed_row in geometry_retained_seed_rows:
                dominated_by_worse_seed = np.any(
                    np.all(geometry_retained_seed_rows >= seed_row[None, :], axis=1)
                    & np.any(geometry_retained_seed_rows > seed_row[None, :], axis=1)
                )
                if not bool(dominated_by_worse_seed):
                    maximal_rows.append(seed_row)
            joint_seed_support = np.unique(np.asarray(maximal_rows, dtype=np.float64), axis=0)
            require(joint_seed_support.ndim == 2 and joint_seed_support.shape[1] == 2 and len(joint_seed_support) >= 1, "P9 invalid retained-seed joint support frontier")
            joint_seed_support = joint_seed_support[np.lexsort((joint_seed_support[:, 1], joint_seed_support[:, 0]))]
            retained_seed_supported = np.zeros(len(geometry_retained_seed_rows), dtype=bool)
            for support_row in joint_seed_support:
                retained_seed_supported |= np.all(geometry_retained_seed_rows <= support_row[None, :], axis=1)
            require(np.all(retained_seed_supported), "P9 retained held-out seed excluded by retained-seed support frontier")
'''

RECORD_ANCHOR = '''                "joint_seed_support": joint_seed_support.tolist(),
                "joint_seed_support_rule": "componentwise-maximal held-out recurrent-seed [d_obs,d_orb] vectors; candidate must be <= one actual support vector in both coordinates",
                "joint_seed_support_float64_sha256": hashlib.sha256(np.ascontiguousarray(joint_seed_support, dtype="<f8").tobytes()).hexdigest(),
                "positive_scores_float64_sha256": hashlib.sha256(np.ascontiguousarray(pp, dtype="<f8").tobytes()).hexdigest(),
'''
RECORD_REPL = '''                "joint_seed_support": joint_seed_support.tolist(),
                "joint_seed_support_rule": "componentwise-maximal P8-retained held-out recurrent-seed [d_obs,d_orb] vectors; retained iff same-fold seed probability >= P8 membership_floor",
                "joint_seed_support_float64_sha256": hashlib.sha256(np.ascontiguousarray(joint_seed_support, dtype="<f8").tobytes()).hexdigest(),
                "p9_geometry_retained_seed_count": int(len(geometry_retained_seed_rows)),
                "p9_geometry_dropped_seed_count": int(len(xp) - len(geometry_retained_seed_rows)),
                "p9_geometry_retained_seed_probability_float64_sha256": hashlib.sha256(np.ascontiguousarray(geometry_retained_seed_probabilities, dtype="<f8").tobytes()).hexdigest(),
                "p9_geometry_rule": "held-out seed may define joint geometry iff same-fold seed probability >= P8 membership_floor",
                "positive_scores_float64_sha256": hashlib.sha256(np.ascontiguousarray(pp, dtype="<f8").tobytes()).hexdigest(),
'''

PAYLOAD_ANCHOR = '''        "p8_order_statistic_tuning": False,
        "no_known_shower_truth_used": True,
'''
PAYLOAD_REPL = '''        "p8_order_statistic_tuning": False,
        "p9_retained_seed_geometry": "P5 joint support recomputed only from held-out recurrent seeds whose same-fold probability >= P8 membership_floor",
        "p9_geometry_tuning": False,
        "no_known_shower_truth_used": True,
'''

MEMBERSHIP_NAMES = (
    ('"p8_membership_pretruth.sha256"', '"p9_membership_pretruth.sha256"'),
    ('"p8_expanded_families.json.gz"', '"p9_expanded_families.json.gz"'),
    ('"p8_decisions_pretruth.sha256"', '"p9_decisions_pretruth.sha256"'),
    ('"p8_decisions_pretruth.json.gz"', '"p9_decisions_pretruth.json.gz"'),
)

GATE_ANCHOR = '''        "p8_no_p7_unreliable_direction_can_propose": all(
            bool(reliability[f"{p['family_id']}|{p['source_year']}|{p['target_year']}"]["reliable"])
            for ps in proposals_by_event.values() for p in ps
        ),
        "expansion_nonvacuous": len(assignments) > 0,
'''
GATE_REPL = '''        "p8_no_p7_unreliable_direction_can_propose": all(
            bool(reliability[f"{p['family_id']}|{p['source_year']}|{p['target_year']}"]["reliable"])
            for ps in proposals_by_event.values() for p in ps
        ),
        "p9_geometry_uses_only_p8_retained_seeds": all(
            int(r["p9_geometry_retained_seed_count"]) >= int(r["seed_count"]) - int(r["membership_floor_rank"]) + 1
            and int(r["p9_geometry_retained_seed_count"]) <= int(r["seed_count"])
            for r in reliability.values()
        ),
        "p9_rank_one_geometry_unchanged": all(
            int(r["membership_floor_rank"]) != 1 or int(r["p9_geometry_retained_seed_count"]) == int(r["seed_count"])
            for r in reliability.values()
        ),
        "p9_retained_seed_frontier_nonempty": all(len(r.get("joint_seed_support", [])) >= 1 for r in reliability.values()),
        "p9_every_surviving_proposal_supported_by_retained_seed_frontier": all(
            any(
                float(p["d_obs"]) <= float(s[0]) and float(p["d_orb"]) <= float(s[1])
                for s in reliability[f"{p['family_id']}|{p['source_year']}|{p['target_year']}"]["joint_seed_support"]
            )
            for ps in proposals_by_event.values() for p in ps
        ),
        "p9_no_p8_unreliable_direction_can_propose": all(
            bool(reliability[f"{p['family_id']}|{p['source_year']}|{p['target_year']}"]["reliable"])
            for ps in proposals_by_event.values() for p in ps
        ),
        "p9_geometry_change_nonvacuous": sum(int(r["p9_geometry_dropped_seed_count"]) for r in reliability.values()) > 0,
        "expansion_nonvacuous": len(assignments) > 0,
'''

VERDICT_ANCHOR = '''    verdict = (
        "PASS_FINITE_SAMPLE_10PCT_ORDER_STAT_MEMBERSHIP_P8_DEVELOPMENT"
        if all(gates.values())
        else "FAIL_FINITE_SAMPLE_10PCT_ORDER_STAT_MEMBERSHIP_P8_NO_GO"
    )
'''
VERDICT_REPL = '''    verdict = (
        "PASS_RETAINED_SEED_GEOMETRY_MEMBERSHIP_P9_DEVELOPMENT"
        if all(gates.values())
        else "FAIL_RETAINED_SEED_GEOMETRY_MEMBERSHIP_P9_NO_GO"
    )
'''

CLASS_ANCHOR = '''        "classification": "P6 same-model cross-fit membership plus full finite-sample order-statistic candidate floor spending only the inherited P3 0.10 scale; immutable promoted-v8 cores and rank",
'''
CLASS_REPL = '''        "classification": "P8 finite-sample scalar floor with P5 joint geometry recomputed from exactly the P8-retained held-out recurrent seeds; immutable promoted-v8 cores and rank",
'''

CONFIG_ANCHOR = '''            "p8_parameter_search": False,
        },
'''
CONFIG_REPL = '''            "p8_parameter_search": False,
            "p9_retained_seed_geometry": "joint support uses exactly held-out recurrent seeds with same-fold probability >= P8 membership_floor",
            "p9_new_numeric_threshold": None,
            "p9_geometry_tuning": False,
            "p9_parameter_search": False,
        },
'''

METHOD_KEY_ANCHOR = '''        "p8": {k: v for k, v in p2_full.items() if k != "per_label"},
'''
METHOD_KEY_REPL = '''        "p9": {k: v for k, v in p2_full.items() if k != "per_label"},
'''
LARGE_KEY_ANCHOR = '''        "p8_large_shower": p2_large,
'''
LARGE_KEY_REPL = '''        "p9_large_shower": p2_large,
'''

DIAG_ANCHOR = '''            "p8_membership_floor_strictly_above_seed_floor_directions": sum(float(r["membership_floor"]) > float(r["seed_floor"]) for r in reliability.values()),
'''
DIAG_REPL = '''            "p8_membership_floor_strictly_above_seed_floor_directions": sum(float(r["membership_floor"]) > float(r["seed_floor"]) for r in reliability.values()),
            "p9_geometry_retained_seeds_total": sum(int(r["p9_geometry_retained_seed_count"]) for r in reliability.values()),
            "p9_geometry_dropped_seeds_total": sum(int(r["p9_geometry_dropped_seed_count"]) for r in reliability.values()),
            "p9_geometry_changed_directions": sum(int(r["p9_geometry_dropped_seed_count"]) > 0 for r in reliability.values()),
            "p9_retained_joint_support_vectors_total": sum(len(r.get("joint_seed_support", [])) for r in reliability.values()),
'''

JSON_ANCHOR = '''    (args.output / "finite_sample_10pct_order_stat_membership_p8_development.json").write_text(json.dumps(result, indent=2) + "\\n")
'''
JSON_REPL = '''    (args.output / "retained_seed_geometry_membership_p9_development.json").write_text(json.dumps(result, indent=2) + "\\n")
'''
MD_ANCHOR = '''    (args.output / "FINITE_SAMPLE_10PCT_ORDER_STAT_MEMBERSHIP_P8_DEVELOPMENT.md").write_text(
'''
MD_REPL = '''    (args.output / "RETAINED_SEED_GEOMETRY_MEMBERSHIP_P9_DEVELOPMENT.md").write_text(
'''
TITLE_ANCHOR = '''        "# OrbitTrace P8 full finite-sample 10% order-statistic membership development\\n\\n"
'''
TITLE_REPL = '''        "# OrbitTrace P9 retained-seed joint-geometry membership development\\n\\n"
'''
SUMMARY_ANCHOR = '''f"- v8 -> P8 macro F1: **{baseline_full['macro_f1']:.6f} -> {p2_full['macro_f1']:.6f}**\\n"'''
SUMMARY_REPL = '''f"- v8 -> P9 macro F1: **{baseline_full['macro_f1']:.6f} -> {p2_full['macro_f1']:.6f}**\\n"'''
QUALIFIED_ANCHOR = '''f"- v8 -> P8 qualified: **{baseline_full['qualified_matches']} -> {p2_full['qualified_matches']}**\\n"'''
QUALIFIED_REPL = '''f"- v8 -> P9 qualified: **{baseline_full['qualified_matches']} -> {p2_full['qualified_matches']}**\\n"'''
RECOVERY_ANCHOR = '''f"- v8 -> P8 recovery@100: **{baseline_full['recovered_at_100']} -> {p2_full['recovered_at_100']}**\\n"'''
RECOVERY_REPL = '''f"- v8 -> P9 recovery@100: **{baseline_full['recovered_at_100']} -> {p2_full['recovered_at_100']}**\\n"'''
PRECISION_ANCHOR = '''f"- v8 -> P8 top100 precision: **{baseline_full['top100_dominant_precision']:.6f} -> {p2_full['top100_dominant_precision']:.6f}**\\n"'''
PRECISION_REPL = '''f"- v8 -> P9 top100 precision: **{baseline_full['top100_dominant_precision']:.6f} -> {p2_full['top100_dominant_precision']:.6f}**\\n"'''
PRINT_ANCHOR = '''    print((args.output / "FINITE_SAMPLE_10PCT_ORDER_STAT_MEMBERSHIP_P8_DEVELOPMENT.md").read_text(), flush=True)
'''
PRINT_REPL = '''    print((args.output / "RETAINED_SEED_GEOMETRY_MEMBERSHIP_P9_DEVELOPMENT.md").read_text(), flush=True)
'''


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply_p9_patch.py EXACT_P8 OUTPUT")
    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    raw = source.read_bytes()
    actual = digest(raw)
    if actual != EXPECTED_P8_SHA256:
        raise RuntimeError(f"exact P8 source SHA changed: {actual}")
    text = raw.decode("utf-8")
    for before, after, label in (
        (SUPPORT_ANCHOR, SUPPORT_REPL, "retained-seed joint geometry"),
        (RECORD_ANCHOR, RECORD_REPL, "P9 reliability geometry record"),
        (PAYLOAD_ANCHOR, PAYLOAD_REPL, "P9 crossfit declaration"),
        (GATE_ANCHOR, GATE_REPL, "P9 integrity gates"),
        (VERDICT_ANCHOR, VERDICT_REPL, "P9 verdict"),
        (CLASS_ANCHOR, CLASS_REPL, "P9 classification"),
        (CONFIG_ANCHOR, CONFIG_REPL, "P9 configuration"),
        (METHOD_KEY_ANCHOR, METHOD_KEY_REPL, "P9 result method key"),
        (LARGE_KEY_ANCHOR, LARGE_KEY_REPL, "P9 large-shower key"),
        (DIAG_ANCHOR, DIAG_REPL, "P9 diagnostics"),
        (JSON_ANCHOR, JSON_REPL, "P9 JSON filename"),
        (MD_ANCHOR, MD_REPL, "P9 markdown filename"),
        (TITLE_ANCHOR, TITLE_REPL, "P9 title"),
        (SUMMARY_ANCHOR, SUMMARY_REPL, "P9 summary label"),
        (QUALIFIED_ANCHOR, QUALIFIED_REPL, "P9 qualified summary label"),
        (RECOVERY_ANCHOR, RECOVERY_REPL, "P9 recovery summary label"),
        (PRECISION_ANCHOR, PRECISION_REPL, "P9 precision summary label"),
        (PRINT_ANCHOR, PRINT_REPL, "P9 print filename"),
    ):
        text = replace_once(text, before, after, label)
    for before, after in MEMBERSHIP_NAMES:
        text = replace_once(text, before, after, f"membership output rename {before}")
    if "OrbitTrace-April" in text or "target_coordinate" in text:
        raise RuntimeError("forbidden target-specific token introduced")
    output.write_text(text, encoding="utf-8")
    print(f"P9_INPUT_P8_SHA256={EXPECTED_P8_SHA256}")
    print(f"P9_OUTPUT_SHA256={digest(text.encode('utf-8'))}")
    print("P9_PATCH_SCOPE=exact P8 with joint geometry recomputed only from P8-retained held-out seeds; no new threshold/search; P4 envelope and all other science unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
