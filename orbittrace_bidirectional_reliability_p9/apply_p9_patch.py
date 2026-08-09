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


SCORING_GATE_ANCHOR = '''        key = f"{direction['family_id']}|{direction['source_year']}|{direction['target_year']}"
        gate = reliability[key]
        scoring_fold = int(gate["fold"])
'''
SCORING_GATE_REPL = '''        key = f"{direction['family_id']}|{direction['source_year']}|{direction['target_year']}"
        gate = reliability[key]
        reciprocal_key = f"{direction['family_id']}|{direction['target_year']}|{direction['source_year']}"
        require(reciprocal_key in reliability, f"P9 missing reciprocal reliability key {reciprocal_key}")
        reciprocal_gate = reliability[reciprocal_key]
        scoring_fold = int(gate["fold"])
'''

RELIABILITY_VETO_ANCHOR = '''        if not bool(gate["reliable"]):
'''
RELIABILITY_VETO_REPL = '''        if not (bool(gate["reliable"]) and bool(reciprocal_gate["reliable"])):
'''

PROPOSAL_ANCHOR = '''                "membership_floor_exclusion_budget": P3_NEGATIVE_TAIL_MAX,
                "scoring_fold": scoring_fold,
'''
PROPOSAL_REPL = '''                "membership_floor_exclusion_budget": P3_NEGATIVE_TAIL_MAX,
                "p9_bidirectional_reliability": True,
                "scoring_fold": scoring_fold,
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
'''
GATE_REPL = '''        "p8_no_p7_unreliable_direction_can_propose": all(
            bool(reliability[f"{p['family_id']}|{p['source_year']}|{p['target_year']}"]["reliable"])
            for ps in proposals_by_event.values() for p in ps
        ),
        "p9_pretruth_family_reliability_pattern_reproduced": (
            sum(
                sum(bool(r["reliable"]) for r in reliability.values() if str(r["family_id"]) == str(fid)) == 2
                for fid in family_fold
            ) == 218
            and sum(
                sum(bool(r["reliable"]) for r in reliability.values() if str(r["family_id"]) == str(fid)) == 1
                for fid in family_fold
            ) == 3
            and sum(
                sum(bool(r["reliable"]) for r in reliability.values() if str(r["family_id"]) == str(fid)) == 0
                for fid in family_fold
            ) == 5
        ),
        "p9_only_bidirectionally_reliable_families_can_propose": all(
            bool(reliability[f"{p['family_id']}|{p['source_year']}|{p['target_year']}"]["reliable"])
            and bool(reliability[f"{p['family_id']}|{p['target_year']}|{p['source_year']}"]["reliable"])
            and bool(p.get("p9_bidirectional_reliability", False))
            for ps in proposals_by_event.values() for p in ps
        ),
'''

VERDICT_ANCHOR = '''    verdict = (
        "PASS_FINITE_SAMPLE_10PCT_ORDER_STAT_MEMBERSHIP_P8_DEVELOPMENT"
        if all(gates.values())
        else "FAIL_FINITE_SAMPLE_10PCT_ORDER_STAT_MEMBERSHIP_P8_NO_GO"
    )
'''
VERDICT_REPL = '''    verdict = (
        "PASS_BIDIRECTIONAL_RELIABILITY_MEMBERSHIP_P9_DEVELOPMENT"
        if all(gates.values())
        else "FAIL_BIDIRECTIONAL_RELIABILITY_MEMBERSHIP_P9_NO_GO"
    )
'''

CLASS_ANCHOR = '''        "classification": "P6 same-model cross-fit membership plus full finite-sample order-statistic candidate floor spending only the inherited P3 0.10 scale; immutable promoted-v8 cores and rank",
'''
CLASS_REPL = '''        "classification": "Exact P8 membership with nonseed halo growth allowed only for recurrent families whose two reciprocal cross-year directions both satisfy the inherited P3 reliability boolean; immutable promoted-v8 cores and rank",
'''

CONFIG_ANCHOR = '''            "p8_order_statistic_tuning": False,
            "p8_parameter_search": False,
'''
CONFIG_REPL = '''            "p8_order_statistic_tuning": False,
            "p8_parameter_search": False,
            "p9_bidirectional_reliability_rule": "both reciprocal P3 direction reliability booleans must be true before either direction may add nonseed members",
            "p9_new_numeric_thresholds": False,
            "p9_parameter_search": False,
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
            "p9_bidirectionally_reliable_families": sum(
                sum(bool(r["reliable"]) for r in reliability.values() if str(r["family_id"]) == str(fid)) == 2
                for fid in family_fold
            ),
            "p9_one_sided_reliable_families": sum(
                sum(bool(r["reliable"]) for r in reliability.values() if str(r["family_id"]) == str(fid)) == 1
                for fid in family_fold
            ),
            "p9_zero_sided_reliable_families": sum(
                sum(bool(r["reliable"]) for r in reliability.values() if str(r["family_id"]) == str(fid)) == 0
                for fid in family_fold
            ),
            "p9_proposals_from_non_bidirectionally_reliable_families": sum(
                not (
                    bool(reliability[f"{p['family_id']}|{p['source_year']}|{p['target_year']}"]["reliable"])
                    and bool(reliability[f"{p['family_id']}|{p['target_year']}|{p['source_year']}"]["reliable"])
                )
                for ps in proposals_by_event.values() for p in ps
            ),
'''

JSON_ANCHOR = '''    (args.output / "finite_sample_10pct_order_stat_membership_p8_development.json").write_text(json.dumps(result, indent=2) + "\\n")
'''
JSON_REPL = '''    (args.output / "bidirectional_reliability_membership_p9_development.json").write_text(json.dumps(result, indent=2) + "\\n")
'''
MD_ANCHOR = '''    (args.output / "FINITE_SAMPLE_10PCT_ORDER_STAT_MEMBERSHIP_P8_DEVELOPMENT.md").write_text(
'''
MD_REPL = '''    (args.output / "BIDIRECTIONAL_RELIABILITY_MEMBERSHIP_P9_DEVELOPMENT.md").write_text(
'''
TITLE_ANCHOR = '''        "# OrbitTrace P8 full finite-sample 10% order-statistic membership development\\n\\n"
'''
TITLE_REPL = '''        "# OrbitTrace P9 bidirectional recurrent-reliability membership development\\n\\n"
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
PRINT_REPL = '''    print((args.output / "BIDIRECTIONAL_RELIABILITY_MEMBERSHIP_P9_DEVELOPMENT.md").read_text(), flush=True)
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
        (SCORING_GATE_ANCHOR, SCORING_GATE_REPL, "reciprocal reliability lookup"),
        (RELIABILITY_VETO_ANCHOR, RELIABILITY_VETO_REPL, "bidirectional reliability veto"),
        (PROPOSAL_ANCHOR, PROPOSAL_REPL, "proposal reciprocal reliability provenance"),
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
    print("P9_PATCH_SCOPE=exact P8 plus reciprocal P3 reliability required before any nonseed proposal; no threshold/model/geometry/rank change or parameter search")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
