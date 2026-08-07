#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath

EXPECTED_ARCHIVE_SHA={
    2022:'8347c4fde8d1035702f74002321e55d66df42055a0d3bf46424fd286b6e861f7',
    2023:'0220c5cb32eb4fdaaaca8773de03512864246c7a91c8211e68cc5d5f54f16f8a',
}
EXPECTED_LEGEND_SHA='afb3f9f7a3b753234db8dbb7219d14095510265293485fc1e744f659a857f48b'
COMMON_MONTHS=list(range(1,11))


def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('--structure-json',required=True,type=Path); p.add_argument('--output',required=True,type=Path)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    src=json.loads(a.structure_json.read_text())
    assert src['verdict']=='FAIL_SAAMER_2022_2023_STRUCTURAL_AUDIT'
    assert src['scientific_values_read'] is False
    assert src['shower_label_values_read'] is False
    assert src['orbital_values_read'] is False
    assert src['target_information_access'] is False
    assert src['excluded_target_interval_values_read'] is False
    by_year={int(row['year']):row for row in src['years']}
    assert set(by_year)=={2022,2023}

    member_months={}
    for year in (2022,2023):
        row=by_year[year]
        assert row['archive_sha256']==EXPECTED_ARCHIVE_SHA[year]
        assert row['legend_sha256']==EXPECTED_LEGEND_SHA
        assert row['global_token_count_histogram'].keys()=={'16'}
        assert row['gates']['zip_crc'] and row['gates']['safe_paths'] and row['gates']['one_legend']
        assert row['gates']['legend_exactly_matches_preexisting_2020_2021_schema_hash']
        assert row['gates']['all_expected_schema_fields_present_in_legend']
        assert row['gates']['no_unexpected_regular_members']
        months=[]
        for member in row['monthly_members']:
            mk=member['month_key']
            assert int(mk[0])==year
            assert member['token_count_histogram'].keys()=={'16'}
            months.append(int(mk[1]))
        member_months[year]=sorted(months)

    assert member_months[2022]==list(range(1,13))
    assert member_months[2023]==COMMON_MONTHS
    intersection=sorted(set(member_months[2022]) & set(member_months[2023]))
    assert intersection==COMMON_MONTHS

    result={
        'verdict':'PASS_SAAMER_2022_2023_COMMON_COVERAGE_ADJUDICATION',
        'source_structure_verdict':src['verdict'],
        'source_structure_run':31211663133,
        'source_structure_artifact':9006922387,
        'archive_sha256':{str(k):v for k,v in EXPECTED_ARCHIVE_SHA.items()},
        'legend_sha256':EXPECTED_LEGEND_SHA,
        'available_nominal_months':{str(year):member_months[year] for year in (2022,2023)},
        'frozen_common_nominal_months':COMMON_MONTHS,
        'excluded_2022_members_before_scientific_decode':['SAAnov2022.dat','SAAdec2022.dat'],
        'archive_access_this_adjudication':False,
        'meteor_value_access_this_adjudication':False,
        'target_information_access':False,
        'scientific_rules_changed':False,
        'claim_boundary':'Artifact-only metadata adjudication. The later scientific panel is frozen to January-October in both years solely because that is the exact nominal-month intersection established before scientific-value access.',
    }
    (a.output/'saamer_2022_2023_common_coverage_adjudication.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0

if __name__=='__main__': raise SystemExit(main())
