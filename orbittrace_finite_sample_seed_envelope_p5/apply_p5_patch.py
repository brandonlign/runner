#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

EXPECTED_P4_SHA256 = "290c4f1b6401eaab6f182760eaeaa2f91cc994854febf465f58f7cacc5d73b2a"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def replace_once(text: str, before: str, after: str, label: str) -> str:
    count = text.count(before)
    if count != 1:
        raise RuntimeError(f"P5 patch anchor {label} count={count}")
    return text.replace(before, after, 1)


CONST_ANCHOR = '''P3_FOLD_COUNT = 5
P3_NEGATIVE_TAIL_MAX = 0.10
P3_SEED_FLOOR_MIN = 0.5
'''
CONST_REPL = '''P3_FOLD_COUNT = 5
P3_NEGATIVE_TAIL_MAX = 0.10
P3_SEED_FLOOR_MIN = 0.5
# Two one-sided held-out sample-maximum tests.  The union-bound true-member
# rejection probability is <= 2/(n+1); require that to be <= the inherited
# 0.10 P3 tail scale.  Thus n >= 19.  This is not a searched parameter.
P5_ENVELOPE_MIN_SEEDS = 19
'''

SCORING_INIT_ANCHOR = '''    proposals_by_event: dict[str, list[dict[str, Any]]] = defaultdict(list)
    eps = np.finfo(np.float64).eps
    p4_envelope_rejected_above_seed_floor = 0
'''
SCORING_INIT_REPL = '''    proposals_by_event: dict[str, list[dict[str, Any]]] = defaultdict(list)
    eps = np.finfo(np.float64).eps
    p5_envelope_rejected_above_seed_floor = 0
    p5_envelope_applied_directions = 0
    p5_envelope_deferred_directions = 0
    p5_seed_floor_candidates_in_applied_directions = 0
    p5_seed_floor_candidates_in_deferred_directions = 0
'''

SCORING_GATE_ANCHOR = '''        seed_floor_allowed = probabilities >= float(gate["seed_floor"])
        feature_ceiling = np.asarray(gate["feature_ceiling"], dtype=np.float64)
        require(feature_ceiling.shape == (2,) and np.all(np.isfinite(feature_ceiling)), "P4 scoring ceiling invalid")
        within_envelope = np.all(features <= feature_ceiling[None, :], axis=1)
        p4_envelope_rejected_above_seed_floor += int(np.sum(seed_floor_allowed & ~within_envelope))
        allowed = seed_floor_allowed & within_envelope
        odds = probabilities / (1.0 - probabilities)
        for event_id, probability, odd, keep, feature_row in zip(ids, probabilities.tolist(), odds.tolist(), allowed.tolist(), features.tolist()):
            if not bool(keep):
                continue
            proposals_by_event[event_id].append({
                "family_index": int(direction["family_index"]),
                "family_id": str(direction["family_id"]),
                "source_year": int(direction["source_year"]),
                "target_year": int(direction["target_year"]),
                "probability": float(probability),
                "odds": float(odd),
                "seed_floor": float(gate["seed_floor"]),
                "d_obs": float(feature_row[0]),
                "d_orb": float(feature_row[1]),
                "obs_ceiling": float(feature_ceiling[0]),
                "orb_ceiling": float(feature_ceiling[1]),
            })
'''
SCORING_GATE_REPL = '''        seed_floor_allowed = probabilities >= float(gate["seed_floor"])
        feature_ceiling = np.asarray(gate["feature_ceiling"], dtype=np.float64)
        require(feature_ceiling.shape == (2,) and np.all(np.isfinite(feature_ceiling)), "P5 scoring ceiling invalid")
        seed_count = int(gate["seed_count"])
        envelope_applied = bool(seed_count >= P5_ENVELOPE_MIN_SEEDS)
        raw_within_envelope = np.all(features <= feature_ceiling[None, :], axis=1)
        if envelope_applied:
            p5_envelope_applied_directions += 1
            p5_seed_floor_candidates_in_applied_directions += int(np.sum(seed_floor_allowed))
            p5_envelope_rejected_above_seed_floor += int(np.sum(seed_floor_allowed & ~raw_within_envelope))
            allowed = seed_floor_allowed & raw_within_envelope
        else:
            p5_envelope_deferred_directions += 1
            p5_seed_floor_candidates_in_deferred_directions += int(np.sum(seed_floor_allowed))
            allowed = seed_floor_allowed
        odds = probabilities / (1.0 - probabilities)
        for event_id, probability, odd, keep, feature_row in zip(ids, probabilities.tolist(), odds.tolist(), allowed.tolist(), features.tolist()):
            if not bool(keep):
                continue
            proposals_by_event[event_id].append({
                "family_index": int(direction["family_index"]),
                "family_id": str(direction["family_id"]),
                "source_year": int(direction["source_year"]),
                "target_year": int(direction["target_year"]),
                "probability": float(probability),
                "odds": float(odd),
                "seed_floor": float(gate["seed_floor"]),
                "seed_count": seed_count,
                "envelope_applied": envelope_applied,
                "d_obs": float(feature_row[0]),
                "d_orb": float(feature_row[1]),
                "obs_ceiling": float(feature_ceiling[0]),
                "orb_ceiling": float(feature_ceiling[1]),
            })
'''

