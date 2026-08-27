#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import json
from collections import Counter
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--broad', required=True, type=Path)
    parser.add_argument('--cal-scan', required=True, type=Path)
    parser.add_argument('--cal-reveal', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    return parser.parse_args()


def unique(root: Path, name: str) -> Path:
    found = list(root.rglob(name))
    if len(found) != 1:
        raise RuntimeError(f'expected one {name} under {root}, found {found}')
    return found[0]


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    broad_scan = json.loads(unique(args.broad, 'blind_scan.json').read_text(encoding='utf-8'))
    broad_reveal = json.loads(unique(args.broad, 'orbittrace_blind_reveal.json').read_text(encoding='utf-8'))
    with gzip.open(unique(args.cal_scan, 'orbittrace_fixed4_blind_scan.json.gz'), 'rt', encoding='utf-8') as handle:
        calibrated_scan = json.load(handle)
    calibrated_reveal = json.loads(
        unique(args.cal_reveal, 'orbittrace_fixed4_blind_reveal.json').read_text(encoding='utf-8')
    )

    threshold_support: dict[str, dict[str, int]] = {}
    complete_saturation = True
    for threshold in ('1.5', '2', '2.5'):
        families = broad_scan['families'][threshold]
        if len(families) != 5000:
            raise RuntimeError(f'unexpected family count at {threshold}: {len(families)}')
        counts = Counter(int(f['support']) for f in families)
        threshold_support[threshold] = {str(k): int(v) for k, v in sorted(counts.items())}
        complete_saturation &= counts == Counter({8: 5000})

    availability = broad_reveal['canonical_availability']
    canonical_by_year = {
        str(year): int(record['present_in_blind_catalogue'])
        for year, record in sorted(availability.items())
    }
    quartet_capable_years = [year for year, count in canonical_by_year.items() if count >= 4]
    if sum(canonical_by_year.values()) != 101:
        raise RuntimeError('canonical availability does not sum to 101')

    selected = calibrated_reveal['selected_family']
    expected = {
        'family_id': 'F0059',
        'rank': 59,
        'year_count': 4,
        'event_count': 39,
        'canonical_overlap': 29,
    }
    if calibrated_reveal['verdict'] != 'PARTIAL_BLIND_ORBITTRACE_RECOVERY':
        raise RuntimeError('calibrated verdict changed')
    for key, value in expected.items():
        if selected.get(key) != value:
            raise RuntimeError(f'calibrated invariant changed: {key}={selected.get(key)}')
    family = next(f for f in calibrated_scan['families'] if f['family_id'] == 'F0059')
    if family['year_count'] != 4 or family['rank'] != 59:
        raise RuntimeError('calibrated scan family invariants changed')

    minimum_broad_support = min(
        int(f['support'])
        for threshold in ('1.5', '2', '2.5')
        for f in broad_scan['families'][threshold]
    )
    classification = (
        'PERSISTENCE_RANKING_SATURATION_CONFIRMED'
        if complete_saturation and selected['year_count'] < minimum_broad_support
        else 'NO_COMPLETE_PERSISTENCE_SATURATION'
    )

    result = {
        'classification': classification,
        'broad_threshold_support_distributions': threshold_support,
        'broad_preserved_families_per_threshold': 5000,
        'broad_minimum_preserved_year_support': minimum_broad_support,
        'broad_canonical_availability_by_year': canonical_by_year,
        'broad_quartet_capable_canonical_years': quartet_capable_years,
        'broad_quartet_capable_year_count': len(quartet_capable_years),
        'calibrated_selected_family': {
            'family_id': selected['family_id'],
            'rank': selected['rank'],
            'year_count': selected['year_count'],
            'years': selected['years'],
            'event_count': selected['event_count'],
            'canonical_overlap': selected['canonical_overlap'],
            'precision': selected['precision'],
        },
        'interpretation': (
            'The broad negative is valid for its frozen persistence-first wrapper, but its reveal set contains '
            'no family with fewer than eight years. It is not a balanced negative test of four-year episodic '
            'recurrence and cannot be treated as an equal-strength refutation of the calibrated partial recovery.'
        ),
        'authorized_next_step': (
            'Develop a support-normalized generic ranking using known non-OrbitTrace showers after removing '
            'solar longitude 20-55 degrees before labels and endpoints.'
        ),
    }
    (args.output / 'orbittrace_fixed4_wrapper_saturation_audit.json').write_text(
        json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8'
    )
    md = f'''# OrbitTrace fixed4 wrapper-saturation audit

Classification: `{classification}`

All three broad top-5,000 family lists were saturated by eight-year families:

- threshold 1.5: `{threshold_support['1.5']}`
- threshold 2.0: `{threshold_support['2']}`
- threshold 2.5: `{threshold_support['2.5']}`

Minimum support in the broad reveal set: **{minimum_broad_support} years**.

Canonical availability by year: `{canonical_by_year}`. Only **{len(quartet_capable_years)}** years contained at least four canonical events: `{quartet_capable_years}`.

The calibrated family **F0059** ranked **59/780**, spanned **4 years**, and contained **29/39** canonical members at precision **{selected['precision']:.4f}**.

The broad negative remains valid for its persistence-first wrapper, but the conflict is explained primarily by ranking saturation rather than disagreement in the fixed four-clique core.
'''
    (args.output / 'ORBITTRACE_FIXED4_WRAPPER_SATURATION_AUDIT.md').write_text(md, encoding='utf-8')
    print(md)
    if classification != 'PERSISTENCE_RANKING_SATURATION_CONFIRMED':
        raise SystemExit('frozen saturation classification did not pass')


if __name__ == '__main__':
    main()
