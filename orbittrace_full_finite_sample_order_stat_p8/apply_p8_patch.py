#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

EXPECTED_P7_SHA256 = "89cf23c9d58692aedfaf12a9c2b7de4a08d641e6326794d82872f2e18608df54"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def replace_once(text: str, before: str, after: str, label: str) -> str:
    count = text.count(before)
    if count != 1:
        raise RuntimeError(f"P8 patch anchor {label} count={count}")
    return text.replace(before, after, 1)


CONST_ANCHOR = '''P3_SEED_FLOOR_MIN = 0.5
P7_ROBUST_FLOOR_MIN_SEEDS = 19
'''
CONST_REPL = '''P3_SEED_FLOOR_MIN = 0.5
'''

FLOOR_ANCHOR = '''            membership_floor_rank = 2 if len(sorted_seed_probabilities) >= P7_ROBUST_FLOOR_MIN_SEEDS else 1
            membership_floor = float(sorted_seed_probabilities[membership_floor_rank - 1])
            require(membership_floor >= seed_floor, "P7 robust membership floor below inherited minimum seed floor")
'''
FLOOR_REPL = '''            membership_floor_rank = max(
                1,
                int(math.floor(P3_NEGATIVE_TAIL_MAX * (len(sorted_seed_probabilities) + 1))),
            )
            require(1 <= membership_floor_rank <= len(sorted_seed_probabilities), "P8 invalid finite-sample order-statistic rank")
            membership_floor = float(sorted_seed_probabilities[membership_floor_rank - 1])
            require(membership_floor >= seed_floor, "P8 order-statistic membership floor below inherited minimum seed floor")
'''

RECORD_ANCHOR = '''                "membership_floor": membership_floor,
                "membership_floor_rank": membership_floor_rank,
                "membership_floor_min_seeds": P7_ROBUST_FLOOR_MIN_SEEDS,
                "membership_floor_rule": "second-smallest held-out recurrent-seed probability iff seed_count >= 19; otherwise inherited minimum seed probability",
'''
RECORD_REPL = '''                "membership_floor": membership_floor,
                "membership_floor_rank": membership_floor_rank,
                "membership_floor_exclusion_budget": P3_NEGATIVE_TAIL_MAX,
                "membership_floor_rule": "k-th smallest held-out recurrent-seed probability with k=max(1,floor(P3_NEGATIVE_TAIL_MAX*(seed_count+1)))",
'''

PAYLOAD_ANCHOR = '''        "p7_membership_floor": "second-smallest held-out recurrent-seed probability iff seed_count >= 19; otherwise inherited minimum seed probability",
        "p7_robust_floor_min_seeds": P7_ROBUST_FLOOR_MIN_SEEDS,
        "p7_order_statistic_tuning": False,
'''
PAYLOAD_REPL = '''        "p8_membership_floor": "k-th smallest held-out recurrent-seed probability with k=max(1,floor(P3_NEGATIVE_TAIL_MAX*(seed_count+1)))",
        "p8_order_statistic_alpha_source": "P3_NEGATIVE_TAIL_MAX",
        "p8_order_statistic_alpha": P3_NEGATIVE_TAIL_MAX,
        "p8_order_statistic_tuning": False,
'''

PROPOSAL_ANCHOR = '''                "membership_floor_rank": int(gate["membership_floor_rank"]),
                "scoring_fold": scoring_fold,
'''
PROPOSAL_REPL = '''                "membership_floor_rank": int(gate["membership_floor_rank"]),
                "membership_floor_exclusion_budget": P3_NEGATIVE_TAIL_MAX,
                "scoring_fold": scoring_fold,
'''

MEMBERSHIP_NAMES = (
    ('"p7_membership_pretruth.sha256"', '"p8_membership_pretruth.sha256"'),
    ('"p7_expanded_families.json.gz"', '"p8_expanded_families.json.gz"'),
    ('"p7_decisions_pretruth.sha256"', '"p8_decisions_pretruth.sha256"'),
    ('"p7_decisions_pretruth.json.gz"', '"p8_decisions_pretruth.json.gz"'),
)

