#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

EXPECTED_P5_SHA256 = "b48b3e6a45a7a371eb8e73c70ee217a33a96c596c61b51ebb7dc9c7b60100456"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def replace_once(text: str, before: str, after: str, label: str) -> str:
    count = text.count(before)
    if count != 1:
        raise RuntimeError(f"P8 patch anchor {label} count={count}")
    return text.replace(before, after, 1)


RUNTIME_DECL_ANCHOR = '''    crossfit_models: list[dict[str, Any]] = []
    reliability: dict[str, dict[str, Any]] = {}
'''
RUNTIME_DECL_REPL = '''    crossfit_models: list[dict[str, Any]] = []
    crossfit_runtime: dict[int, tuple[Any, Any]] = {}
    reliability: dict[str, dict[str, Any]] = {}
'''

RUNTIME_STORE_ANCHOR = '''        })
        for d in held_dirs:
'''
RUNTIME_STORE_REPL = '''        })
        require(held_fold not in crossfit_runtime, f"P8 duplicate runtime fold {held_fold}")
        crossfit_runtime[held_fold] = (scf, clf)
        for d in held_dirs:
'''

RUNTIME_COMPLETE_ANCHOR = '''    require(len(reliability) == len(directions), "P3 reliability direction universe changed")
'''
RUNTIME_COMPLETE_REPL = '''    require(len(crossfit_runtime) == P3_FOLD_COUNT and set(crossfit_runtime) == set(range(P3_FOLD_COUNT)), "P8 crossfit runtime fold universe changed")
    require(len(reliability) == len(directions), "P3 reliability direction universe changed")
'''

CROSSFIT_PAYLOAD_ANCHOR = '''        "p5_support_tuning": False,
        "no_known_shower_truth_used": True,
'''
CROSSFIT_PAYLOAD_REPL = '''        "p5_support_tuning": False,
        "p8_candidate_scoring": "family-excluded fold model identical to the model that generated the family-direction held-out seed floor",
        "p8_all_family_model_membership_role": "reference-only; zero candidate probabilities, odds, or responsibility contributions",
        "p8_parameter_search": False,
        "no_known_shower_truth_used": True,
'''

SCORING_INIT_ANCHOR = '''    p5_joint_support_rejected_inside_p4 = 0
'''
SCORING_INIT_REPL = '''    p5_joint_support_rejected_inside_p4 = 0
    p8_fold_scored_directions = 0
    p8_fold_scored_candidate_rows = 0
    p8_all_family_scored_candidate_rows = 0
'''

SCORING_MODEL_ANCHOR = '''        probabilities = classifier.predict_proba(scaler.transform(features))[:, 1]
        probabilities = np.clip(probabilities, eps, 1.0 - eps)
        key = f"{direction['family_id']}|{direction['source_year']}|{direction['target_year']}"
        gate = reliability[key]
'''
SCORING_MODEL_REPL = '''        family_id = str(direction["family_id"])
        key = f"{family_id}|{direction['source_year']}|{direction['target_year']}"
        gate = reliability[key]
        score_fold = int(family_fold[family_id])
        require(score_fold == int(gate["fold"]), f"P8 scoring/reliability fold mismatch {key}")
        require(score_fold in crossfit_runtime, f"P8 missing runtime model fold {score_fold}")
        score_scaler, score_classifier = crossfit_runtime[score_fold]
        probabilities = score_classifier.predict_proba(score_scaler.transform(features))[:, 1]
        probabilities = np.clip(probabilities, eps, 1.0 - eps)
        p8_fold_scored_directions += 1
        p8_fold_scored_candidate_rows += int(len(features))
'''

PROPOSAL_RECORD_ANCHOR = '''                "orb_ceiling": float(feature_ceiling[1]),
            })
'''
PROPOSAL_RECORD_REPL = '''                "orb_ceiling": float(feature_ceiling[1]),
                "score_model_fold": int(score_fold),
                "score_model_scope": "family-excluded-crossfit",
            })
'''

MEMBERSHIP_NAMES = (
    ('"p5_membership_pretruth.sha256"', '"p8_membership_pretruth.sha256"'),
    ('"p5_expanded_families.json.gz"', '"p8_expanded_families.json.gz"'),
    ('"p5_decisions_pretruth.sha256"', '"p8_decisions_pretruth.sha256"'),
    ('"p5_decisions_pretruth.json.gz"', '"p8_decisions_pretruth.json.gz"'),
)

