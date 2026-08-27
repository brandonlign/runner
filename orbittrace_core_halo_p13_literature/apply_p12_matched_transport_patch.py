#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

EXPECTED_P12_SHA256='78e93b5af19a441bc58b00428d2b356218b33f7a4a891a640dd59cb5d4599c32'


def digest(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()


def replace_once(text:str,before:str,after:str,label:str)->str:
    count=text.count(before)
    if count!=1:
        raise RuntimeError(f'P13 P12 transport anchor {label} count={count}')
    return text.replace(before,after,1)


def replace_span(text:str,start:str,end:str,replacement:str,label:str)->str:
    i=text.find(start)
    if i<0: raise RuntimeError(f'P13 P12 transport start anchor missing: {label}')
    j=text.find(end,i)
    if j<0: raise RuntimeError(f'P13 P12 transport end anchor missing: {label}')
    j+=len(end)
    if text.find(start,i+1)>=0: raise RuntimeError(f'P13 P12 transport start anchor nonunique: {label}')
    return text[:i]+replacement+text[j:]


def main()->int:
    if len(sys.argv)!=3:
        raise SystemExit('usage: apply_p12_matched_transport_patch.py EXACT_P12 OUTPUT')
    src=Path(sys.argv[1]); out=Path(sys.argv[2]); raw=src.read_bytes(); actual=digest(raw)
    if actual!=EXPECTED_P12_SHA256:
        raise RuntimeError(f'exact P12 source SHA changed: {actual}')
    t=raw.decode('utf-8')

    t=replace_once(t,'import math\nimport types\n','import math\nimport pickle\nimport types\n','pickle import')
    t=replace_once(t,'YEARS = (2022, 2023)\n','YEARS = (2023, 2025)\n','matched years')
    t=replace_once(
        t,
        '    p.add_argument("--dsh-comparator", required=True, type=Path)\n    p.add_argument("--output", required=True, type=Path)\n',
        '    p.add_argument("--dsh-comparator", required=True, type=Path)\n    p.add_argument("--panel-input", required=True, type=Path)\n    p.add_argument("--output", required=True, type=Path)\n',
        'panel input argument',
    )

    start='    require(sha256_file(args.v6_structural_families_json_gz) == V6_STRUCTURAL_FAMILIES_SHA256, "v6 structural-family artifact mismatch")\n'
    end='    require(all(seed_id in orbit_by_id for seed_id in global_seed_ids), "P2 input-ineligible: exact v8 seed missing valid orbit")\n'
    repl='''    # P13 matched-panel transport changes only the data universe.  The exact
    # P12 feature/model/membership code below is left unchanged.  Input was
    # frozen from strict ID-only manifests before comparator/truth values.
    dsh = load_dsh_module(args.dsh_comparator)
    old = load_module(args.base_runner, "orbittrace_p13_p12_panel_base_runner")
    support = old.load_support_module(args.support_source_parts)
    source_args = types.SimpleNamespace(
        candidate_payload=args.candidate_payload,
        baseline_payload=args.baseline_payload,
        scorer_parts=args.scorer_parts,
    )
    _, base, _ = support.load_sources(source_args)
    require(float(support.BLIND_LOW) == 20.0 and float(support.BLIND_HIGH) == 55.0, "blind interval changed")

    panel_input = json.loads(gzip.decompress(args.panel_input.read_bytes()).decode("utf-8"))
    require(panel_input["classification"] == "P13 matched-literature pretruth core panel input", "wrong P13 panel input class")
    panel = str(panel_input["panel"])
    require(panel in {"hdbscan", "sugar"}, "invalid P13 panel")
    require(panel_input["years"] == list(YEARS), "P13 panel years changed")
    require(panel_input["blind_exclusion"] == [20.0,55.0], "P13 panel blind interval changed")
    require(panel_input["competitor_cluster_values_accessed"] is False, "competitor values entered P13 panel input")
    require(panel_input["known_shower_truth_accessed"] is False, "truth entered P13 panel input")
    require(panel_input["parameter_search"] is False, "P13 panel parameter search enabled")
    scan_by_year = {year: list(panel_input["scan_by_year"][str(year)]) for year in YEARS}
    orbit_by_id = {str(k):v for k,v in panel_input["orbit_by_id"].items()}
    exact_scan_ids = {year:{str(e["id"]) for e in scan_by_year[year]} for year in YEARS}
    require(all(len(exact_scan_ids[y]) == len(scan_by_year[y]) for y in YEARS), "P13 panel duplicate scan ID")
    require(set(orbit_by_id) == set().union(*(exact_scan_ids[y] for y in YEARS)), "P13 panel orbit/scan universe mismatch")
    require(all(not (20.0 <= float(e["sol"]) <= 55.0) for y in YEARS for e in scan_by_year[y]), "target interval entered P13 panel scan")
    families = json.loads(json.dumps(panel_input["core_families"]))
    v8_order = list(map(str,panel_input["multiplicity_order"]))
    require(len(families) == len(v8_order) == int(panel_input["core_family_count"]), "P13 core family/order count changed")
    require({str(f["family_id"]) for f in families} == set(v8_order), "P13 core family/order universe changed")
    by_id = {str(f["family_id"]):f for f in families}
    families = [by_id[fid] for fid in v8_order]
    family_rank = {str(fid):index for index,fid in enumerate(v8_order)}
    core_identity_payload = [
        {"family_id":str(f["family_id"]),"event_ids":sorted(map(str,f["event_ids"]))}
        for f in families
    ]
    core_identity_payload.sort(key=lambda r:r["family_id"])
    core_pretruth_sha256 = canonical_sha(core_identity_payload)
    require(core_pretruth_sha256 == str(panel_input["core_pretruth_sha256"]), "P13 core identity changed before halo transport")
    global_seed_ids = set().union(*(set(map(str,f["event_ids"])) for f in families))
    require(all(seed_id in orbit_by_id for seed_id in global_seed_ids), "P13 core seed missing exact panel orbit")
    geometry_audits = list(panel_input["geometry_audits"])
    orbit_audits = list(panel_input["orbit_audits"])
    sources = geometry_audits
'''
    t=replace_span(t,start,end,repl,'panel universe replacement')

    old_year_ids='''        ids_by_year = {
            year: sorted(str(eid) for eid in family["event_ids"] if int(str(eid)[:4]) == year)
            for year in YEARS
        }
'''
    new_year_ids='''        ids_by_year = {
            year: sorted(str(eid) for eid in family["event_ids"] if str(eid) in event_lookup_by_year[year])
            for year in YEARS
        }
'''
    t=replace_once(t,old_year_ids,new_year_ids,'SNM panel year identity')
    t=replace_once(t,'        for source_year, target_year in ((2022, 2023), (2023, 2022)):\n','        for source_year, target_year in ((2023, 2025), (2025, 2023)):\n','matched reciprocal years')

    truth='    hidden_labels, truth_audits = p3_parse_truth_after_freeze(support, pretruth_ids)\n'
    stop='''    # P13 matched transport stops exactly at the existing P12 truth firewall.
    # No known-shower or competitor cluster value is opened here.
    require(
        len(p12_drift_sha) == 64 and len(crossfit_sha) == 64 and len(model_sha) == 64
        and len(density_sha) == 64 and len(membership_sha) == 64 and len(decision_sha) == 64,
        "P13 transported P12 pretruth hashes missing",
    )
    halo_checkpoint = {
        "classification": "P13 exact-P12 matched-panel pretruth halo transport",
        "panel": panel,
        "years": list(YEARS),
        "blind_exclusion": [20.0,55.0],
        "competitor_cluster_values_accessed": False,
        "known_shower_truth_accessed": False,
        "parameter_search": False,
        "core_families": families,
        "core_multiplicity_order": v8_order,
        "core_pretruth_sha256": core_pretruth_sha256,
        "halo_families": expanded,
        "drift_pretruth_sha256": p12_drift_sha,
        "crossfit_pretruth_sha256": crossfit_sha,
        "model_pretruth_sha256": model_sha,
        "density_pretruth_sha256": density_sha,
        "halo_membership_pretruth_sha256": membership_sha,
        "decisions_pretruth_sha256": decision_sha,
        "assigned_nonseed_events": int(len(assignments)),
        "proposal_events": int(len(proposals_by_event)),
        "conflicted_proposal_events": int(conflicted),
        "p12_bidirectional_family_count_pretruth": int(p12_bidirectional_family_count_pretruth),
        "geometry_audits": geometry_audits,
        "orbit_audits": orbit_audits,
        "exact_event_rows": {str(y):len(scan_by_year[y]) for y in YEARS},
        "target_accessed": False,
    }
    raw_checkpoint = pickle.dumps(halo_checkpoint, protocol=pickle.HIGHEST_PROTOCOL)
    checkpoint_path = args.output / f"p13_{panel}_p12_halo_pretruth.pkl"
    checkpoint_path.write_bytes(raw_checkpoint)
    checkpoint_path.with_suffix(checkpoint_path.suffix + ".sha256").write_text(hashlib.sha256(raw_checkpoint).hexdigest() + "\\n")
    print("P13_P12_HALO_PRETRUTH_FROZEN", panel, json.dumps({
        "core_families":len(families),
        "halo_families":len(expanded),
        "assigned_nonseed_events":len(assignments),
        "proposal_events":len(proposals_by_event),
        "core_pretruth_sha256":core_pretruth_sha256,
        "halo_membership_pretruth_sha256":membership_sha,
    },sort_keys=True),flush=True)
    return 0
'''
    t=replace_once(t,truth,stop,'stop before truth')

    if 'OrbitTrace-April' in t or 'target_coordinate' in t:
        raise RuntimeError('forbidden target-specific token introduced')
    out.write_text(t,encoding='utf-8')
    print(f'P13_P12_TRANSPORT_INPUT_SHA256={EXPECTED_P12_SHA256}')
    print(f'P13_P12_TRANSPORT_OUTPUT_SHA256={digest(t.encode())}')
    print('P13_P12_TRANSPORT_SCOPE=exact P12 science on strict P13 2023/2025 panel/core universe; stop at original pretruth firewall; no comparator/truth/target values')
    return 0


if __name__=='__main__': raise SystemExit(main())