GATE_ANCHOR = '''        "p7_exact_robust_floor_min_seeds": P7_ROBUST_FLOOR_MIN_SEEDS == 19,
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
'''
GATE_REPL = '''        "p8_exact_finite_sample_order_statistic_rank": all(
            int(r["membership_floor_rank"]) == max(
                1,
                int(math.floor(P3_NEGATIVE_TAIL_MAX * (int(r["seed_count"]) + 1))),
            )
            for r in reliability.values()
        ),
        "p8_order_statistic_rank_within_seed_vector": all(
            1 <= int(r["membership_floor_rank"]) <= int(r["seed_count"])
            for r in reliability.values()
        ),
        "p8_order_statistic_exclusion_budget_not_exceeded": all(
            int(r["membership_floor_rank"]) == 1
            or float(r["membership_floor_rank"]) / float(int(r["seed_count"]) + 1) <= P3_NEGATIVE_TAIL_MAX + 1e-15
            for r in reliability.values()
        ),
        "p8_rank_one_directions_keep_inherited_minimum_floor": all(
            int(r["membership_floor_rank"]) != 1 or float(r["membership_floor"]) == float(r["seed_floor"])
            for r in reliability.values()
        ),
        "p8_every_surviving_proposal_meets_membership_floor": all(
            float(p["probability"]) >= float(p["membership_floor"])
            for ps in proposals_by_event.values() for p in ps
        ),
        "p8_no_p7_unreliable_direction_can_propose": all(
            bool(reliability[f"{p['family_id']}|{p['source_year']}|{p['target_year']}"]["reliable"])
            for ps in proposals_by_event.values() for p in ps
        ),
'''

VERDICT_ANCHOR = '''    verdict = (
        "PASS_FINITE_SAMPLE_ROBUST_FLOOR_MEMBERSHIP_P7_DEVELOPMENT"
        if all(gates.values())
        else "FAIL_FINITE_SAMPLE_ROBUST_FLOOR_MEMBERSHIP_P7_NO_GO"
    )
'''
VERDICT_REPL = '''    verdict = (
        "PASS_FINITE_SAMPLE_10PCT_ORDER_STAT_MEMBERSHIP_P8_DEVELOPMENT"
        if all(gates.values())
        else "FAIL_FINITE_SAMPLE_10PCT_ORDER_STAT_MEMBERSHIP_P8_NO_GO"
    )
'''

CLASS_ANCHOR = '''        "classification": "P6 same-model cross-fit membership plus finite-sample second-order-statistic candidate floor only for directions with >=19 held-out recurrent seeds; immutable promoted-v8 cores and rank",
'''
CLASS_REPL = '''        "classification": "P6 same-model cross-fit membership plus full finite-sample order-statistic candidate floor spending only the inherited P3 0.10 scale; immutable promoted-v8 cores and rank",
'''

CONFIG_ANCHOR = '''            "p7_membership_floor": "second-smallest held-out recurrent-seed probability iff seed_count >= 19; otherwise inherited minimum seed probability",
            "p7_robust_floor_min_seeds": P7_ROBUST_FLOOR_MIN_SEEDS,
            "p7_order_statistic_tuning": False,
            "p7_parameter_search": False,
'''
CONFIG_REPL = '''            "p8_membership_floor": "k-th smallest held-out recurrent-seed probability with k=max(1,floor(P3_NEGATIVE_TAIL_MAX*(seed_count+1)))",
            "p8_order_statistic_alpha_source": "P3_NEGATIVE_TAIL_MAX",
            "p8_order_statistic_alpha": P3_NEGATIVE_TAIL_MAX,
            "p8_order_statistic_tuning": False,
            "p8_parameter_search": False,
'''

