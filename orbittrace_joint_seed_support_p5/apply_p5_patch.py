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


SUPPORT_ANCHOR = '''            feature_ceiling = np.max(xp, axis=0).astype(np.float64, copy=False)
            require(feature_ceiling.shape == (2,) and np.all(np.isfinite(feature_ceiling)), "P4 invalid two-view held-out seed ceiling")
            require(np.all(xp <= feature_ceiling[None, :]), "P4 held-out seed excluded by its own coordinate envelope")
            key = f"{d['family_id']}|{d['source_year']}|{d['target_year']}"
'''
SUPPORT_REPL = '''            feature_ceiling = np.max(xp, axis=0).astype(np.float64, copy=False)
            require(feature_ceiling.shape == (2,) and np.all(np.isfinite(feature_ceiling)), "P4 invalid two-view held-out seed ceiling")
            require(np.all(xp <= feature_ceiling[None, :]), "P4 held-out seed excluded by its own coordinate envelope")
            maximal_rows = []
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
            key = f"{d['family_id']}|{d['source_year']}|{d['target_year']}"
'''

RECORD_ANCHOR = '''                "feature_ceiling": feature_ceiling.tolist(),
                "feature_ceiling_rule": "coordinate-wise maximum held-out recurrent-seed [d_obs,d_orb]",
                "positive_scores_float64_sha256": hashlib.sha256(np.ascontiguousarray(pp, dtype="<f8").tobytes()).hexdigest(),
'''
RECORD_REPL = '''                "feature_ceiling": feature_ceiling.tolist(),
                "feature_ceiling_rule": "coordinate-wise maximum held-out recurrent-seed [d_obs,d_orb]",
                "joint_seed_support": joint_seed_support.tolist(),
                "joint_seed_support_rule": "componentwise-maximal held-out recurrent-seed [d_obs,d_orb] vectors; candidate must be <= one actual support vector in both coordinates",
                "joint_seed_support_float64_sha256": hashlib.sha256(np.ascontiguousarray(joint_seed_support, dtype="<f8").tobytes()).hexdigest(),
                "positive_scores_float64_sha256": hashlib.sha256(np.ascontiguousarray(pp, dtype="<f8").tobytes()).hexdigest(),
'''

PAYLOAD_ANCHOR = '''        "p4_envelope_tuning": False,
        "no_known_shower_truth_used": True,
'''
PAYLOAD_REPL = '''        "p4_envelope_tuning": False,
        "p5_joint_seed_support": "candidate [d_obs,d_orb] must be componentwise <= at least one actual componentwise-maximal held-out recurrent-seed vector",
        "p5_support_tuning": False,
        "no_known_shower_truth_used": True,
'''

SCORING_INIT_ANCHOR = '''    p4_envelope_rejected_above_seed_floor = 0
'''
SCORING_INIT_REPL = '''    p4_envelope_rejected_above_seed_floor = 0
    p5_joint_support_rejected_inside_p4 = 0
'''

SCORING_GATE_ANCHOR = '''        seed_floor_allowed = probabilities >= float(gate["seed_floor"])
        feature_ceiling = np.asarray(gate["feature_ceiling"], dtype=np.float64)
        require(feature_ceiling.shape == (2,) and np.all(np.isfinite(feature_ceiling)), "P4 scoring ceiling invalid")
        within_envelope = np.all(features <= feature_ceiling[None, :], axis=1)
        p4_envelope_rejected_above_seed_floor += int(np.sum(seed_floor_allowed & ~within_envelope))
        allowed = seed_floor_allowed & within_envelope
        odds = probabilities / (1.0 - probabilities)
'''
SCORING_GATE_REPL = '''        seed_floor_allowed = probabilities >= float(gate["seed_floor"])
        feature_ceiling = np.asarray(gate["feature_ceiling"], dtype=np.float64)
        require(feature_ceiling.shape == (2,) and np.all(np.isfinite(feature_ceiling)), "P4 scoring ceiling invalid")
        within_envelope = np.all(features <= feature_ceiling[None, :], axis=1)
        p4_envelope_rejected_above_seed_floor += int(np.sum(seed_floor_allowed & ~within_envelope))
        joint_seed_support = np.asarray(gate["joint_seed_support"], dtype=np.float64)
        require(joint_seed_support.ndim == 2 and joint_seed_support.shape[1] == 2 and len(joint_seed_support) >= 1 and np.all(np.isfinite(joint_seed_support)), "P5 scoring joint seed support invalid")
        jointly_supported = np.zeros(len(features), dtype=bool)
        for support_row in joint_seed_support:
            jointly_supported |= np.all(features <= support_row[None, :], axis=1)
        require(not np.any(jointly_supported & ~within_envelope), "P5 joint support escaped P4 coordinate envelope")
        p5_joint_support_rejected_inside_p4 += int(np.sum(seed_floor_allowed & within_envelope & ~jointly_supported))
        allowed = seed_floor_allowed & jointly_supported
        odds = probabilities / (1.0 - probabilities)
'''

