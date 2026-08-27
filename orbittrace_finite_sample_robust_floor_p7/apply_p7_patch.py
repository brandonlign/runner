#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

EXPECTED_P6_SHA256 = "d32648136b58e2f777912d6403d9de3cbd091a8c23e16aedcda0b146f09f38c2"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def replace_once(text: str, before: str, after: str, label: str) -> str:
    count = text.count(before)
    if count != 1:
        raise RuntimeError(f"P7 patch anchor {label} count={count}")
    return text.replace(before, after, 1)


CONST_ANCHOR = '''P3_SEED_FLOOR_MIN = 0.5
'''
CONST_REPL = '''P3_SEED_FLOOR_MIN = 0.5
P7_ROBUST_FLOOR_MIN_SEEDS = 19
'''

FLOOR_ANCHOR = '''            seed_floor = float(np.min(pp))
            negative_tail = float(np.mean(pn >= seed_floor))
            feature_ceiling = np.max(xp, axis=0).astype(np.float64, copy=False)
'''
FLOOR_REPL = '''            seed_floor = float(np.min(pp))
            negative_tail = float(np.mean(pn >= seed_floor))
            sorted_seed_probabilities = np.sort(np.asarray(pp, dtype=np.float64))
            require(len(sorted_seed_probabilities) == len(xp) and len(sorted_seed_probabilities) >= 4, "P7 invalid held-out seed score vector")
            membership_floor_rank = 2 if len(sorted_seed_probabilities) >= P7_ROBUST_FLOOR_MIN_SEEDS else 1
            membership_floor = float(sorted_seed_probabilities[membership_floor_rank - 1])
            require(membership_floor >= seed_floor, "P7 robust membership floor below inherited minimum seed floor")
            feature_ceiling = np.max(xp, axis=0).astype(np.float64, copy=False)
'''

RECORD_ANCHOR = '''                "seed_floor": seed_floor,
                "negative_tail": negative_tail,
                "feature_ceiling": feature_ceiling.tolist(),
'''
RECORD_REPL = '''                "seed_floor": seed_floor,
                "negative_tail": negative_tail,
                "membership_floor": membership_floor,
                "membership_floor_rank": membership_floor_rank,
                "membership_floor_min_seeds": P7_ROBUST_FLOOR_MIN_SEEDS,
                "membership_floor_rule": "second-smallest held-out recurrent-seed probability iff seed_count >= 19; otherwise inherited minimum seed probability",
                "feature_ceiling": feature_ceiling.tolist(),
'''

PAYLOAD_ANCHOR = '''        "p6_probability_scale_tuning": False,
        "no_known_shower_truth_used": True,
'''
PAYLOAD_REPL = '''        "p6_probability_scale_tuning": False,
        "p7_membership_floor": "second-smallest held-out recurrent-seed probability iff seed_count >= 19; otherwise inherited minimum seed probability",
        "p7_robust_floor_min_seeds": P7_ROBUST_FLOOR_MIN_SEEDS,
        "p7_order_statistic_tuning": False,
        "no_known_shower_truth_used": True,
'''

SCORING_ANCHOR = '''        seed_floor_allowed = probabilities >= float(gate["seed_floor"])
        feature_ceiling = np.asarray(gate["feature_ceiling"], dtype=np.float64)
'''
SCORING_REPL = '''        seed_floor_allowed = probabilities >= float(gate["seed_floor"])
        membership_floor_allowed = probabilities >= float(gate["membership_floor"])
        feature_ceiling = np.asarray(gate["feature_ceiling"], dtype=np.float64)
'''

ALLOWED_ANCHOR = '''        allowed = seed_floor_allowed & jointly_supported
        odds = probabilities / (1.0 - probabilities)
'''
ALLOWED_REPL = '''        allowed = membership_floor_allowed & jointly_supported
        odds = probabilities / (1.0 - probabilities)
'''

PROPOSAL_ANCHOR = '''                "seed_floor": float(gate["seed_floor"]),
                "scoring_fold": scoring_fold,
                "d_obs": float(feature_row[0]),
'''
PROPOSAL_REPL = '''                "seed_floor": float(gate["seed_floor"]),
                "membership_floor": float(gate["membership_floor"]),
                "membership_floor_rank": int(gate["membership_floor_rank"]),
                "scoring_fold": scoring_fold,
                "d_obs": float(feature_row[0]),
'''

MEMBERSHIP_NAMES = (
    ('"p6_membership_pretruth.sha256"', '"p7_membership_pretruth.sha256"'),
    ('"p6_expanded_families.json.gz"', '"p7_expanded_families.json.gz"'),
    ('"p6_decisions_pretruth.sha256"', '"p7_decisions_pretruth.sha256"'),
    ('"p6_decisions_pretruth.json.gz"', '"p7_decisions_pretruth.json.gz"'),
)

