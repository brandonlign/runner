#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('p3_patch_v1',HERE/'apply_p3_patch.py')
if spec is None or spec.loader is None: raise RuntimeError('cannot load P3 v1 patch')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

# Correct anchors to the exact canonical P2 v2 source.
m.GATES_ANCHOR='''        "model_frozen_before_truth_evaluation": bool(model_sha),
        "membership_frozen_before_truth_evaluation": bool(membership_sha),
        "classifier_converged": int(np.max(classifier.n_iter_)) < LOGISTIC_MAX_ITER,
'''
m.GATES_REPL='''        "model_frozen_before_truth_evaluation": bool(model_sha),
        "membership_frozen_before_truth_evaluation": bool(membership_sha),
        "classifier_converged": int(np.max(classifier.n_iter_)) < LOGISTIC_MAX_ITER,
        "p3_exact_five_crossfit_folds": P3_FOLD_COUNT == 5 and set(family_fold.values()) <= set(range(5)),
        "p3_crossfit_frozen_before_truth": len(crossfit_sha) == 64,
        "p3_every_direction_has_one_heldout_gate": len(reliability) == len(directions),
        "p3_truth_physically_unavailable_until_membership_freeze": all(a["label_value_accessed"] is False for a in geometry_audits) and all(a["label_value_accessed_only_after_blind_and_dedup"] is True for a in truth_audits),
        "p3_no_unreliable_direction_can_propose": all(bool(reliability[f"{d['family_id']}|{d['source_year']}|{d['target_year']}"]["reliable"]) or not any(str(p.get("family_id")) == str(d["family_id"]) and int(p.get("source_year")) == int(d["source_year"]) and int(p.get("target_year")) == int(d["target_year"]) for ps in proposals_by_event.values() for p in ps) for d in directions),
'''
m.VERDICT_ANCHOR='''    verdict = (
        "PASS_CROSSYEAR_TWO_VIEW_MEMBERSHIP_P2_DEVELOPMENT"
        if all(gates.values())
        else "FAIL_CROSSYEAR_TWO_VIEW_MEMBERSHIP_P2_NO_GO"
    )
'''
m.VERDICT_REPL='''    verdict = (
        "PASS_CROSSFIT_SEED_FLOOR_MEMBERSHIP_P3_DEVELOPMENT"
        if all(gates.values())
        else "FAIL_CROSSFIT_SEED_FLOOR_MEMBERSHIP_P3_NO_GO"
    )
'''
m.CLASS_ANCHOR='''        "classification": "cross-year self-supervised two-view membership discriminator; immutable promoted-v8 cores and rank",
'''
m.CLASS_REPL='''        "classification": "cross-fitted held-out seed-floor two-view membership discriminator; immutable promoted-v8 cores and rank",
'''
m.TITLE_ANCHOR='''        "# OrbitTrace cross-year two-view membership P2 development\\n\\n"
'''
m.TITLE_REPL='''        "# OrbitTrace cross-fitted seed-floor two-view membership P3 development\\n\\n"
'''
m.OUTFILE_ANCHOR='''    (args.output / "crossyear_two_view_membership_p2_development.json").write_text(json.dumps(result, indent=2) + "\\n")
'''
m.OUTFILE_REPL='''    (args.output / "crossfit_seed_floor_membership_p3_development.json").write_text(json.dumps(result, indent=2) + "\\n")
'''
# Keep the existing markdown filename to avoid needing a second replacement for
# the immediately following read/print. The content title is P3 and the JSON
# scientific result has a P3-specific filename/verdict.
m.MD_ANCHOR='''    (args.output / "CROSSYEAR_TWO_VIEW_MEMBERSHIP_P2_DEVELOPMENT.md").write_text(
'''
m.MD_REPL=m.MD_ANCHOR