MEMBERSHIP_NAMES = (
    ('"p4_membership_pretruth.sha256"', '"p5_membership_pretruth.sha256"'),
    ('"p4_expanded_families.json.gz"', '"p5_expanded_families.json.gz"'),
    ('"p4_decisions_pretruth.sha256"', '"p5_decisions_pretruth.sha256"'),
    ('"p4_decisions_pretruth.json.gz"', '"p5_decisions_pretruth.json.gz"'),
)

GATE_ANCHOR = '''        "p4_every_surviving_proposal_inside_two_view_seed_envelope": all(
            float(p["d_obs"]) <= float(p["obs_ceiling"]) and float(p["d_orb"]) <= float(p["orb_ceiling"])
            for ps in proposals_by_event.values() for p in ps
        ),
        "expansion_nonvacuous": len(assignments) > 0,
'''
GATE_REPL = '''        "p4_every_surviving_proposal_inside_two_view_seed_envelope": all(
            float(p["d_obs"]) <= float(p["obs_ceiling"]) and float(p["d_orb"]) <= float(p["orb_ceiling"])
            for ps in proposals_by_event.values() for p in ps
        ),
        "p5_joint_seed_support_frozen_before_truth": len(crossfit_sha) == 64 and all(len(r.get("joint_seed_support", [])) >= 1 for r in reliability.values()),
        "p5_heldout_seeds_supported_by_frontier": all(len(r.get("joint_seed_support", [])) >= 1 for r in reliability.values()),
        "p5_every_surviving_proposal_jointly_supported_by_one_heldout_seed": all(
            any(
                float(p["d_obs"]) <= float(s[0]) and float(p["d_orb"]) <= float(s[1])
                for s in reliability[f"{p['family_id']}|{p['source_year']}|{p['target_year']}"]["joint_seed_support"]
            )
            for ps in proposals_by_event.values() for p in ps
        ),
        "expansion_nonvacuous": len(assignments) > 0,
'''

VERDICT_ANCHOR = '''    verdict = (
        "PASS_DUAL_VIEW_SEED_ENVELOPE_MEMBERSHIP_P4_DEVELOPMENT"
        if all(gates.values())
        else "FAIL_DUAL_VIEW_SEED_ENVELOPE_MEMBERSHIP_P4_NO_GO"
    )
'''
VERDICT_REPL = '''    verdict = (
        "PASS_JOINT_SEED_SUPPORT_MEMBERSHIP_P5_DEVELOPMENT"
        if all(gates.values())
        else "FAIL_JOINT_SEED_SUPPORT_MEMBERSHIP_P5_NO_GO"
    )
'''

CLASS_ANCHOR = '''        "classification": "P3 cross-fitted seed-floor membership plus coordinate-wise held-out two-view recurrent-seed envelope; immutable promoted-v8 cores and rank",
'''
CLASS_REPL = '''        "classification": "P4 coordinate envelope plus parameter-free joint support by one actual held-out recurrent seed in both two-view distances; immutable promoted-v8 cores and rank",
'''

CONFIG_ANCHOR = '''            "p4_parameter_search": False,
        },
'''
CONFIG_REPL = '''            "p4_parameter_search": False,
            "p5_joint_seed_support": "candidate [d_obs,d_orb] must be <= at least one Pareto-maximal held-out recurrent-seed vector componentwise",
            "p5_quantile_multiplier_or_offset": None,
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

DIAG_ANCHOR = '''            "p4_envelope_rejected_above_seed_floor": p4_envelope_rejected_above_seed_floor,
'''
DIAG_REPL = '''            "p4_envelope_rejected_above_seed_floor": p4_envelope_rejected_above_seed_floor,
            "p5_joint_support_rejected_inside_p4": p5_joint_support_rejected_inside_p4,
            "p5_joint_support_vectors_total": sum(len(r.get("joint_seed_support", [])) for r in reliability.values()),