MEMBERSHIP_NAMES = (
    ('"p4_membership_pretruth.sha256"', '"p5_membership_pretruth.sha256"'),
    ('"p4_expanded_families.json.gz"', '"p5_expanded_families.json.gz"'),
    ('"p4_decisions_pretruth.sha256"', '"p5_decisions_pretruth.sha256"'),
    ('"p4_decisions_pretruth.json.gz"', '"p5_decisions_pretruth.json.gz"'),
)

GATE_ANCHOR = '''        "p4_coordinate_envelope_frozen_before_truth": len(crossfit_sha) == 64 and all(len(r.get("feature_ceiling", [])) == 2 for r in reliability.values()),
        "p4_heldout_seeds_inside_own_envelope": all(len(r.get("feature_ceiling", [])) == 2 for r in reliability.values()),
        "p4_every_surviving_proposal_inside_two_view_seed_envelope": all(
            float(p["d_obs"]) <= float(p["obs_ceiling"]) and float(p["d_orb"]) <= float(p["orb_ceiling"])
            for ps in proposals_by_event.values() for p in ps
        ),
        "expansion_nonvacuous": len(assignments) > 0,
'''
GATE_REPL = '''        "p4_coordinate_envelope_frozen_before_truth": len(crossfit_sha) == 64 and all(len(r.get("feature_ceiling", [])) == 2 for r in reliability.values()),
        "p4_heldout_seeds_inside_own_envelope": all(len(r.get("feature_ceiling", [])) == 2 for r in reliability.values()),
        "p5_finite_sample_min_seed_count_exactly_19": P5_ENVELOPE_MIN_SEEDS == 19,
        "p5_envelope_applied_iff_seed_count_at_least_19": all(
            bool(p["envelope_applied"]) == bool(int(p["seed_count"]) >= P5_ENVELOPE_MIN_SEEDS)
            for ps in proposals_by_event.values() for p in ps
        ),
        "p5_high_support_survivors_inside_exact_p4_envelope": all(
            (not bool(p["envelope_applied"]))
            or (float(p["d_obs"]) <= float(p["obs_ceiling"]) and float(p["d_orb"]) <= float(p["orb_ceiling"]))
            for ps in proposals_by_event.values() for p in ps
        ),
        "p5_low_support_survivors_use_p3_seed_floor_only": all(
            bool(p["envelope_applied"]) or int(p["seed_count"]) < P5_ENVELOPE_MIN_SEEDS
            for ps in proposals_by_event.values() for p in ps
        ),
        "p5_reliable_direction_partition_complete": p5_envelope_applied_directions + p5_envelope_deferred_directions == sum(bool(r["reliable"]) for r in reliability.values()),
        "expansion_nonvacuous": len(assignments) > 0,
'''

VERDICT_ANCHOR = '''    verdict = (
        "PASS_DUAL_VIEW_SEED_ENVELOPE_MEMBERSHIP_P4_DEVELOPMENT"
        if all(gates.values())
        else "FAIL_DUAL_VIEW_SEED_ENVELOPE_MEMBERSHIP_P4_NO_GO"
    )
'''
VERDICT_REPL = '''    verdict = (
        "PASS_FINITE_SAMPLE_SEED_ENVELOPE_MEMBERSHIP_P5_DEVELOPMENT"
        if all(gates.values())
        else "FAIL_FINITE_SAMPLE_SEED_ENVELOPE_MEMBERSHIP_P5_NO_GO"
    )
'''