GATE_ANCHOR = '''        "p5_every_surviving_proposal_jointly_supported_by_one_heldout_seed": all(
            any(
                float(p["d_obs"]) <= float(s[0]) and float(p["d_orb"]) <= float(s[1])
                for s in reliability[f"{p['family_id']}|{p['source_year']}|{p['target_year']}"]["joint_seed_support"]
            )
            for ps in proposals_by_event.values() for p in ps
        ),
        "expansion_nonvacuous": len(assignments) > 0,
'''
GATE_REPL = '''        "p5_every_surviving_proposal_jointly_supported_by_one_heldout_seed": all(
            any(
                float(p["d_obs"]) <= float(s[0]) and float(p["d_orb"]) <= float(s[1])
                for s in reliability[f"{p['family_id']}|{p['source_year']}|{p['target_year']}"]["joint_seed_support"]
            )
            for ps in proposals_by_event.values() for p in ps
        ),
        "p8_all_five_runtime_fold_models_present": len(crossfit_runtime) == P3_FOLD_COUNT and set(crossfit_runtime) == set(range(P3_FOLD_COUNT)),
        "p8_runtime_models_match_serialized_crossfit_models": all(
            np.array_equal(np.asarray(crossfit_runtime[int(m["held_fold"])][0].mean_, dtype=np.float64), np.asarray(m["scaler_mean"], dtype=np.float64))
            and np.array_equal(np.asarray(crossfit_runtime[int(m["held_fold"])][0].scale_, dtype=np.float64), np.asarray(m["scaler_scale"], dtype=np.float64))
            and np.array_equal(np.asarray(crossfit_runtime[int(m["held_fold"])][1].coef_, dtype=np.float64), np.asarray(m["logistic_coef"], dtype=np.float64))
            and np.array_equal(np.asarray(crossfit_runtime[int(m["held_fold"])][1].intercept_, dtype=np.float64), np.asarray(m["logistic_intercept"], dtype=np.float64))
            for m in crossfit_models
        ),
        "p8_every_proposal_scored_by_own_family_excluded_fold": all(
            str(p.get("score_model_scope")) == "family-excluded-crossfit"
            and int(p["score_model_fold"]) == int(family_fold[str(p["family_id"])])
            and int(p["score_model_fold"]) == int(reliability[f"{p['family_id']}|{p['source_year']}|{p['target_year']}"]["fold"])
            for ps in proposals_by_event.values() for p in ps
        ),
        "p8_every_surviving_proposal_meets_same_fold_seed_floor": all(
            float(p["probability"]) >= float(reliability[f"{p['family_id']}|{p['source_year']}|{p['target_year']}"]["seed_floor"])
            for ps in proposals_by_event.values() for p in ps
        ),
        "p8_all_family_model_zero_membership_scores": p8_all_family_scored_candidate_rows == 0,
        "expansion_nonvacuous": len(assignments) > 0,
'''

VERDICT_ANCHOR = '''    verdict = (
        "PASS_JOINT_SEED_SUPPORT_MEMBERSHIP_P5_DEVELOPMENT"
        if all(gates.values())
        else "FAIL_JOINT_SEED_SUPPORT_MEMBERSHIP_P5_NO_GO"
    )
'''
VERDICT_REPL = '''    verdict = (
        "PASS_CONSISTENT_CROSSFIT_SCORING_P8_DEVELOPMENT"
        if all(gates.values())
        else "FAIL_CONSISTENT_CROSSFIT_SCORING_P8_NO_GO"
    )
'''

CLASS_ANCHOR = '''        "classification": "P4 coordinate envelope plus parameter-free joint support by one actual held-out recurrent seed in both two-view distances; immutable promoted-v8 cores and rank",
'''
CLASS_REPL = '''        "classification": "exact P5 geometry/reliability with family-excluded crossfit model used consistently for candidate probability, odds and conflict responsibility; immutable promoted-v8 cores and rank",
'''

CONFIG_ANCHOR = '''            "p5_parameter_search": False,
        },
'''
CONFIG_REPL = '''            "p5_parameter_search": False,
            "p8_candidate_probability_model": "the deterministic family-excluded fold model that generated the family-direction seed floor",
            "p8_candidate_odds_model": "same family-excluded fold probability p transformed as p/(1-p)",
            "p8_all_family_model_role": "reference-only; retained for exact P2 provenance but not P8 membership scoring",
            "p8_parameter_search": False,
        },
'''

METHOD_KEY_ANCHOR = '''        "p5": {k: v for k, v in p2_full.items() if k != "per_label"},
'''
METHOD_KEY_REPL = '''        "p8": {k: v for k, v in p2_full.items() if k != "per_label"},
'''
LARGE_KEY_ANCHOR = '''        "p5_large_shower": p2_large,
'''
LARGE_KEY_REPL = '''        "p8_large_shower": p2_large,
'''

DIAG_ANCHOR = '''            "p5_joint_support_vectors_total": sum(len(r.get("joint_seed_support", [])) for r in reliability.values()),
'''
DIAG_REPL = '''            "p5_joint_support_vectors_total": sum(len(r.get("joint_seed_support", [])) for r in reliability.values()),
            "p8_fold_scored_directions": p8_fold_scored_directions,
            "p8_fold_scored_candidate_rows": p8_fold_scored_candidate_rows,
            "p8_all_family_scored_candidate_rows": p8_all_family_scored_candidate_rows,
'''

