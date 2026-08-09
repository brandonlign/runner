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
        raise RuntimeError(f"P6 patch anchor {label} count={count}")
    return text.replace(before, after, 1)


RUNTIME_INIT_ANCHOR = '''    crossfit_models: list[dict[str, Any]] = []
    reliability: dict[str, dict[str, Any]] = {}
'''
RUNTIME_INIT_REPL = '''    crossfit_models: list[dict[str, Any]] = []
    crossfit_runtime_models: dict[int, tuple[Any, Any]] = {}
    reliability: dict[str, dict[str, Any]] = {}
'''

RUNTIME_STORE_ANCHOR = '''        require(int(np.max(clf.n_iter_)) < LOGISTIC_MAX_ITER, f"P3 cross-fit solver hit max_iter fold {held_fold}")
        crossfit_models.append({
'''
RUNTIME_STORE_REPL = '''        require(int(np.max(clf.n_iter_)) < LOGISTIC_MAX_ITER, f"P3 cross-fit solver hit max_iter fold {held_fold}")
        require(held_fold not in crossfit_runtime_models, f"P6 duplicate runtime fold model {held_fold}")
        crossfit_runtime_models[held_fold] = (scf, clf)
        crossfit_models.append({
'''

PAYLOAD_ANCHOR = '''        "p5_support_tuning": False,
        "no_known_shower_truth_used": True,
'''
PAYLOAD_REPL = '''        "p5_support_tuning": False,
        "p6_candidate_scoring": "same family-excluded held-fold scaler/logistic model that sets this direction's held-out-seed floor",
        "p6_probability_scale_tuning": False,
        "no_known_shower_truth_used": True,
'''

SCORING_ANCHOR = '''        probabilities = classifier.predict_proba(scaler.transform(features))[:, 1]
        probabilities = np.clip(probabilities, eps, 1.0 - eps)
        key = f"{direction['family_id']}|{direction['source_year']}|{direction['target_year']}"
        gate = reliability[key]
'''
SCORING_REPL = '''        key = f"{direction['family_id']}|{direction['source_year']}|{direction['target_year']}"
        gate = reliability[key]
        scoring_fold = int(gate["fold"])
        require(scoring_fold in crossfit_runtime_models, f"P6 missing runtime fold model {scoring_fold}")
        scoring_scaler, scoring_classifier = crossfit_runtime_models[scoring_fold]
        probabilities = scoring_classifier.predict_proba(scoring_scaler.transform(features))[:, 1]
        probabilities = np.clip(probabilities, eps, 1.0 - eps)
'''

PROPOSAL_ANCHOR = '''                "seed_floor": float(gate["seed_floor"]),
                "d_obs": float(feature_row[0]),
'''
PROPOSAL_REPL = '''                "seed_floor": float(gate["seed_floor"]),
                "scoring_fold": scoring_fold,
                "d_obs": float(feature_row[0]),
'''

MEMBERSHIP_NAMES = (
    ('"p5_membership_pretruth.sha256"', '"p6_membership_pretruth.sha256"'),
    ('"p5_expanded_families.json.gz"', '"p6_expanded_families.json.gz"'),
    ('"p5_decisions_pretruth.sha256"', '"p6_decisions_pretruth.sha256"'),
    ('"p5_decisions_pretruth.json.gz"', '"p6_decisions_pretruth.json.gz"'),
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
        "p6_all_five_runtime_crossfit_models_present": set(crossfit_runtime_models) == set(range(P3_FOLD_COUNT)),
        "p6_same_crossfit_model_sets_floor_and_scores_candidate": all(
            int(p["scoring_fold"]) == int(reliability[f"{p['family_id']}|{p['source_year']}|{p['target_year']}"]["fold"])
            for ps in proposals_by_event.values() for p in ps
        ),
        "p6_final_all_family_model_not_used_for_proposal_scoring": all("scoring_fold" in p for ps in proposals_by_event.values() for p in ps),
        "expansion_nonvacuous": len(assignments) > 0,
'''

VERDICT_ANCHOR = '''    verdict = (
        "PASS_JOINT_SEED_SUPPORT_MEMBERSHIP_P5_DEVELOPMENT"
        if all(gates.values())
        else "FAIL_JOINT_SEED_SUPPORT_MEMBERSHIP_P5_NO_GO"
    )
'''
VERDICT_REPL = '''    verdict = (
        "PASS_SAME_MODEL_CROSSFIT_MEMBERSHIP_P6_DEVELOPMENT"
        if all(gates.values())
        else "FAIL_SAME_MODEL_CROSSFIT_MEMBERSHIP_P6_NO_GO"
    )
'''

CLASS_ANCHOR = '''        "classification": "P4 coordinate envelope plus parameter-free joint support by one actual held-out recurrent seed in both two-view distances; immutable promoted-v8 cores and rank",
'''
CLASS_REPL = '''        "classification": "P5 joint held-out-seed geometry with direction candidates scored on the identical family-excluded cross-fit model that defines their seed floor; immutable promoted-v8 cores and rank",
'''

CONFIG_ANCHOR = '''            "p5_parameter_search": False,
        },