CLASS_ANCHOR = '''        "classification": "P3 cross-fitted seed-floor membership plus coordinate-wise held-out two-view recurrent-seed envelope; immutable promoted-v8 cores and rank",
'''
CLASS_REPL = '''        "classification": "P3/P4 two-view membership with finite-sample-valid application of the held-out recurrent-seed envelope; immutable promoted-v8 cores and rank",
'''

CONFIG_ANCHOR = '''            "p4_two_view_seed_envelope": "candidate d_obs <= max held-out seed d_obs AND candidate d_orb <= max held-out seed d_orb",
            "p4_envelope_quantile_or_multiplier": None,
            "p4_parameter_search": False,
        },
'''
CONFIG_REPL = '''            "p4_two_view_seed_envelope": "candidate d_obs <= max held-out seed d_obs AND candidate d_orb <= max held-out seed d_orb",
            "p4_envelope_quantile_or_multiplier": None,
            "p4_parameter_search": False,
            "p5_envelope_min_seed_count": P5_ENVELOPE_MIN_SEEDS,
            "p5_finite_sample_derivation": "apply two-view sample-maximum envelope only when 2/(n+1) <= 0.10; therefore n >= 19",
            "p5_low_support_rule": "if held-out seed_count < 19, retain exact P3 seed-floor proposal rule with no coordinate-envelope rejection",
            "p5_parameter_search": False,
        },
'''

METHOD_KEY_ANCHOR = '''        "p4": {k: v for k, v in p2_full.items() if k != "per_label"},
'''
METHOD_KEY_REPL = '''        "p5": {k: v for k, v in p2_full.items() if k != "per_label"},
'''
LARGE_KEY_ANCHOR = '''        "p4_large_shower": p2_large,
'''
LARGE_KEY_REPL = '''        "p5_large_shower": p2_large,
'''

DIAG_ANCHOR = '''            "p4_decisions_pretruth_sha256": decision_sha,
            "p4_envelope_rejected_above_seed_floor": p4_envelope_rejected_above_seed_floor,
'''
DIAG_REPL = '''            "p5_decisions_pretruth_sha256": decision_sha,
            "p5_envelope_min_seed_count": P5_ENVELOPE_MIN_SEEDS,
            "p5_envelope_applied_directions": p5_envelope_applied_directions,
            "p5_envelope_deferred_directions": p5_envelope_deferred_directions,
            "p5_seed_floor_candidates_in_applied_directions": p5_seed_floor_candidates_in_applied_directions,
            "p5_seed_floor_candidates_in_deferred_directions": p5_seed_floor_candidates_in_deferred_directions,
            "p5_envelope_rejected_above_seed_floor": p5_envelope_rejected_above_seed_floor,
'''