JSON_ANCHOR = '''    (args.output / "joint_seed_support_membership_p5_development.json").write_text(json.dumps(result, indent=2) + "\\n")
'''
JSON_REPL = '''    (args.output / "consistent_crossfit_scoring_p8_development.json").write_text(json.dumps(result, indent=2) + "\\n")
'''
MD_ANCHOR = '''    (args.output / "JOINT_SEED_SUPPORT_MEMBERSHIP_P5_DEVELOPMENT.md").write_text(
'''
MD_REPL = '''    (args.output / "CONSISTENT_CROSSFIT_SCORING_P8_DEVELOPMENT.md").write_text(
'''
TITLE_ANCHOR = '''        "# OrbitTrace P5 joint held-out-seed support membership development\\n\\n"
'''
TITLE_REPL = '''        "# OrbitTrace P8 consistent family-excluded crossfit scoring development\\n\\n"
'''
SUMMARY_ANCHOR = '''f"- v8 -> P5 macro F1: **{baseline_full['macro_f1']:.6f} -> {p2_full['macro_f1']:.6f}**\\n"'''
SUMMARY_REPL = '''f"- v8 -> P8 macro F1: **{baseline_full['macro_f1']:.6f} -> {p2_full['macro_f1']:.6f}**\\n"'''
QUALIFIED_ANCHOR = '''f"- v8 -> P5 qualified: **{baseline_full['qualified_matches']} -> {p2_full['qualified_matches']}**\\n"'''
QUALIFIED_REPL = '''f"- v8 -> P8 qualified: **{baseline_full['qualified_matches']} -> {p2_full['qualified_matches']}**\\n"'''
RECOVERY_ANCHOR = '''f"- v8 -> P5 recovery@100: **{baseline_full['recovered_at_100']} -> {p2_full['recovered_at_100']}**\\n"'''
RECOVERY_REPL = '''f"- v8 -> P8 recovery@100: **{baseline_full['recovered_at_100']} -> {p2_full['recovered_at_100']}**\\n"'''
PRECISION_ANCHOR = '''f"- v8 -> P5 top100 precision: **{baseline_full['top100_dominant_precision']:.6f} -> {p2_full['top100_dominant_precision']:.6f}**\\n"'''
PRECISION_REPL = '''f"- v8 -> P8 top100 precision: **{baseline_full['top100_dominant_precision']:.6f} -> {p2_full['top100_dominant_precision']:.6f}**\\n"'''
PRINT_ANCHOR = '''    print((args.output / "JOINT_SEED_SUPPORT_MEMBERSHIP_P5_DEVELOPMENT.md").read_text(), flush=True)
'''
PRINT_REPL = '''    print((args.output / "CONSISTENT_CROSSFIT_SCORING_P8_DEVELOPMENT.md").read_text(), flush=True)
'''


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply_p8_patch.py EXACT_P5 OUTPUT")
    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    raw = source.read_bytes()
    actual = digest(raw)
    if actual != EXPECTED_P5_SHA256:
        raise RuntimeError(f"exact P5 source SHA changed: {actual}")
    text = raw.decode("utf-8")
    for before, after, label in (
        (RUNTIME_DECL_ANCHOR, RUNTIME_DECL_REPL, "crossfit runtime declaration"),
        (RUNTIME_STORE_ANCHOR, RUNTIME_STORE_REPL, "crossfit runtime model retention"),
        (RUNTIME_COMPLETE_ANCHOR, RUNTIME_COMPLETE_REPL, "runtime fold completeness"),
        (CROSSFIT_PAYLOAD_ANCHOR, CROSSFIT_PAYLOAD_REPL, "P8 scoring declaration"),
        (SCORING_INIT_ANCHOR, SCORING_INIT_REPL, "P8 scoring diagnostics"),
        (SCORING_MODEL_ANCHOR, SCORING_MODEL_REPL, "family-excluded candidate scoring"),
        (PROPOSAL_RECORD_ANCHOR, PROPOSAL_RECORD_REPL, "proposal scoring-fold provenance"),
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
    if 'classifier.predict_proba(scaler.transform(features))' in text:
        raise RuntimeError('P8 all-family classifier still scores membership candidates')
    if "OrbitTrace-April" in text or "target_coordinate" in text:
        raise RuntimeError("forbidden target-specific token introduced")
    output.write_text(text, encoding="utf-8")
    print(f"P8_INPUT_P5_SHA256={EXPECTED_P5_SHA256}")
    print(f"P8_OUTPUT_SHA256={digest(text.encode('utf-8'))}")
    print("P8_PATCH_SCOPE=exact P5 except candidate probabilities/odds use the same family-excluded fold model that generated each direction seed floor; no threshold or filter change")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