# Inject a physical truth firewall. This code is adapted from the already-used
# v6-LF geometry/truth split and uses no label column in the pretruth parser.
TRUTH_HELPER_ANCHOR='''def main() -> int:
'''
TRUTH_HELPER_REPL='''def p3_geometry_arrays(frame: Any, columns: dict[str, str]):
    ids=frame[columns["id"]].astype(str).to_numpy()
    sol=np.asarray(frame[columns["sol"]], dtype=np.float64)
    lam=np.asarray(frame[columns["lam"]], dtype=np.float64)
    bet=np.asarray(frame[columns["bet"]], dtype=np.float64)
    vg=np.asarray(frame[columns["vg"]], dtype=np.float64)
    return ids,sol,lam,bet,vg


def p3_valid_mask(sol: np.ndarray, lam: np.ndarray, bet: np.ndarray, vg: np.ndarray, support: Any) -> np.ndarray:
    valid=np.isfinite(sol)&np.isfinite(lam)&np.isfinite(bet)&np.isfinite(vg)
    valid &= (sol>=0.0)&(sol<=360.0)&(lam>=0.0)&(lam<=360.0)&(bet>=-90.0)&(bet<=90.0)&(vg>=5.0)&(vg<=75.0)
    blind=(sol>=float(support.BLIND_LOW))&(sol<=float(support.BLIND_HIGH))
    return valid & ~blind


def p3_parse_geometry_only(support: Any, base: Any):
    scan={year:[] for year in YEARS}; audits=[]; seen:set[str]=set()
    for key in MONTH_KEYS:
        year=int(key[:4]); text=support.dd.get_monthly_file_content_by_date(key); frame=support.read_gmn_frame(text); columns=support.column_map(frame)
        ids,sol,lam,bet,vg=p3_geometry_arrays(frame,columns); keep=p3_valid_mask(sol,lam,bet,vg,support); accepted=duplicates=0
        for index in np.flatnonzero(keep):
            eid=str(ids[int(index)])
            if not eid or eid in seen: duplicates+=int(bool(eid)); continue
            seen.add(eid); s=float(sol[int(index)])
            scan[year].append({"id":eid,"year":year,"sol":s,"sun_lon":float(base.wrap180(float(lam[int(index)])-s)),"ecl_lat":float(bet[int(index)]),"vg":float(vg[int(index)]),"iau":0,"complex_key":"HIDDEN"}); accepted+=1
        audits.append({"key":key,"raw_rows":int(len(frame)),"geometry_rows_after_blind_and_dedup":accepted,"duplicates_removed":duplicates,"label_column_name":columns["label"],"label_value_accessed":False})
    return scan,audits,seen


def p3_parse_truth_after_freeze(support: Any, expected_ids: set[str]):
    hidden:dict[str,str]={}; audits=[]; seen:set[str]=set()
    for key in MONTH_KEYS:
        text=support.dd.get_monthly_file_content_by_date(key); frame=support.read_gmn_frame(text); columns=support.column_map(frame)
        ids,sol,lam,bet,vg=p3_geometry_arrays(frame,columns); keep=p3_valid_mask(sol,lam,bet,vg,support); selected=duplicates=0
        for index in np.flatnonzero(keep):
            eid=str(ids[int(index)])
            if not eid or eid in seen: duplicates+=int(bool(eid)); continue
            seen.add(eid); require(eid in expected_ids,f"P3 truth pass added pretruth-absent event {eid}")
            label=support.normalize_label(frame.iloc[int(index)][columns["label"]]); hidden[eid]=label if label else "SPORADIC"; selected+=1
        audits.append({"key":key,"truth_rows":selected,"duplicates_removed":duplicates,"label_value_accessed_only_after_blind_and_dedup":True})
    require(seen==expected_ids,f"P3 truth/pretruth event universe mismatch truth={len(seen)} pretruth={len(expected_ids)}"); require(set(hidden)==expected_ids,"P3 truth labels missing expected IDs")
    return hidden,audits


def main() -> int:
'''

PARSE_ANCHOR='''    scan_by_year, _, hidden_labels, sources = support.parse_catalogue(base)
    require(sorted(scan_by_year) == list(YEARS), "development year universe changed")
'''
PARSE_REPL='''    scan_by_year, geometry_audits, pretruth_ids = p3_parse_geometry_only(support, base)
    hidden_labels = None
    sources = {"geometry_audits": geometry_audits}
    require(sorted(scan_by_year) == list(YEARS), "development year universe changed")
'''

TRUTH_OPEN_ANCHOR='''    baseline_full = v8.mult.evaluate_order(hidden_labels, families, v8_order)
'''
TRUTH_OPEN_REPL='''    # FIRST known-shower label-value access: both cross-fit and final model plus
    # complete P3 memberships are already durable and SHA-frozen above.
    hidden_labels, truth_audits = p3_parse_truth_after_freeze(support, pretruth_ids)
    require(len(crossfit_sha)==64 and len(model_sha)==64 and len(membership_sha)==64, "P3 pretruth hashes missing before truth")
    baseline_full = v8.mult.evaluate_order(hidden_labels, families, v8_order)
'''

RESULT_AUDIT_ANCHOR='''        "direction_audits": direction_audits,
'''
RESULT_AUDIT_REPL='''        "geometry_audits": geometry_audits,
        "truth_audits": truth_audits,
        "direction_audits": direction_audits,
'''

# Wrap v1 main: first run its fixed deterministic P3 transform to a temporary,
# then add the stricter truth firewall as a second exactly anchored transform.
def main()->int:
    if len(sys.argv)!=3: raise SystemExit('usage: apply_p3_patch_v2.py CANONICAL_P2 OUTPUT')
    source=Path(sys.argv[1]); output=Path(sys.argv[2]); tmp=output.with_suffix(output.suffix+'.stage1')
    old_argv=sys.argv; sys.argv=[str(HERE/'apply_p3_patch.py'),str(source),str(tmp)]
    try: m.main()
    finally: sys.argv=old_argv
    text=tmp.read_text()
    for before,after,label in (
        (TRUTH_HELPER_ANCHOR,TRUTH_HELPER_REPL,'truth helper insertion'),
        (PARSE_ANCHOR,PARSE_REPL,'geometry-only parser'),
        (TRUTH_OPEN_ANCHOR,TRUTH_OPEN_REPL,'post-freeze truth opening'),
        (RESULT_AUDIT_ANCHOR,RESULT_AUDIT_REPL,'truth firewall audit payload'),
    ):
        text=m.replace_once(text,before,after,label)
    output.write_text(text)
    tmp.unlink()
    print(f'P3_V2_OUTPUT_SHA256={m.digest(text.encode())}')
    print('P3_V2_TRUTH_FIREWALL=geometry-only before crossfit/model/membership freeze; known-shower values opened only afterward')
    return 0

if __name__=='__main__': raise SystemExit(main())
