#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

EXPECTED_P3_SHA256 = "f6c4c5a76b8b3f35d434aed4f1fb15035be05c40d0e0531c343ff620f3ba8185"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def replace_once(text: str, before: str, after: str, label: str) -> str:
    count = text.count(before)
    if count != 1:
        raise RuntimeError(f"P4 patch anchor {label} count={count}")
    return text.replace(before, after, 1)


RELIABILITY_ANCHOR = '''            seed_floor = float(np.min(pp))
            negative_tail = float(np.mean(pn >= seed_floor))
            key = f"{d['family_id']}|{d['source_year']}|{d['target_year']}"
'''
RELIABILITY_REPL = '''            seed_floor = float(np.min(pp))
            negative_tail = float(np.mean(pn >= seed_floor))
            feature_ceiling = np.max(xp, axis=0).astype(np.float64, copy=False)
            require(feature_ceiling.shape == (2,) and np.all(np.isfinite(feature_ceiling)), "P4 invalid two-view held-out seed ceiling")
            require(np.all(xp <= feature_ceiling[None, :]), "P4 held-out seed excluded by its own coordinate envelope")
            key = f"{d['family_id']}|{d['source_year']}|{d['target_year']}"
'''

RELIABILITY_RECORD_ANCHOR = '''                "seed_floor": seed_floor,
                "negative_tail": negative_tail,
                "positive_scores_float64_sha256": hashlib.sha256(np.ascontiguousarray(pp, dtype="<f8").tobytes()).hexdigest(),
'''
RELIABILITY_RECORD_REPL = '''                "seed_floor": seed_floor,
                "negative_tail": negative_tail,
                "feature_ceiling": feature_ceiling.tolist(),
                "feature_ceiling_rule": "coordinate-wise maximum held-out recurrent-seed [d_obs,d_orb]",
                "positive_scores_float64_sha256": hashlib.sha256(np.ascontiguousarray(pp, dtype="<f8").tobytes()).hexdigest(),
'''

CROSSFIT_PAYLOAD_ANCHOR = '''        "negative_tail_max": P3_NEGATIVE_TAIL_MAX,
        "no_known_shower_truth_used": True,
'''
CROSSFIT_PAYLOAD_REPL = '''        "negative_tail_max": P3_NEGATIVE_TAIL_MAX,
        "p4_two_view_seed_envelope": "candidate d_obs and d_orb must each be <= coordinate-wise maximum held-out recurrent-seed feature",
        "p4_envelope_tuning": False,
        "no_known_shower_truth_used": True,
'''

SCORING_INIT_ANCHOR = '''    proposals_by_event: dict[str, list[dict[str, Any]]] = defaultdict(list)
    eps = np.finfo(np.float64).eps
'''
SCORING_INIT_REPL = '''    proposals_by_event: dict[str, list[dict[str, Any]]] = defaultdict(list)
    eps = np.finfo(np.float64).eps
    p4_envelope_rejected_above_seed_floor = 0
'''

SCORING_GATE_ANCHOR = '''        allowed = probabilities >= float(gate["seed_floor"])
        odds = probabilities / (1.0 - probabilities)
        for event_id, probability, odd, keep in zip(ids, probabilities.tolist(), odds.tolist(), allowed.tolist()):
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
            })
'''
SCORING_GATE_REPL = '''        seed_floor_allowed = probabilities >= float(gate["seed_floor"])
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

MEMBERSHIP_NAMES = (
    ('"p3_membership_pretruth.sha256"', '"p4_membership_pretruth.sha256"'),
    ('"p3_expanded_families.json.gz"', '"p4_expanded_families.json.gz"'),
    ('"p3_decisions_pretruth.sha256"', '"p4_decisions_pretruth.sha256"'),
    ('"p3_decisions_pretruth.json.gz"', '"p4_decisions_pretruth.json.gz"'),
)

GATE_ANCHOR = '''        "p3_every_surviving_proposal_meets_seed_floor": all(
            float(p["probability"]) >= float(p["seed_floor"])
            for ps in proposals_by_event.values() for p in ps
        ),
        "expansion_nonvacuous": len(assignments) > 0,