METHOD_KEY_ANCHOR = '''        "p7": {k: v for k, v in p2_full.items() if k != "per_label"},
'''
METHOD_KEY_REPL = '''        "p8": {k: v for k, v in p2_full.items() if k != "per_label"},
'''
LARGE_KEY_ANCHOR = '''        "p7_large_shower": p2_large,
'''
LARGE_KEY_REPL = '''        "p8_large_shower": p2_large,
'''

DIAG_ANCHOR = '''            "p7_robust_floor_min_seeds": P7_ROBUST_FLOOR_MIN_SEEDS,
            "p7_second_order_statistic_directions": sum(int(r["seed_count"]) >= P7_ROBUST_FLOOR_MIN_SEEDS for r in reliability.values()),
            "p7_second_order_statistic_reliable_directions": sum(bool(r["reliable"]) and int(r["seed_count"]) >= P7_ROBUST_FLOOR_MIN_SEEDS for r in reliability.values()),
            "p7_membership_floor_strictly_above_seed_floor_directions": sum(float(r["membership_floor"]) > float(r["seed_floor"]) for r in reliability.values()),
'''
DIAG_REPL = '''            "p8_order_statistic_alpha": P3_NEGATIVE_TAIL_MAX,
            "p8_rank_gt1_directions": sum(int(r["membership_floor_rank"]) > 1 for r in reliability.values()),
            "p8_rank_gt1_reliable_directions": sum(bool(r["reliable"]) and int(r["membership_floor_rank"]) > 1 for r in reliability.values()),
            "p8_rank_gt2_reliable_directions": sum(bool(r["reliable"]) and int(r["membership_floor_rank"]) > 2 for r in reliability.values()),
            "p8_max_membership_floor_rank": max(int(r["membership_floor_rank"]) for r in reliability.values()),
            "p8_membership_floor_strictly_above_seed_floor_directions": sum(float(r["membership_floor"]) > float(r["seed_floor"]) for r in reliability.values()),
'''

