#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

SECONDARY = ('mean_year_strength', 'min_year_strength', 'size_penalized_strength')
PANELS = ('development', 'validation')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    return parser.parse_args()


def unique(root: Path, name: str) -> Path:
    found = list(root.rglob(name))
    if len(found) != 1:
        raise RuntimeError(f'expected one {name}, found {found}')
    return found[0]


def rank_metrics(panel: dict, secondary: str, weight: float) -> dict:
    families = panel['families']
    ordered = sorted(
        families,
        key=lambda f: (
            -(
                weight / (60.0 + float(f['ranks']['persistence']))
                + (1.0 - weight) / (60.0 + float(f['ranks'][secondary]))
            ),
            f['family_id'],
        ),
    )
    ranks = {family['family_id']: rank for rank, family in enumerate(ordered, 1)}
    baseline_per_label = panel['evaluation']['metrics']['persistence']['per_label']
    qualified = [item for item in baseline_per_label if item.get('qualified')]
    matched_ranks = [ranks[item['family_id']] for item in qualified]
    return {
        'qualified_matches': len(qualified),
        'recovered_at_100': sum(rank <= 100 for rank in matched_ranks),
        'recovered_at_500': sum(rank <= 500 for rank in matched_ranks),
        'mrr': sum(1.0 / rank for rank in matched_ranks) / len(matched_ranks),
    }


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    result = json.loads(unique(args.input, 'orbittrace_fixed4_support_wrapper_development.json').read_text())
    if result['verdict'] != 'FAIL_SUPPORT_NORMALIZED_WRAPPER_DEVELOPMENT':
        raise RuntimeError('unexpected v2 verdict')

    candidates = []
    for secondary_index, secondary in enumerate(SECONDARY):
        for weight_i in range(50, 91):
            weight = weight_i / 100.0
            panels = {}
            deltas = {}
            eligible = True
            for panel_name in PANELS:
                panel = result['panel_results'][panel_name]
                metrics = rank_metrics(panel, secondary, weight)
                baseline = panel['evaluation']['metrics']['persistence']
                panels[panel_name] = metrics
                deltas[panel_name] = {
                    'recovered_at_100': metrics['recovered_at_100'] - baseline['recovered_at_100'],
                    'recovered_at_500': metrics['recovered_at_500'] - baseline['recovered_at_500'],
                    'mrr': metrics['mrr'] - baseline['mrr'],
                }
                eligible &= deltas[panel_name]['recovered_at_500'] >= 0
                eligible &= deltas[panel_name]['mrr'] >= 0.0
            if not eligible:
                continue
            key = (
                min(deltas[p]['recovered_at_100'] for p in PANELS),
                sum(deltas[p]['recovered_at_100'] for p in PANELS),
                min(deltas[p]['mrr'] for p in PANELS),
                sum(deltas[p]['mrr'] for p in PANELS),
                -abs(weight - 0.67),
                -secondary_index,
            )
            candidates.append({
                'secondary': secondary,
                'persistence_weight': weight,
                'rrf_constant': 60.0,
                'panels': panels,
                'deltas': deltas,
                'selection_key': list(key),
            })
    if not candidates:
        raise RuntimeError('no eligible reciprocal-rank fusion candidate')
    selected = max(candidates, key=lambda item: tuple(item['selection_key']))
    expected = ('min_year_strength', 0.66)
    if (selected['secondary'], selected['persistence_weight']) != expected:
        raise RuntimeError(f'unexpected selected candidate: {selected}')

    output = {
        'classification': 'LOCK_RRF_PERSISTENCE_MIN_YEAR_066',
        'candidate_count': len(candidates),
        'selected': selected,
        'formula': '0.66/(60+persistence_rank) + 0.34/(60+min_year_strength_rank)',
        'claim_boundary': (
            'This formula is developed on 2022-2025 target-excluded evidence and is not validated until '
            'a one-shot 2019-2021 known-shower test passes.'
        ),
    }
    (args.output / 'orbittrace_fixed4_rrf_diagnosis.json').write_text(
        json.dumps(output, indent=2, sort_keys=True) + '\n', encoding='utf-8'
    )
    md = f'''# Fixed4 reciprocal-rank fusion diagnosis

Classification: `LOCK_RRF_PERSISTENCE_MIN_YEAR_066`

Locked formula:

`0.66/(60+persistence_rank) + 0.34/(60+min_year_strength_rank)`

| panel | top-100 delta | top-500 delta | MRR delta |
|---|---:|---:|---:|
| 2022–2023 | {selected['deltas']['development']['recovered_at_100']:+d} | {selected['deltas']['development']['recovered_at_500']:+d} | {selected['deltas']['development']['mrr']:+.6f} |
| 2024–2025 | {selected['deltas']['validation']['recovered_at_100']:+d} | {selected['deltas']['validation']['recovered_at_500']:+d} | {selected['deltas']['validation']['mrr']:+.6f} |

This is a development result only. The formula must pass a separately frozen one-shot test on previously unused 2019–2021 labels before any OrbitTrace application.
'''
    (args.output / 'ORBITTRACE_FIXED4_RRF_DIAGNOSIS.md').write_text(md, encoding='utf-8')
    print(md)


if __name__ == '__main__':
    main()