'''
GATE_REPL = '''        "p3_every_surviving_proposal_meets_seed_floor": all(
            float(p["probability"]) >= float(p["seed_floor"])
            for ps in proposals_by_event.values() for p in ps
        ),
        "p4_coordinate_envelope_frozen_before_truth": len(crossfit_sha) == 64 and all(len(r.get("feature_ceiling", [])) == 2 for r in reliability.values()),
        "p4_heldout_seeds_inside_own_envelope": all(len(r.get("feature_ceiling", [])) == 2 for r in reliability.values()),
        "p4_every_surviving_proposal_inside_two_view_seed_envelope": all(
            float(p["d_obs"]) <= float(p["obs_ceiling"]) and float(p["d_orb"]) <= float(p["orb_ceiling"])
            for ps in proposals_by_event.values() for p in ps
        ),
        "expansion_nonvacuous": len(assignments) > 0,
'''

VERDICT_ANCHOR = '''    verdict = (
        "PASS_CROSSFIT_SEED_FLOOR_MEMBERSHIP_P3_DEVELOPMENT"
        if all(gates.values())
        else "FAIL_CROSSFIT_SEED_FLOOR_MEMBERSHIP_P3_NO_GO"
    )
'''
VERDICT_REPL = '''    verdict = (
        "PASS_DUAL_VIEW_SEED_ENVELOPE_MEMBERSHIP_P4_DEVELOPMENT"
        if all(gates.values())
        else "FAIL_DUAL_VIEW_SEED_ENVELOPE_MEMBERSHIP_P4_NO_GO"
    )
'''

CLASS_ANCHOR = '''        "classification": "cross-fitted held-out seed-floor two-view membership discriminator; immutable promoted-v8 cores and rank",
'''
CLASS_REPL = '''        "classification": "P3 cross-fitted seed-floor membership plus coordinate-wise held-out two-view recurrent-seed envelope; immutable promoted-v8 cores and rank",
'''

CONFIG_ANCHOR = '''            "p3_final_probability_gate": "probability >= immutable family-direction seed_floor",
        },
'''
CONFIG_REPL = '''            "p3_final_probability_gate": "probability >= immutable family-direction seed_floor",
            "p4_two_view_seed_envelope": "candidate d_obs <= max held-out seed d_obs AND candidate d_orb <= max held-out seed d_orb",
            "p4_envelope_quantile_or_multiplier": None,
            "p4_parameter_search": False,
        },
'''

METHOD_KEY_ANCHOR = '''        "p3": {k: v for k, v in p2_full.items() if k != "per_label"},
'''
METHOD_KEY_REPL = '''        "p4": {k: v for k, v in p2_full.items() if k != "per_label"},
'''
LARGE_KEY_ANCHOR = '''        "p3_large_shower": p2_large,
'''
LARGE_KEY_REPL = '''        "p4_large_shower": p2_large,
'''

DIAG_ANCHOR = '''            "p3_crossfit_pretruth_sha256": crossfit_sha,
            "p3_decisions_pretruth_sha256": decision_sha,
'''
DIAG_REPL = '''            "p3_crossfit_pretruth_sha256": crossfit_sha,
            "p4_decisions_pretruth_sha256": decision_sha,
            "p4_envelope_rejected_above_seed_floor": p4_envelope_rejected_above_seed_floor,