JSON_ANCHOR = '''    (args.output / "dual_view_seed_envelope_membership_p4_development.json").write_text(json.dumps(result, indent=2) + "\\n")
'''
JSON_REPL = '''    (args.output / "finite_sample_seed_envelope_membership_p5_development.json").write_text(json.dumps(result, indent=2) + "\\n")
'''
MD_ANCHOR = '''    (args.output / "DUAL_VIEW_SEED_ENVELOPE_MEMBERSHIP_P4_DEVELOPMENT.md").write_text(
'''
MD_REPL = '''    (args.output / "FINITE_SAMPLE_SEED_ENVELOPE_MEMBERSHIP_P5_DEVELOPMENT.md").write_text(
'''
TITLE_ANCHOR = '''        "# OrbitTrace P4 dual-view held-out seed-envelope membership development\\n\\n"
'''
TITLE_REPL = '''        "# OrbitTrace P5 finite-sample-valid dual-view seed-envelope membership development\\n\\n"
'''
SUMMARY_ANCHOR = '''f"- v8 -> P4 macro F1: **{baseline_full['macro_f1']:.6f} -> {p2_full['macro_f1']:.6f}**\\n"'''
SUMMARY_REPL = '''f"- v8 -> P5 macro F1: **{baseline_full['macro_f1']:.6f} -> {p2_full['macro_f1']:.6f}**\\n"'''
QUALIFIED_LABEL_ANCHOR = '''f"- v8 -> P2 qualified: **{baseline_full['qualified_matches']} -> {p2_full['qualified_matches']}**\\n"'''
QUALIFIED_LABEL_REPL = '''f"- v8 -> P5 qualified: **{baseline_full['qualified_matches']} -> {p2_full['qualified_matches']}**\\n"'''
RECOVERY_LABEL_ANCHOR = '''f"- v8 -> P2 recovery@100: **{baseline_full['recovered_at_100']} -> {p2_full['recovered_at_100']}**\\n"'''
RECOVERY_LABEL_REPL = '''f"- v8 -> P5 recovery@100: **{baseline_full['recovered_at_100']} -> {p2_full['recovered_at_100']}**\\n"'''
PRECISION_LABEL_ANCHOR = '''f"- v8 -> P2 top100 precision: **{baseline_full['top100_dominant_precision']:.6f} -> {p2_full['top100_dominant_precision']:.6f}**\\n"'''
PRECISION_LABEL_REPL = '''f"- v8 -> P5 top100 precision: **{baseline_full['top100_dominant_precision']:.6f} -> {p2_full['top100_dominant_precision']:.6f}**\\n"'''
PRINT_ANCHOR = '''    print((args.output / "DUAL_VIEW_SEED_ENVELOPE_MEMBERSHIP_P4_DEVELOPMENT.md").read_text(), flush=True)
'''
PRINT_REPL = '''    print((args.output / "FINITE_SAMPLE_SEED_ENVELOPE_MEMBERSHIP_P5_DEVELOPMENT.md").read_text(), flush=True)
'''


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply_p5_patch.py EXACT_P4 OUTPUT")
    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    raw = source.read_bytes()
    actual = digest(raw)
    if actual != EXPECTED_P4_SHA256:
        raise RuntimeError(f"exact P4 source SHA changed: {actual}")
    text = raw.decode("utf-8")
    for before, after, label in (
        (CONST_ANCHOR, CONST_REPL, "finite-sample constant"),
        (SCORING_INIT_ANCHOR, SCORING_INIT_REPL, "P5 diagnostics"),
        (SCORING_GATE_ANCHOR, SCORING_GATE_REPL, "finite-sample envelope application"),
        (GATE_ANCHOR, GATE_REPL, "P5 integrity gates"),
        (VERDICT_ANCHOR, VERDICT_REPL, "P5 verdict"),
        (CLASS_ANCHOR, CLASS_REPL, "P5 classification"),
        (CONFIG_ANCHOR, CONFIG_REPL, "P5 configuration"),
        (METHOD_KEY_ANCHOR, METHOD_KEY_REPL, "P5 result method key"),
        (LARGE_KEY_ANCHOR, LARGE_KEY_REPL, "P5 large-shower key"),
        (DIAG_ANCHOR, DIAG_REPL, "P5 diagnostics output"),
        (JSON_ANCHOR, JSON_REPL, "P5 JSON filename"),
        (MD_ANCHOR, MD_REPL, "P5 markdown filename"),
        (TITLE_ANCHOR, TITLE_REPL, "P5 markdown title"),
        (SUMMARY_ANCHOR, SUMMARY_REPL, "P5 macro label"),
        (QUALIFIED_LABEL_ANCHOR, QUALIFIED_LABEL_REPL, "P5 qualified label"),
        (RECOVERY_LABEL_ANCHOR, RECOVERY_LABEL_REPL, "P5 recovery label"),
        (PRECISION_LABEL_ANCHOR, PRECISION_LABEL_REPL, "P5 precision label"),
        (PRINT_ANCHOR, PRINT_REPL, "P5 print filename"),
    ):
        text = replace_once(text, before, after, label)
    for before, after in MEMBERSHIP_NAMES:
        text = replace_once(text, before, after, f"P5 output rename {before}")
    if "OrbitTrace-April" in text or "target_coordinate" in text:
        raise RuntimeError("forbidden target-specific token introduced")
    output.write_text(text, encoding="utf-8")
    print(f"P5_INPUT_P4_SHA256={EXPECTED_P4_SHA256}")
    print(f"P5_OUTPUT_SHA256={digest(text.encode('utf-8'))}")
    print("P5_PATCH_SCOPE=exact P4 except its two-view seed envelope is applied only when held-out seed_count >= 19, derived from 2/(n+1) <= 0.10; no parameter search")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