GATE_ANCHOR = '''        "p6_final_all_family_model_not_used_for_proposal_scoring": all("scoring_fold" in p for ps in proposals_by_event.values() for p in ps),
        "expansion_nonvacuous": len(assignments) > 0,
'''
GATE_REPL = '''        "p6_final_all_family_model_not_used_for_proposal_scoring": all("scoring_fold" in p for ps in proposals_by_event.values() for p in ps),
        "p7_exact_robust_floor_min_seeds": P7_ROBUST_FLOOR_MIN_SEEDS == 19,
        "p7_sparse_directions_keep_inherited_minimum_floor": all(
            int(r["seed_count"]) >= P7_ROBUST_FLOOR_MIN_SEEDS or (
                int(r["membership_floor_rank"]) == 1 and float(r["membership_floor"]) == float(r["seed_floor"])
            )
            for r in reliability.values()
        ),
        "p7_supported_directions_use_second_order_statistic": all(
            int(r["seed_count"]) < P7_ROBUST_FLOOR_MIN_SEEDS or (
                int(r["membership_floor_rank"]) == 2 and float(r["membership_floor"]) >= float(r["seed_floor"])
            )
            for r in reliability.values()
        ),
        "p7_every_surviving_proposal_meets_membership_floor": all(
            float(p["probability"]) >= float(p["membership_floor"])
            for ps in proposals_by_event.values() for p in ps
        ),
        "p7_no_p6_unreliable_direction_can_propose": all(
            bool(reliability[f"{p['family_id']}|{p['source_year']}|{p['target_year']}"]["reliable"])
            for ps in proposals_by_event.values() for p in ps
        ),
        "expansion_nonvacuous": len(assignments) > 0,
'''

VERDICT_ANCHOR = '''    verdict = (
        "PASS_SAME_MODEL_CROSSFIT_MEMBERSHIP_P6_DEVELOPMENT"
        if all(gates.values())
        else "FAIL_SAME_MODEL_CROSSFIT_MEMBERSHIP_P6_NO_GO"
    )
'''
VERDICT_REPL = '''    verdict = (
        "PASS_FINITE_SAMPLE_ROBUST_FLOOR_MEMBERSHIP_P7_DEVELOPMENT"
        if all(gates.values())
        else "FAIL_FINITE_SAMPLE_ROBUST_FLOOR_MEMBERSHIP_P7_NO_GO"
    )
'''

CLASS_ANCHOR = '''        "classification": "P5 joint held-out-seed geometry with direction candidates scored on the identical family-excluded cross-fit model that defines their seed floor; immutable promoted-v8 cores and rank",
'''
CLASS_REPL = '''        "classification": "P6 same-model cross-fit membership plus finite-sample second-order-statistic candidate floor only for directions with >=19 held-out recurrent seeds; immutable promoted-v8 cores and rank",
'''

CONFIG_ANCHOR = '''            "p6_parameter_search": False,
        },
'''
CONFIG_REPL = '''            "p6_parameter_search": False,
            "p7_membership_floor": "second-smallest held-out recurrent-seed probability iff seed_count >= 19; otherwise inherited minimum seed probability",
            "p7_robust_floor_min_seeds": P7_ROBUST_FLOOR_MIN_SEEDS,
            "p7_order_statistic_tuning": False,
            "p7_parameter_search": False,
        },
'''

METHOD_KEY_ANCHOR = '''        "p6": {k: v for k, v in p2_full.items() if k != "per_label"},
'''
METHOD_KEY_REPL = '''        "p7": {k: v for k, v in p2_full.items() if k != "per_label"},
'''
LARGE_KEY_ANCHOR = '''        "p6_large_shower": p2_large,
'''
LARGE_KEY_REPL = '''        "p7_large_shower": p2_large,
'''

DIAG_ANCHOR = '''            "p6_candidate_scoring_uses_final_all_family_model": False,
'''
DIAG_REPL = '''            "p6_candidate_scoring_uses_final_all_family_model": False,
            "p7_robust_floor_min_seeds": P7_ROBUST_FLOOR_MIN_SEEDS,
            "p7_second_order_statistic_directions": sum(int(r["seed_count"]) >= P7_ROBUST_FLOOR_MIN_SEEDS for r in reliability.values()),
            "p7_second_order_statistic_reliable_directions": sum(bool(r["reliable"]) and int(r["seed_count"]) >= P7_ROBUST_FLOOR_MIN_SEEDS for r in reliability.values()),
            "p7_membership_floor_strictly_above_seed_floor_directions": sum(float(r["membership_floor"]) > float(r["seed_floor"]) for r in reliability.values()),
'''