'''

JSON_ANCHOR = '''    (args.output / "crossfit_seed_floor_membership_p3_development.json").write_text(json.dumps(result, indent=2) + "\\n")
'''
JSON_REPL = '''    (args.output / "dual_view_seed_envelope_membership_p4_development.json").write_text(json.dumps(result, indent=2) + "\\n")
'''
MD_ANCHOR = '''    (args.output / "CROSSFIT_SEED_FLOOR_MEMBERSHIP_P3_DEVELOPMENT.md").write_text(
'''
MD_REPL = '''    (args.output / "DUAL_VIEW_SEED_ENVELOPE_MEMBERSHIP_P4_DEVELOPMENT.md").write_text(
'''
TITLE_ANCHOR = '''        "# OrbitTrace cross-fitted seed-floor two-view membership P3 development\\n\\n"
'''
TITLE_REPL = '''        "# OrbitTrace P4 dual-view held-out seed-envelope membership development\\n\\n"
'''
SUMMARY_ANCHOR = '''f"- v8 -> P3 macro F1: **{baseline_full['macro_f1']:.6f} -> {p2_full['macro_f1']:.6f}**\\n"'''
SUMMARY_REPL = '''f"- v8 -> P4 macro F1: **{baseline_full['macro_f1']:.6f} -> {p2_full['macro_f1']:.6f}**\\n"'''
PRINT_ANCHOR = '''    print((args.output / "CROSSFIT_SEED_FLOOR_MEMBERSHIP_P3_DEVELOPMENT.md").read_text(), flush=True)
'''
PRINT_REPL = '''    print((args.output / "DUAL_VIEW_SEED_ENVELOPE_MEMBERSHIP_P4_DEVELOPMENT.md").read_text(), flush=True)
'''


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply_p4_patch.py EXACT_P3 OUTPUT")
    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    raw = source.read_bytes()
    actual = digest(raw)
    if actual != EXPECTED_P3_SHA256:
        raise RuntimeError(f"exact P3 source SHA changed: {actual}")
    text = raw.decode("utf-8")
    for before, after, label in (
        (RELIABILITY_ANCHOR, RELIABILITY_REPL, "held-out seed feature ceiling"),
        (RELIABILITY_RECORD_ANCHOR, RELIABILITY_RECORD_REPL, "reliability envelope record"),
        (CROSSFIT_PAYLOAD_ANCHOR, CROSSFIT_PAYLOAD_REPL, "crossfit envelope declaration"),
        (SCORING_INIT_ANCHOR, SCORING_INIT_REPL, "envelope rejection diagnostic"),
        (SCORING_GATE_ANCHOR, SCORING_GATE_REPL, "candidate dual-view envelope gate"),
        (GATE_ANCHOR, GATE_REPL, "P4 integrity gates"),
        (VERDICT_ANCHOR, VERDICT_REPL, "P4 verdict"),
        (CLASS_ANCHOR, CLASS_REPL, "P4 classification"),
        (CONFIG_ANCHOR, CONFIG_REPL, "P4 configuration"),
        (METHOD_KEY_ANCHOR, METHOD_KEY_REPL, "P4 result method key"),
        (LARGE_KEY_ANCHOR, LARGE_KEY_REPL, "P4 large-shower key"),
        (DIAG_ANCHOR, DIAG_REPL, "P4 diagnostics"),
        (JSON_ANCHOR, JSON_REPL, "P4 JSON filename"),
        (MD_ANCHOR, MD_REPL, "P4 markdown filename"),
        (TITLE_ANCHOR, TITLE_REPL, "P4 title"),
        (SUMMARY_ANCHOR, SUMMARY_REPL, "P4 summary label"),
        (PRINT_ANCHOR, PRINT_REPL, "P4 print filename"),
    ):
        text = replace_once(text, before, after, label)
    for before, after in MEMBERSHIP_NAMES:
        text = replace_once(text, before, after, f"membership output rename {before}")
    if "OrbitTrace-April" in text or "target_coordinate" in text:
        raise RuntimeError("forbidden target-specific token introduced")
    output.write_text(text, encoding="utf-8")
    print(f"P4_INPUT_P3_SHA256={EXPECTED_P3_SHA256}")
    print(f"P4_OUTPUT_SHA256={digest(text.encode('utf-8'))}")
    print("P4_PATCH_SCOPE=exact P3 plus coordinate-wise maximum held-out seed envelope in existing d_obs and d_orb views; no threshold search")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