JSON_ANCHOR = '''    (args.output / "finite_sample_robust_floor_membership_p7_development.json").write_text(json.dumps(result, indent=2) + "\\n")
'''
JSON_REPL = '''    (args.output / "finite_sample_10pct_order_stat_membership_p8_development.json").write_text(json.dumps(result, indent=2) + "\\n")
'''
MD_ANCHOR = '''    (args.output / "FINITE_SAMPLE_ROBUST_FLOOR_MEMBERSHIP_P7_DEVELOPMENT.md").write_text(
'''
MD_REPL = '''    (args.output / "FINITE_SAMPLE_10PCT_ORDER_STAT_MEMBERSHIP_P8_DEVELOPMENT.md").write_text(
'''
TITLE_ANCHOR = '''        "# OrbitTrace P7 finite-sample robust held-seed floor membership development\\n\\n"
'''
TITLE_REPL = '''        "# OrbitTrace P8 full finite-sample 10% order-statistic membership development\\n\\n"
'''
SUMMARY_ANCHOR = '''f"- v8 -> P7 macro F1: **{baseline_full['macro_f1']:.6f} -> {p2_full['macro_f1']:.6f}**\\n"'''
SUMMARY_REPL = '''f"- v8 -> P8 macro F1: **{baseline_full['macro_f1']:.6f} -> {p2_full['macro_f1']:.6f}**\\n"'''
QUALIFIED_ANCHOR = '''f"- v8 -> P7 qualified: **{baseline_full['qualified_matches']} -> {p2_full['qualified_matches']}**\\n"'''
QUALIFIED_REPL = '''f"- v8 -> P8 qualified: **{baseline_full['qualified_matches']} -> {p2_full['qualified_matches']}**\\n"'''
RECOVERY_ANCHOR = '''f"- v8 -> P7 recovery@100: **{baseline_full['recovered_at_100']} -> {p2_full['recovered_at_100']}**\\n"'''
RECOVERY_REPL = '''f"- v8 -> P8 recovery@100: **{baseline_full['recovered_at_100']} -> {p2_full['recovered_at_100']}**\\n"'''
PRECISION_ANCHOR = '''f"- v8 -> P7 top100 precision: **{baseline_full['top100_dominant_precision']:.6f} -> {p2_full['top100_dominant_precision']:.6f}**\\n"'''
PRECISION_REPL = '''f"- v8 -> P8 top100 precision: **{baseline_full['top100_dominant_precision']:.6f} -> {p2_full['top100_dominant_precision']:.6f}**\\n"'''
PRINT_ANCHOR = '''    print((args.output / "FINITE_SAMPLE_ROBUST_FLOOR_MEMBERSHIP_P7_DEVELOPMENT.md").read_text(), flush=True)
'''
PRINT_REPL = '''    print((args.output / "FINITE_SAMPLE_10PCT_ORDER_STAT_MEMBERSHIP_P8_DEVELOPMENT.md").read_text(), flush=True)
'''


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply_p8_patch.py EXACT_P7 OUTPUT")
    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    raw = source.read_bytes()
    actual = digest(raw)
    if actual != EXPECTED_P7_SHA256:
        raise RuntimeError(f"exact P7 source SHA changed: {actual}")
    text = raw.decode("utf-8")
    for before, after, label in (
        (CONST_ANCHOR, CONST_REPL, "remove P7 fixed-support constant"),
        (FLOOR_ANCHOR, FLOOR_REPL, "P8 full finite-sample rank"),
        (RECORD_ANCHOR, RECORD_REPL, "P8 reliability rank record"),
        (PAYLOAD_ANCHOR, PAYLOAD_REPL, "P8 crossfit declaration"),
        (PROPOSAL_ANCHOR, PROPOSAL_REPL, "P8 proposal budget record"),
        (GATE_ANCHOR, GATE_REPL, "P8 integrity gates"),
        (VERDICT_ANCHOR, VERDICT_REPL, "P8 verdict"),
        (CLASS_ANCHOR, CLASS_REPL, "P8 classification"),
        (CONFIG_ANCHOR, CONFIG_REPL, "P8 configuration"),
        (METHOD_KEY_ANCHOR, METHOD_KEY_REPL, "P8 result method key"),
        (LARGE_KEY_ANCHOR, LARGE_KEY_REPL, "P8 large-shower key"),
        (DIAG_ANCHOR, DIAG_REPL, "P8 diagnostics"),
        (JSON_ANCHOR, JSON_REPL, "P8 JSON filename"),
        (MD_ANCHOR, MD_REPL, "P8 markdown filename"),
        (TITLE_ANCHOR, TITLE_REPL, "P8 title"),
        (SUMMARY_ANCHOR, SUMMARY_REPL, "P8 summary label"),
        (QUALIFIED_ANCHOR, QUALIFIED_REPL, "P8 qualified summary label"),
        (RECOVERY_ANCHOR, RECOVERY_REPL, "P8 recovery summary label"),
        (PRECISION_ANCHOR, PRECISION_REPL, "P8 precision summary label"),
        (PRINT_ANCHOR, PRINT_REPL, "P8 print filename"),
    ):
        text = replace_once(text, before, after, label)
    for before, after in MEMBERSHIP_NAMES:
        text = replace_once(text, before, after, f"membership output rename {before}")
    if "P7_ROBUST_FLOOR_MIN_SEEDS" in text:
        raise RuntimeError("obsolete P7 fixed support threshold remains")
    if "OrbitTrace-April" in text or "target_coordinate" in text:
        raise RuntimeError("forbidden target-specific token introduced")
    output.write_text(text, encoding="utf-8")
    print(f"P8_INPUT_P7_SHA256={EXPECTED_P7_SHA256}")
    print(f"P8_OUTPUT_SHA256={digest(text.encode('utf-8'))}")
    print("P8_PATCH_SCOPE=exact P7 with full finite-sample k=max(1,floor(P3_NEGATIVE_TAIL_MAX*(n+1))) candidate floor; no alpha/rank search; inherited reliability/geometry/rank unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