JSON_ANCHOR = '''    (args.output / "same_model_crossfit_membership_p6_development.json").write_text(json.dumps(result, indent=2) + "\\n")
'''
JSON_REPL = '''    (args.output / "finite_sample_robust_floor_membership_p7_development.json").write_text(json.dumps(result, indent=2) + "\\n")
'''
MD_ANCHOR = '''    (args.output / "SAME_MODEL_CROSSFIT_MEMBERSHIP_P6_DEVELOPMENT.md").write_text(
'''
MD_REPL = '''    (args.output / "FINITE_SAMPLE_ROBUST_FLOOR_MEMBERSHIP_P7_DEVELOPMENT.md").write_text(
'''
TITLE_ANCHOR = '''        "# OrbitTrace P6 same-model cross-fit membership development\\n\\n"
'''
TITLE_REPL = '''        "# OrbitTrace P7 finite-sample robust held-seed floor membership development\\n\\n"
'''
SUMMARY_ANCHOR = '''f"- v8 -> P6 macro F1: **{baseline_full['macro_f1']:.6f} -> {p2_full['macro_f1']:.6f}**\\n"'''
SUMMARY_REPL = '''f"- v8 -> P7 macro F1: **{baseline_full['macro_f1']:.6f} -> {p2_full['macro_f1']:.6f}**\\n"'''
QUALIFIED_ANCHOR = '''f"- v8 -> P6 qualified: **{baseline_full['qualified_matches']} -> {p2_full['qualified_matches']}**\\n"'''
QUALIFIED_REPL = '''f"- v8 -> P7 qualified: **{baseline_full['qualified_matches']} -> {p2_full['qualified_matches']}**\\n"'''
RECOVERY_ANCHOR = '''f"- v8 -> P6 recovery@100: **{baseline_full['recovered_at_100']} -> {p2_full['recovered_at_100']}**\\n"'''
RECOVERY_REPL = '''f"- v8 -> P7 recovery@100: **{baseline_full['recovered_at_100']} -> {p2_full['recovered_at_100']}**\\n"'''
PRECISION_ANCHOR = '''f"- v8 -> P6 top100 precision: **{baseline_full['top100_dominant_precision']:.6f} -> {p2_full['top100_dominant_precision']:.6f}**\\n"'''
PRECISION_REPL = '''f"- v8 -> P7 top100 precision: **{baseline_full['top100_dominant_precision']:.6f} -> {p2_full['top100_dominant_precision']:.6f}**\\n"'''
PRINT_ANCHOR = '''    print((args.output / "SAME_MODEL_CROSSFIT_MEMBERSHIP_P6_DEVELOPMENT.md").read_text(), flush=True)
'''
PRINT_REPL = '''    print((args.output / "FINITE_SAMPLE_ROBUST_FLOOR_MEMBERSHIP_P7_DEVELOPMENT.md").read_text(), flush=True)
'''


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply_p7_patch.py EXACT_P6 OUTPUT")
    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    raw = source.read_bytes()
    actual = digest(raw)
    if actual != EXPECTED_P6_SHA256:
        raise RuntimeError(f"exact P6 source SHA changed: {actual}")
    text = raw.decode("utf-8")
    for before, after, label in (
        (CONST_ANCHOR, CONST_REPL, "P7 finite-sample constant"),
        (FLOOR_ANCHOR, FLOOR_REPL, "P7 held-seed order-statistic floor"),
        (RECORD_ANCHOR, RECORD_REPL, "P7 reliability floor record"),
        (PAYLOAD_ANCHOR, PAYLOAD_REPL, "P7 crossfit declaration"),
        (SCORING_ANCHOR, SCORING_REPL, "P7 candidate floor comparison"),
        (ALLOWED_ANCHOR, ALLOWED_REPL, "P7 candidate inclusion gate"),
        (PROPOSAL_ANCHOR, PROPOSAL_REPL, "P7 proposal floor record"),
        (GATE_ANCHOR, GATE_REPL, "P7 integrity gates"),
        (VERDICT_ANCHOR, VERDICT_REPL, "P7 verdict"),
        (CLASS_ANCHOR, CLASS_REPL, "P7 classification"),
        (CONFIG_ANCHOR, CONFIG_REPL, "P7 configuration"),
        (METHOD_KEY_ANCHOR, METHOD_KEY_REPL, "P7 result method key"),
        (LARGE_KEY_ANCHOR, LARGE_KEY_REPL, "P7 large-shower key"),
        (DIAG_ANCHOR, DIAG_REPL, "P7 diagnostics"),
        (JSON_ANCHOR, JSON_REPL, "P7 JSON filename"),
        (MD_ANCHOR, MD_REPL, "P7 markdown filename"),
        (TITLE_ANCHOR, TITLE_REPL, "P7 title"),
        (SUMMARY_ANCHOR, SUMMARY_REPL, "P7 summary label"),
        (QUALIFIED_ANCHOR, QUALIFIED_REPL, "P7 qualified summary label"),
        (RECOVERY_ANCHOR, RECOVERY_REPL, "P7 recovery summary label"),
        (PRECISION_ANCHOR, PRECISION_REPL, "P7 precision summary label"),
        (PRINT_ANCHOR, PRINT_REPL, "P7 print filename"),
    ):
        text = replace_once(text, before, after, label)
    for before, after in MEMBERSHIP_NAMES:
        text = replace_once(text, before, after, f"membership output rename {before}")
    if "OrbitTrace-April" in text or "target_coordinate" in text:
        raise RuntimeError("forbidden target-specific token introduced")
    output.write_text(text, encoding="utf-8")
    print(f"P7_INPUT_P6_SHA256={EXPECTED_P6_SHA256}")
    print(f"P7_OUTPUT_SHA256={digest(text.encode('utf-8'))}")
    print("P7_PATCH_SCOPE=exact P6 plus second-smallest held-seed candidate floor iff n>=19; inherited reliability and all geometry/rank unchanged; no parameter search")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
