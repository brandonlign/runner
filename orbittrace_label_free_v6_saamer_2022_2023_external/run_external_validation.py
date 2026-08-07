#!/usr/bin/env python3
"""Final fresh SAAMER 2022/2023 external validation; reuses frozen 2020/2021 scientific functions."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

import numpy as np

from orbittrace_label_free_sparse_support_v6 import run_development as v6
from orbittrace_sparse_support_multiplicity_v5 import run_holdout as mult
from orbittrace_label_free_v6_saamer_external import run_external_validation as prior

YEARS=(2022,2023)
COMMON_MONTHS=tuple(range(1,11))
URLS={
    2022:'https://ceres.ta3.sk/iaumdcdb/dataDBs/radio_offline/iaumdcSAAMER2022.zip',
    2023:'https://ceres.ta3.sk/iaumdcdb/dataDBs/radio_offline/iaumdcSAAMER2023.zip',
}
EXPECTED_ARCHIVE_SHA256={
    2022:'8347c4fde8d1035702f74002321e55d66df42055a0d3bf46424fd286b6e861f7',
    2023:'0220c5cb32eb4fdaaaca8773de03512864246c7a91c8211e68cc5d5f54f16f8a',
}
EXPECTED_LEGEND_SHA256='afb3f9f7a3b753234db8dbb7219d14095510265293485fc1e744f659a857f48b'
MAX_EVENTS_PER_BIN=10_000
TOP_K=100
MIN_SCANNABLE_BINS=24
MIN_FAMILIES=100
MIN_ORBITALLY_CORROBORATED=30
BROWN_EQ_TOL=1e-10


def require(condition:bool,message:str)->None:
    if not condition:
        raise RuntimeError(message)


def parse_args()->argparse.Namespace:
    p=argparse.ArgumentParser()
    p.add_argument('--support-source-parts',required=True,type=Path)
    p.add_argument('--candidate-payload',required=True,type=Path)
    p.add_argument('--baseline-payload',required=True,type=Path)
    p.add_argument('--scorer-parts',required=True,type=Path)
    p.add_argument('--v6-result-json',required=True,type=Path)
    p.add_argument('--freshness-json',required=True,type=Path)
    p.add_argument('--coverage-json',required=True,type=Path)
    p.add_argument('--dsh-comparator',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    return p.parse_args()


def expected_all_months(year:int)->set[str]:
    if year==2022:
        return {prior.month_member(year,m) for m in range(1,13)}
    if year==2023:
        return {prior.month_member(year,m) for m in COMMON_MONTHS}
    raise ValueError(year)


def verify_common_archive_structure(year:int,path:Path)->dict[str,Any]:
    """Metadata-only member guard; returns Jan-Oct only for scientific parsing."""
    with zipfile.ZipFile(path) as zf:
        require(zf.testzip() is None,f'{year} ZIP CRC failure')
        names=zf.namelist()
        require(all(prior.safe_member(name) for name in names),f'{year} unsafe ZIP member')
        regular=[name for name in names if not name.endswith('/') and zf.getinfo(name).file_size>0]
        legends=[name for name in regular if PurePosixPath(name).name.lower()=='legend.inf']
        require(len(legends)==1,f'{year} legend count changed')
        legend=zf.read(legends[0])
        require(hashlib.sha256(legend).hexdigest()==EXPECTED_LEGEND_SHA256,f'{year} legend SHA changed')
        basename_to_member={PurePosixPath(name).name:name for name in regular}
        actual_dat={name for name in basename_to_member if name.lower().endswith('.dat')}
        require(actual_dat==expected_all_months(year),f'{year} monthly member set changed: {sorted(actual_dat)}')
        common=[basename_to_member[prior.month_member(year,m)] for m in COMMON_MONTHS]
        require(len(common)==10,f'{year} common-month member count changed')
        return {
            'year':year,
            'archive_sha256':EXPECTED_ARCHIVE_SHA256[year],
            'archive_bytes':path.stat().st_size,
            'legend_sha256':EXPECTED_LEGEND_SHA256,
            'available_dat_members':sorted(actual_dat),
            'monthly_members':common,
            'scientific_months':list(COMMON_MONTHS),
            'excluded_before_row_decode':(['SAAnov2022.dat','SAAdec2022.dat'] if year==2022 else []),
        }


def main()->int:
    args=parse_args(); args.output.mkdir(parents=True,exist_ok=True)

    # Every methodological and transport prerequisite is checked before archive scientific values.
    v6_result=json.loads(args.v6_result_json.read_text())
    require(v6_result['verdict']=='PASS_LABEL_FREE_SPARSE_SUPPORT_V6_DEVELOPMENT','v6 prerequisite did not pass')
    require(all(v6_result['integrity_gates'].values()),'v6 integrity changed')
    require(all(v6_result['scientific_gates'].values()),'v6 scientific gates changed')
    require(v6_result['configuration']['max_quartets_per_bin']==512,'v6 quartet cap changed')
    require(v6_result['configuration']['min_anchor_count']==2,'v6 anchor multiplicity changed')
    require(v6_result['configuration']['first_shortlist']==64 and v6_result['configuration']['audit_shortlist']==128,'v6 shortlist changed')
    require(v6_result['configuration']['no_source_labels_in_proposal_generation'] is True,'v6 label-free boundary changed')

    fresh=json.loads(args.freshness_json.read_text())
    require(fresh['verdict']=='PASS_SAAMER_2022_2023_REPO_SCIENTIFIC_FRESHNESS_AUDIT','freshness prerequisite did not pass')
    require(fresh['potential_exposure_hit_count']==0,'freshness exposure hit appeared')
    require(fresh['catalogue_access_this_audit'] is False and fresh['scientific_value_access_this_audit'] is False,'freshness boundary changed')
    require(fresh['target_information_access'] is False,'freshness target boundary changed')

    coverage=json.loads(args.coverage_json.read_text())
    require(coverage['verdict']=='PASS_SAAMER_2022_2023_COMMON_COVERAGE_ADJUDICATION','coverage adjudication did not pass')
    require(coverage['frozen_common_nominal_months']==list(COMMON_MONTHS),'common coverage changed')
    require(coverage['archive_sha256']=={str(k):v for k,v in EXPECTED_ARCHIVE_SHA256.items()},'coverage archive hashes changed')
    require(coverage['legend_sha256']==EXPECTED_LEGEND_SHA256,'coverage legend changed')
    require(coverage['archive_access_this_adjudication'] is False and coverage['meteor_value_access_this_adjudication'] is False,'coverage adjudication accessed data')
    require(coverage['scientific_rules_changed'] is False,'coverage adjudication changed science')

    require(all(mult.v3.self_test().values()),'multi-anchor v3 self-test failed')
    require(all(mult.brown.self_test().values()),'Brown self-test failed')
    runtime=mult.load_frozen_runtime()
    support=runtime.load_support_module(args.support_source_parts)

    # Freeze the same v6 runtime state used in 2020/2021, changing only the year universe/corpus label.
    support.YEARS=YEARS
    support.MONTH_KEYS=tuple()
    support.CORPUS='orbittrace-label-free-v6-saamer-2022-2023-external'
    support.RANKING_VARIANTS=('persistence','mean_year_strength','sqrt_support_strength','min_year_strength','size_penalized_strength')
    require(float(support.BLIND_LOW)==20.0 and float(support.BLIND_HIGH)==55.0,'blind interval changed')
    require(int(support.MIN_FAMILY_YEARS)==2,'family-year minimum changed')
    require(abs(float(support.FAMILY_LINK_RADIUS)-1.5)<1e-15,'family link radius changed')
    require(int(support.MIN_COMPONENT_EVENTS)==4 and int(support.MIN_COMPONENT_QUARTETS)==2,'component gates changed')
    require(int(support.SHORTLIST_K)==64 and int(support.AUDIT_SHORTLIST_K)==128,'shortlists changed')
    require(int(support.MIN_ANCHOR_COUNT)==2 and int(support.MAX_QUARTETS_PER_BIN)==512,'proposal gates changed')
    setattr(args,'fixed4_baseline_json',args.v6_result_json)
    _candidate,base,_scorer=support.load_sources(args)
    require(abs(float(getattr(_candidate,'CANDIDATE_SCALE',4.0))-4.0)<1e-15,'candidate scale changed')
    dsh=prior.load_dsh_module(args.dsh_comparator)

    # Patch only panel constants in the already-executed external helper module.
    prior.YEARS=YEARS
    prior.URLS=URLS
    prior.EXPECTED_ARCHIVE_SHA256=EXPECTED_ARCHIVE_SHA256
    prior.EXPECTED_LEGEND_SHA256=EXPECTED_LEGEND_SHA256
    prior.MAX_EVENTS_PER_BIN=MAX_EVENTS_PER_BIN
    prior.TOP_K=TOP_K
    prior.MIN_SCANNABLE_BINS=MIN_SCANNABLE_BINS
    prior.MIN_FAMILIES=MIN_FAMILIES
    prior.MIN_ORBITALLY_CORROBORATED=MIN_ORBITALLY_CORROBORATED
    prior.verify_archive_structure=verify_common_archive_structure

    archive_root=args.output/'_raw_saamer'
    archive_root.mkdir(exist_ok=True)
    archive_paths:dict[int,Path]={}
    structure:dict[int,dict[str,Any]]={}
    geometry_audits=[]
    scan_by_year:dict[int,list[dict[str,Any]]]={}

    try:
        # FIRST 2022/2023 SCIENTIFIC-VALUE ACCESS occurs inside parse_geometry_and_sample.
        for year in YEARS:
            archive_paths[year]=prior.download_archive(year,archive_root)
            structure[year]=verify_common_archive_structure(year,archive_paths[year])
            require(structure[year]['scientific_months']==list(COMMON_MONTHS),'scientific month set changed')
            events,audit=prior.parse_geometry_and_sample(year,archive_paths[year],structure[year],base)
            scan_by_year[year]=events; geometry_audits.append(audit)
            print(f"SAAMER {year} Jan-Oct: eligible={audit['eligible_geometry_before_density_cap']} selected={audit['selected_events']}",flush=True)

        components=[]; scan_audits=[]; retained_counts={}
        for year in YEARS:
            audit,passing,year_components=v6.label_free_scan_year(year,scan_by_year[year],support,base)
            scan_audits.append(audit); retained_counts[str(year)]=len(passing); components.extend(year_components)
            print(f"SAAMER v6 {year}: quartets={len(passing)} components={len(year_components)}",flush=True)

        families,support_rankings=support.build_families(components,base)
        persistence_order=[str(value) for value in support_rankings['persistence']]
        family_ids=[str(family['family_id']) for family in families]
        require(set(persistence_order)==set(family_ids) and len(persistence_order)==len(family_ids),'persistence universe mismatch')

        mult.YEARS=YEARS; mult.TOP_K=TOP_K
        scored,scoring_summary=mult.score_families(families,scan_by_year,runtime,base)
        require(len(scored)==len(families),'not every recurrent family received a score')
        rankings={
            'multiplicity':mult.rank_scored(scored,'multiplicity'),
            'brown':mult.rank_scored(scored,'brown'),
            'v3':mult.rank_scored(scored,'v3'),
            'label_free_persistence':persistence_order,
        }
        require(all(set(order)==set(family_ids) for order in rankings.values()),'ranking universe changed')
        rankings_frozen_before_orbit_access=True

        # FIRST ORBITAL-ELEMENT INTERPRETATION: every family/ranking is already frozen.
        needed_ids={str(event_id) for family in families for event_id in family['event_ids']}
        orbits,orbit_read_audit=prior.read_orbits_after_rank_freeze(archive_paths,needed_ids)
        corroboration,orbital_summary=prior.orbital_corroboration(families,orbits,dsh)
        metrics={name:prior.evaluate_ranking(order,corroboration) for name,order in rankings.items()}

        n=len(families); q=int(orbital_summary['orbitally_corroborated_families'])
        scannable=all(int(a['scannable_bin_count'])>=MIN_SCANNABLE_BINS for a in scan_audits)
        shortlist_exact=all(int(a['shortlist_audit_failures'])==0 for a in scan_audits)
        exact_years=all(sorted(int(y) for y in family['years'])==list(YEARS) for family in families)
        exact_episode_sizes=scoring_summary['episode_sizes']==[128] if families else False
        density_exact=all(
            all(int(value)<=MAX_EVENTS_PER_BIN for value in audit['selected_by_bin'].values())
            and audit['density_cap']==MAX_EVENTS_PER_BIN
            for audit in geometry_audits
        )
        common_months_exact=all(structure[year]['scientific_months']==list(COMMON_MONTHS) for year in YEARS)
        excluded_2022_exact=structure[2022]['excluded_before_row_decode']==['SAAnov2022.dat','SAAdec2022.dat']

        integrity_gates={
            'frozen_v6_freshness_and_common_coverage_prerequisites':True,
            'exact_archive_and_legend_hashes':all(
                structure[year]['archive_sha256']==EXPECTED_ARCHIVE_SHA256[year]
                and structure[year]['legend_sha256']==EXPECTED_LEGEND_SHA256 for year in YEARS
            ),
            'exact_common_jan_oct_scientific_coverage':common_months_exact and excluded_2022_exact,
            'target_interval_removed_before_radiant_speed':all(a['blind_removed_before_radiant_speed']>=0 for a in geometry_audits),
            'rankings_frozen_before_orbital_interpretation':rankings_frozen_before_orbit_access and orbit_read_audit['orbital_elements_interpreted_only_after_rank_freeze'],
            'exact_10000_identity_hash_density_normalization':density_exact,
            'at_least_24_scannable_bins_each_year':scannable,
            'zero_shortlist_audit_mismatches':shortlist_exact,
            'all_recurrent_families_span_both_years':exact_years,
            'all_local_episode_sizes_exact_128':exact_episode_sizes,
            'brown_equivalence_within_1e_10':float(scoring_summary['max_brown_equivalence_difference'])<=BROWN_EQ_TOL,
            'at_least_100_recurrent_families':n>=MIN_FAMILIES,
            'at_least_30_orbitally_corroborated_families':q>=MIN_ORBITALLY_CORROBORATED,
        }

        m=int(metrics['multiplicity']['top_k_orbitally_corroborated'])
        b=int(metrics['brown']['top_k_orbitally_corroborated'])
        p=int(metrics['label_free_persistence']['top_k_orbitally_corroborated'])
        required_vs_persistence=int(math.ceil(0.90*p))
        scientific_gates={
            'multiplicity_topk_beats_brown_by_at_least_one':m>=b+1,
            'multiplicity_topk_at_least_90pct_persistence':m>=required_vs_persistence,
            'multiplicity_topk_hypergeometric_enrichment_p_le_005':float(metrics['multiplicity']['hypergeometric_enrichment_p'])<=0.05,
        }

        if not all(integrity_gates.values()):
            if not integrity_gates['at_least_100_recurrent_families'] or not integrity_gates['at_least_30_orbitally_corroborated_families']:
                verdict='INCONCLUSIVE_LABEL_FREE_V6_SAAMER_2022_2023_EXTERNAL_POWER'
            else:
                verdict='FAIL_LABEL_FREE_V6_SAAMER_2022_2023_EXTERNAL_INTEGRITY'
        elif all(scientific_gates.values()):
            verdict='PASS_LABEL_FREE_V6_SAAMER_2022_2023_EXTERNAL_VALIDATION'
        else:
            verdict='FAIL_LABEL_FREE_V6_SAAMER_2022_2023_EXTERNAL_VALIDATION'

        result={
            'verdict':verdict,
            'configuration':{
                'years':list(YEARS),'scientific_months':list(COMMON_MONTHS),'blind_exclusion':[20.0,55.0],
                'max_events_per_10deg_bin':MAX_EVENTS_PER_BIN,
                'density_selection':'smallest SHA256 of SAAMER|year|member|physical_row_number',
                'candidate_architecture':'frozen label-free sparse-support v6',
                'primary_ranking':'worst-year multiplicity descending, geometric-mean multiplicity descending, family id',
                'multiplicity':'(multi-anchor-v3-energy / Brown-peak)^2',
                'orbital_validation':'largest cross-year D_SH<0.05 single-link component; >=4 events/year; >=0.50 family precision',
                'top_k':TOP_K,'no_source_labels':True,'no_orbits_in_candidate_or_ranking':True,
                'no_threshold_search':True,'no_density_search':True,'no_cap_search':True,'no_weight_search':True,
                'scientific_gates_identical_to_2020_2021':True,
            },
            'archive_structure':[structure[year] for year in YEARS],
            'geometry_audits':geometry_audits,
            'fixed4_scan_audits':scan_audits,
            'retained_quartet_counts':retained_counts,
            'family_count':n,
            'family_scoring_summary':scoring_summary,
            'orbit_read_audit':orbit_read_audit,
            'orbital_summary':orbital_summary,
            'metrics':metrics,
            'required_multiplicity_vs_persistence':required_vs_persistence,
            'integrity_gates':integrity_gates,
            'scientific_gates':scientific_gates,
            'prior_saamer_2020_2021_result':'INCONCLUSIVE_LABEL_FREE_V6_SAAMER_EXTERNAL_POWER',
            'terminal_external_panel':True,
            'claim_boundary':(
                'Final fresh SAAMER external panel under the already-frozen label-free v6 architecture. '
                'Common Jan-Oct coverage was fixed from archive-member metadata before scientific values. '
                'The 20-55 degree target interval was excluded before radiant/speed use; orbital elements were first interpreted only after all discovery rankings were frozen. '
                'No OrbitTrace target information entered this run.'
            ),
        }
        (args.output/'saamer_2022_2023_external_validation.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
        (args.output/'saamer_2022_2023_rankings.json').write_text(json.dumps(rankings,indent=2)+'\n')
        (args.output/'saamer_2022_2023_orbital_corroboration.json.gz').write_bytes(gzip.compress(json.dumps(corroboration,separators=(',',':')).encode()))
        (args.output/'saamer_2022_2023_families.json.gz').write_bytes(gzip.compress(json.dumps(families,separators=(',',':')).encode()))
        (args.output/'saamer_2022_2023_family_scores.json.gz').write_bytes(gzip.compress(json.dumps(scored,separators=(',',':')).encode()))

        k=min(TOP_K,n)
        lines=[
            '# OrbitTrace label-free v6 SAAMER 2022-2023 final fresh external validation','',
            f'Verdict: **`{verdict}`**','',
            f'- recurrent families: **{n}**',f'- orbitally corroborated families: **{q}**',
            f'- multiplicity top-{k} corroborated: **{m}**; enrichment p: **{metrics["multiplicity"]["hypergeometric_enrichment_p"]:.6g}**',
            f'- label-free persistence top-{k} corroborated: **{p}**',f'- Brown top-{k} corroborated: **{b}**',
            f'- total-v3 top-{k} corroborated: **{metrics["v3"]["top_k_orbitally_corroborated"]}**',
            f'- median valid-orbit fraction: **{orbital_summary["median_valid_orbit_fraction"]:.4f}**','',
            'Scientific coverage was frozen to January-October in both years before any meteor value access. No source shower labels were available or used; orbital elements were validation-only after ranking freeze.'
        ]
        (args.output/'SAAMER_2022_2023_EXTERNAL_VALIDATION.md').write_text('\n'.join(lines)+'\n')
        print('\n'.join(lines),flush=True)
        return 0
    finally:
        if archive_root.exists():
            for path in archive_root.iterdir():
                path.unlink()
            archive_root.rmdir()

if __name__=='__main__': raise SystemExit(main())
