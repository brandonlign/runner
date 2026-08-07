#!/usr/bin/env python3
"""Source/artifact-only audit: are SonotaCo 2017 and 2019 still score/label-unseen?"""
from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path

OUT = Path('output')
OUT.mkdir(exist_ok=True)


def git_show(ref: str, path: str) -> str:
    return subprocess.check_output(['git', 'show', f'{ref}:{path}'], text=True)


def assignment_tuple(source: str, name: str):
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(t, ast.Name) and t.id == name for t in targets):
                value = node.value
                if isinstance(value, (ast.Tuple, ast.List)):
                    vals=[]
                    for e in value.elts:
                        if not isinstance(e, ast.Constant):
                            raise RuntimeError(f'nonconstant {name}')
                        vals.append(e.value)
                    return vals
    raise RuntimeError(f'missing assignment {name}')


def main() -> int:
    # 2017: use preserved post-access fixed-protocol failure artifact plus exact runner source.
    prior = json.loads(Path('input/2017_failure/multiplicity_sonotaco_external.json').read_text())
    runner = git_show('origin/agent/orbittrace-multiplicity-sonotaco-2015-2017-external', 'orbittrace_multiplicity_sonotaco_2015_2017_external/run_external_validation.py')
    years = assignment_tuple(runner, 'YEARS')
    assert years == [2015, 2017], years
    assert 'parsed_by_year = {' in runner
    assert 'year: parse_year(year, parser_modules[year], archives[year], base, args.mapping_audit)' in runner
    assert 'for year in YEARS' in runner
    assert prior['verdict'] == 'FAIL_MULTIPLICITY_SONOTACO_EXTERNAL_INTEGRITY'
    assert prior['stage'] == 'parser_transport'
    assert prior['scientific_ranking_result_available'] is False
    assert prior['orbittrace_target_access'] is False
    assert 'frozen 2015 parser gate failed' in prior['error']
    assert len(prior['archive_sources']) == 2

    # Python dict-comprehension iteration is sequential. Since parse_year(2015)
    # raised, parse_year(2017) was never invoked; build_hidden_panel/scanning/ranking
    # are below the exception boundary in the frozen runner.
    index_parse = runner.index('parsed_by_year = {')
    index_hidden = runner.index('scan_by_year, calibration_by_year, hidden_labels, hidden_years = build_hidden_panel')
    index_scan = runner.index('support.scan_year(', index_hidden)
    assert index_parse < index_hidden < index_scan

    # 2019: exact frozen CMOR multiyear input audit explicitly forbade labels/scores.
    cmor = json.loads(git_show('origin/agent/orbittrace-cmor-wavelet-multiyear-input-audit', 'orbittrace_literature_freeze/SONOTACO_2019_2025_CMOR_WAVELET_MULTIYEAR_INPUT_RESULT.json'))
    protocol = json.loads(git_show('origin/agent/orbittrace-cmor-wavelet-multiyear-input-audit', 'orbittrace_literature_comparison/CMOR_WAVELET_MULTIYEAR_INPUT_PROTOCOL.json'))
    loader = git_show('origin/agent/orbittrace-cmor-wavelet-multiyear-input-audit', 'orbittrace_literature_comparison/run_cmor_wavelet_multiyear_input_audit_v2.py')
    assert cmor['verdict'] == 'PASS_CMOR_WAVELET_MULTIYEAR_INPUT_AUDIT'
    assert cmor['frozen_design']['wavelet_coefficients_computed'] is False
    assert cmor['frozen_design']['shower_labels_read'] is False
    assert cmor['integrity']['wavelet_endpoint_computed'] is False
    assert cmor['integrity']['candidate_values_accessed'] is False
    y2019 = next(x for x in cmor['annual_inputs'] if x['year'] == 2019)
    assert y2019['archive_sha256'] == 'd49c37f5a9f7f089973d7029b840283f26ca9d915c137152a6f4368bbf5aabb4'
    assert y2019['member_sha256'] == '8d80ec18108c04ace4f1a2f3daeaa05ab1e7d879022c2db8b80185d28f5aa11f'
    assert protocol['geometry_and_quality']['shower_labels_read'] is False
    assert 'Do not calculate a wavelet coefficient' in protocol['prohibitions'][0]
    assert 'Do not read shower labels or OrbitTrace candidate values.' in protocol['prohibitions']
    assert 'required = ("sol(deg)", "vg(km/s)", "vg sd(km/s)", "Qc(deg)")' in loader
    assert '"shower_label_field_read": False' in loader

    result = {
        'verdict': 'PASS_SONOTACO_2017_2019_SCORE_LABEL_HOLDOUT_BOUNDARY_AUDIT',
        'catalogue_download_this_audit': False,
        'target_information_access': False,
        'scientific_score_access_this_audit': False,
        'classification': 'raw-transport-exposed but scientific-score-and-label-unseen pair',
        'years': {
            '2017': {
                'raw_archive_exposed': True,
                'archive_sha256': next(x['sha256'] for x in prior['archive_sources'] if x['year'] == 2017),
                'parser_invoked_before_failure': False,
                'shower_labels_read_in_current_chain': False,
                'detector_scores_computed_in_current_chain': False,
                'scientific_ranking_computed_in_current_chain': False,
                'basis': '2015-first parse raised before 2017 parse invocation; downstream hidden panel and ranking were not reached',
            },
            '2019': {
                'raw_archive_exposed': True,
                'archive_sha256': y2019['archive_sha256'],
                'member_sha256': y2019['member_sha256'],
                'shower_labels_read_in_prior_input_audit': False,
                'wavelet_coefficients_computed_in_prior_input_audit': False,
                'candidate_values_accessed_in_prior_input_audit': False,
                'basis': 'frozen CMOR multiyear input audit read only solar longitude, speed, speed uncertainty, and convergence angle',
            },
        },
        'claim_boundary': 'This establishes only a score/label-unseen holdout boundary, not raw-data freshness. Any later evaluation must be described as a locked scientific-score/label holdout, not pristine first-pass prospective validation.',
    }
    (OUT / 'sonotaco_2017_2019_score_label_boundary_audit.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