'''

JSON_ANCHOR = '''    (args.output / "dual_view_seed_envelope_membership_p4_development.json").write_text(json.dumps(result, indent=2) + "\\n")
'''
JSON_REPL = '''    (args.output / "joint_seed_support_membership_p5_development.json").write_text(json.dumps(result, indent=2) + "\\n")
'''
MD_ANCHOR = '''    (args.output / "DUAL_VIEW_SEED_ENVELOPE_MEMBERSHIP_P4_DEVELOPMENT.md").write_text(
'''
MD_REPL = '''    (args.output / "JOINT_SEED_SUPPORT_MEMBERSHIP_P5_DEVELOPMENT.md").write_text(
'''
TITLE_ANCHOR = '''        "# OrbitTrace P4 dual-view held-out seed-envelope membership development\\n\\n"
'''
TITLE_REPL = '''        "# OrbitTrace P5 joint held-out-seed support membership development\\n\\n"
'''
SUMMARY_ANCHOR = '''f"- v8 -> P4 macro F1: **{baseline_full['macro_f1']:.6f} -> {p2_full['macro_f1']:.6f}**\\n"'''
SUMMARY_REPL = '''f"- v8 -> P5 macro F1: **{baseline_full['macro_f1']:.6f} -> {p2_full['macro_f1']:.6f}**\\n"'''
QUALIFIED_ANCHOR = '''f"- v8 -> P2 qualified: **{baseline_full['qualified_matches']} -> {p2_full['qualified_matches']}**\\n"'''
QUALIFIED_REPL = '''f"- v8 -> P5 qualified: **{baseline_full['qualified_matches']} -> {p2_full['qualified_matches']}**\\n"'''
RECOVERY_ANCHOR = '''f"- v8 -> P2 recovery@100: **{baseline_full['recovered_at_100']} -> {p2_full['recovered_at_100']}**\\n"'''
RECOVERY_REPL = '''f"- v8 -> P5 recovery@100: **{baseline_full['recovered_at_100']} -> {p2_full['recovered_at_100']}**\\n"'''
PRECISION_ANCHOR = '''f"- v8 -> P2 top100 precision: **{baseline_full['top100_dominant_precision']:.6f} -> {p2_full['top100_dominant_precision']:.6f}**\\n"'''
PRECISION_REPL = '''f"- v8 -> P5 top100 precision: **{baseline_full['top100_dominant_precision']:.6f} -> {p2_full['top100_dominant_precision']:.6f}**\\n"'''
PRINT_ANCHOR = '''    print((args.output / "DUAL_VIEW_SEED_ENVELOPE_MEMBERSHIP_P4_DEVELOPMENT.md").read_text(), flush=True)
'''
PRINT_REPL = '''    print((args.output / "JOINT_SEED_SUPPORT_MEMBERSHIP_P5_DEVELOPMENT.md").read_text(), flush=True)
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
        (SUPPORT_ANCHOR, SUPPORT_REPL, "joint held-out seed support frontier"),
        (RECORD_ANCHOR, RECORD_REPL, "joint support reliability record"),
        (PAYLOAD_ANCHOR, PAYLOAD_REPL, "joint support crossfit declaration"),
        (SCORING_INIT_ANCHOR, SCORING_INIT_REPL, "P5 rejection diagnostic"),
        (SCORING_GATE_ANCHOR, SCORING_GATE_REPL, "candidate joint seed-support gate"),
        (GATE_ANCHOR, GATE_REPL, "P5 integrity gates"),
        (VERDICT_ANCHOR, VERDICT_REPL, "P5 verdict"),
        (CLASS_ANCHOR, CLASS_REPL, "P5 classification"),
        (CONFIG_ANCHOR, CONFIG_REPL, "P5 configuration"),
        (METHOD_KEY_ANCHOR, METHOD_KEY_REPL, "P5 result method key"),
        (LARGE_KEY_ANCHOR, LARGE_KEY_REPL, "P5 large-shower key"),
        (DIAG_ANCHOR, DIAG_REPL, "P5 diagnostics"),
        (JSON_ANCHOR, JSON_REPL, "P5 JSON filename"),
        (MD_ANCHOR, MD_REPL, "P5 markdown filename"),
        (TITLE_ANCHOR, TITLE_REPL, "P5 title"),
        (SUMMARY_ANCHOR, SUMMARY_REPL, "P5 summary label"),
        (QUALIFIED_ANCHOR, QUALIFIED_REPL, "P5 qualified summary label"),
        (RECOVERY_ANCHOR, RECOVERY_REPL, "P5 recovery summary label"),
        (PRECISION_ANCHOR, PRECISION_REPL, "P5 precision summary label"),
        (PRINT_ANCHOR, PRINT_REPL, "P5 print filename"),
    ):
        text = replace_once(text, before, after, label)
    for before, after in MEMBERSHIP_NAMES:
        text = replace_once(text, before, after, f"membership output rename {before}")
    if "OrbitTrace-April" in text or "target_coordinate" in text:
        raise RuntimeError("forbidden target-specific token introduced")
    output.write_text(text, encoding="utf-8")
    print(f"P5_INPUT_P4_SHA256={EXPECTED_P4_SHA256}")
    print(f"P5_OUTPUT_SHA256={digest(text.encode('utf-8'))}")
    print("P5_PATCH_SCOPE=exact P4 plus joint support by one actual held-out recurrent-seed two-view vector; no threshold search or relaxation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