'''
CONFIG_REPL = '''            "p5_parameter_search": False,
            "p6_candidate_scoring_model": "same held-fold cross-fit model that sets direction seed_floor",
            "p6_final_all_family_model_used_for_decisions": False,
            "p6_parameter_search": False,
        },
'''

METHOD_KEY_ANCHOR = '''        "p5": {k: v for k, v in p2_full.items() if k != "per_label"},
'''
METHOD_KEY_REPL = '''        "p6": {k: v for k, v in p2_full.items() if k != "per_label"},
'''
LARGE_KEY_ANCHOR = '''        "p5_large_shower": p2_large,
'''
LARGE_KEY_REPL = '''        "p6_large_shower": p2_large,
'''

DIAG_ANCHOR = '''            "p5_joint_support_vectors_total": sum(len(r.get("joint_seed_support", [])) for r in reliability.values()),
'''
DIAG_REPL = '''            "p5_joint_support_vectors_total": sum(len(r.get("joint_seed_support", [])) for r in reliability.values()),
            "p6_candidate_scoring_runtime_folds": sorted(crossfit_runtime_models),
            "p6_candidate_scoring_uses_final_all_family_model": False,
'''

JSON_ANCHOR = '''    (args.output / "joint_seed_support_membership_p5_development.json").write_text(json.dumps(result, indent=2) + "\\n")
'''
JSON_REPL = '''    (args.output / "same_model_crossfit_membership_p6_development.json").write_text(json.dumps(result, indent=2) + "\\n")
'''
MD_ANCHOR = '''    (args.output / "JOINT_SEED_SUPPORT_MEMBERSHIP_P5_DEVELOPMENT.md").write_text(
'''
MD_REPL = '''    (args.output / "SAME_MODEL_CROSSFIT_MEMBERSHIP_P6_DEVELOPMENT.md").write_text(
'''
TITLE_ANCHOR = '''        "# OrbitTrace P5 joint held-out-seed support membership development\\n\\n"
'''
TITLE_REPL = '''        "# OrbitTrace P6 same-model cross-fit membership development\\n\\n"
'''
SUMMARY_ANCHOR = '''f"- v8 -> P5 macro F1: **{baseline_full['macro_f1']:.6f} -> {p2_full['macro_f1']:.6f}**\\n"'''
SUMMARY_REPL = '''f"- v8 -> P6 macro F1: **{baseline_full['macro_f1']:.6f} -> {p2_full['macro_f1']:.6f}**\\n"'''
QUALIFIED_ANCHOR = '''f"- v8 -> P5 qualified: **{baseline_full['qualified_matches']} -> {p2_full['qualified_matches']}**\\n"'''
QUALIFIED_REPL = '''f"- v8 -> P6 qualified: **{baseline_full['qualified_matches']} -> {p2_full['qualified_matches']}**\\n"'''
RECOVERY_ANCHOR = '''f"- v8 -> P5 recovery@100: **{baseline_full['recovered_at_100']} -> {p2_full['recovered_at_100']}**\\n"'''
RECOVERY_REPL = '''f"- v8 -> P6 recovery@100: **{baseline_full['recovered_at_100']} -> {p2_full['recovered_at_100']}**\\n"'''
PRECISION_ANCHOR = '''f"- v8 -> P5 top100 precision: **{baseline_full['top100_dominant_precision']:.6f} -> {p2_full['top100_dominant_precision']:.6f}**\\n"'''
PRECISION_REPL = '''f"- v8 -> P6 top100 precision: **{baseline_full['top100_dominant_precision']:.6f} -> {p2_full['top100_dominant_precision']:.6f}**\\n"'''
PRINT_ANCHOR = '''    print((args.output / "JOINT_SEED_SUPPORT_MEMBERSHIP_P5_DEVELOPMENT.md").read_text(), flush=True)
'''
PRINT_REPL = '''    print((args.output / "SAME_MODEL_CROSSFIT_MEMBERSHIP_P6_DEVELOPMENT.md").read_text(), flush=True)
'''


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply_p6_patch.py EXACT_P5 OUTPUT")
    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    raw = source.read_bytes()
    actual = digest(raw)
    if actual != EXPECTED_P5_SHA256:
        raise RuntimeError(f"exact P5 source SHA changed: {actual}")
    text = raw.decode("utf-8")
    for before, after, label in (
        (RUNTIME_INIT_ANCHOR, RUNTIME_INIT_REPL, "crossfit runtime model registry"),
        (RUNTIME_STORE_ANCHOR, RUNTIME_STORE_REPL, "crossfit runtime model retention"),
        (PAYLOAD_ANCHOR, PAYLOAD_REPL, "same-model crossfit declaration"),
        (SCORING_ANCHOR, SCORING_REPL, "same-model candidate scoring"),
        (PROPOSAL_ANCHOR, PROPOSAL_REPL, "proposal scoring fold record"),
        (GATE_ANCHOR, GATE_REPL, "P6 integrity gates"),
        (VERDICT_ANCHOR, VERDICT_REPL, "P6 verdict"),
        (CLASS_ANCHOR, CLASS_REPL, "P6 classification"),
        (CONFIG_ANCHOR, CONFIG_REPL, "P6 configuration"),
        (METHOD_KEY_ANCHOR, METHOD_KEY_REPL, "P6 result method key"),
        (LARGE_KEY_ANCHOR, LARGE_KEY_REPL, "P6 large-shower key"),
        (DIAG_ANCHOR, DIAG_REPL, "P6 diagnostics"),
        (JSON_ANCHOR, JSON_REPL, "P6 JSON filename"),
        (MD_ANCHOR, MD_REPL, "P6 markdown filename"),
        (TITLE_ANCHOR, TITLE_REPL, "P6 title"),
        (SUMMARY_ANCHOR, SUMMARY_REPL, "P6 summary label"),
        (QUALIFIED_ANCHOR, QUALIFIED_REPL, "P6 qualified summary label"),
        (RECOVERY_ANCHOR, RECOVERY_REPL, "P6 recovery summary label"),
        (PRECISION_ANCHOR, PRECISION_REPL, "P6 precision summary label"),
        (PRINT_ANCHOR, PRINT_REPL, "P6 print filename"),
    ):
        text = replace_once(text, before, after, label)
    for before, after in MEMBERSHIP_NAMES:
        text = replace_once(text, before, after, f"membership output rename {before}")
    if "OrbitTrace-April" in text or "target_coordinate" in text:
        raise RuntimeError("forbidden target-specific token introduced")
    output.write_text(text, encoding="utf-8")
    print(f"P6_INPUT_P5_SHA256={EXPECTED_P5_SHA256}")
    print(f"P6_OUTPUT_SHA256={digest(text.encode('utf-8'))}")
    print("P6_PATCH_SCOPE=exact P5 plus same held-fold crossfit model for each direction's candidate scoring and seed-floor calibration; no threshold search")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
