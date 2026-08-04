from __future__ import annotations

import argparse
import re
from pathlib import Path

SCORE_FUNCTION = '''def fourstar_score(base: types.ModuleType, episode: Any, distance: np.ndarray | None = None) -> float:\n    \"\"\"Negative minimum diameter among center-plus-three-nearest four-point stars.\n\n    Every event is considered as a possible center. Its three nearest neighbors are\n    added and the tightest resulting four-point diameter is returned with a negative\n    sign, so larger values indicate stronger coherence.\n    \"\"\"\n    if distance is None:\n        distance = base.pairwise_geometry_distance(episode)\n    work = np.asarray(distance, dtype=np.float64).copy()\n    np.fill_diagonal(work, np.inf)\n    nearest = np.argpartition(work, 3, axis=1)[:, :3]\n    best = float('inf')\n    for center in range(work.shape[0]):\n        subset = np.concatenate((np.asarray([center], dtype=np.int64), nearest[center]))\n        diameter = float(np.max(distance[np.ix_(subset, subset)]))\n        if diameter < best:\n            best = diameter\n    return -best\n'''


def replace_once(source: str, old: str, new: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f'Expected one occurrence, found {count}: {old[:100]!r}')
    return source.replace(old, new)


def derive_null(source: str) -> str:
    source = replace_once(
        source,
        'CROSS_FIT_SPLITS = 8\nREFERENCE_SIZE = 64\nK_NEIGHBOR = 2\nTOP_QUERY_EVENTS = 2\nEXPECTED_YEARS = (2020, 2022, 2024)',
        'EXPECTED_YEARS = (2026,)',
    )
    start = source.index('def crossfit_score(')
    end = source.index('\n\ndef main()', start)
    source = source[:start] + SCORE_FUNCTION + source[end:]
    replacements = {
        "if years != EXPECTED_YEARS:\n        raise RuntimeError(f'Expected untouched even years {EXPECTED_YEARS}, got {years}')":
            "if years != EXPECTED_YEARS:\n        raise RuntimeError(f'Expected untouched H1 2026 data {EXPECTED_YEARS}, got {years}')",
        "for year in years:\n        for sector in range(int(360 / SECTOR_WIDTH_DEG)):\n            factory.make(year, sector, stable_seed('evenyear-support', year, sector))\n            groups.append((year, sector))":
            "for year in years:\n        for sector in range(int(360 / SECTOR_WIDTH_DEG)):\n            try:\n                factory.make(year, sector, stable_seed('h1-2026-fourstar-support', year, sector))\n            except RuntimeError:\n                continue\n            groups.append((year, sector))\n    if len(groups) < 3:\n        raise RuntimeError(f'Only {len(groups)} supported H1 2026 sectors; need at least 3')",
        "stable_seed('evenyear-calibration-window', batch, year, sector, index)":
            "stable_seed('h1-2026-fourstar-null-calibration', batch, year, sector, index)",
        "crossfit_score(base, episode, ('calibration', batch, year, sector, index))":
            "fourstar_score(base, episode)",
        "stable_seed('evenyear-audit-window', batch, year, sector, index)":
            "stable_seed('h1-2026-fourstar-null-audit', batch, year, sector, index)",
        "score = crossfit_score(base, episode, ('audit', batch, year, sector, index))":
            "score = fourstar_score(base, episode)",
        "gates: dict[str, bool] = {}":
            "gates: dict[str, bool] = {'supported_groups_at_least_3': len(groups) >= 3}",
        "'PROCEED_TO_UNTOUCHED_EVENYEAR_POWER'": "'PROCEED_TO_H1_2026_FOURSTAR_POWER'",
        "'KILL_EMPIRICAL_WINDOW_NULL'": "'KILL_H1_2026_FOURSTAR_NULL'",
        "'cross_fit_splits': CROSS_FIT_SPLITS,\n            'reference_size': REFERENCE_SIZE,\n            'k_neighbor': K_NEIGHBOR,\n            'top_query_events': TOP_QUERY_EVENTS,":
            "'candidate': 'minimum center-plus-three-nearest four-point diameter',",
        "'# Untouched even-year empirical-window null audit'":
            "'# Untouched H1 2026 four-star empirical-window null audit'",
        "f'- untouched years: {years}'": "f'- untouched period: January-June 2026 ({years})'",
        "'frozen_evenyear_empirical_null_base'": "'frozen_h1_2026_fourstar_null_base'",
    }
    for old, new in replacements.items():
        source = replace_once(source, old, new)
    return source


def derive_power(source: str) -> str:
    source = replace_once(source, 'CROSS_FIT_SPLITS = 8\nREFERENCE_SIZE = 64\nK_NEIGHBOR = 2\nTOP_QUERY_EVENTS = 2\n', '')
    source = replace_once(source, 'EXPECTED_YEARS = (2020, 2022, 2024)', 'EXPECTED_YEARS = (2026,)')
    source = replace_once(source, "parser.add_argument('--stage0-result', required=True, type=Path)", "parser.add_argument('--null-result', required=True, type=Path)")
    start = source.index('def crossfit_score(')
    end = source.index('\n\ndef score_with_comparators', start)
    source = source[:start] + SCORE_FUNCTION + source[end:]
    source = re.sub(
        r"def score_with_comparators\(base: types\.ModuleType, episode: Any, key: object\) -> tuple\[float, float, float\]:\n    distance = base\.pairwise_geometry_distance\(episode\)\n    candidate = crossfit_score\(base, episode, key, distance\)",
        "def score_with_comparators(base: types.ModuleType, episode: Any) -> tuple[float, float, float]:\n    distance = base.pairwise_geometry_distance(episode)\n    candidate = fourstar_score(base, episode, distance)",
        source,
        count=1,
    )
    replacements = {
        "stage0 = json.loads(args.stage0_result.read_text(encoding='utf-8'))":
            "null_result = json.loads(args.null_result.read_text(encoding='utf-8'))",
        "if stage0.get('verdict') != 'PROCEED_TO_UNTOUCHED_EVENYEAR_POWER':\n        raise RuntimeError(f\"Untouched null gate did not pass: {stage0.get('verdict')}\")\n    if not stage0.get('gates') or not all(bool(value) for value in stage0['gates'].values()):\n        raise RuntimeError('Untouched null result does not contain an all-pass frozen gate set')":
            "if null_result.get('verdict') != 'PROCEED_TO_H1_2026_FOURSTAR_POWER':\n        raise RuntimeError(f\"Untouched null gate did not pass: {null_result.get('verdict')}\")\n    if not null_result.get('gates') or not all(bool(value) for value in null_result['gates'].values()):\n        raise RuntimeError('Untouched null result does not contain an all-pass frozen gate set')",
        "raise RuntimeError(f'Expected untouched even years {EXPECTED_YEARS}, got {observed_years}')":
            "raise RuntimeError(f'Expected untouched H1 2026 data {EXPECTED_YEARS}, got {observed_years}')",
        "stable_seed('evenyear-power-calibration-window', year, sector, index)":
            "stable_seed('h1-2026-fourstar-power-calibration', year, sector, index)",
        "stable_seed('evenyear-power-test-negative-window', year, sector, index)":
            "stable_seed('h1-2026-fourstar-power-negative', year, sector, index)",
        "stable_seed('evenyear-power-positive-window', shower, year, k, replicate)":
            "stable_seed('h1-2026-fourstar-power-positive', shower, year, k, replicate)",
        "'PROCEED_TO_EXTERNAL_WEAK_STREAM_AND_MULTIPLICITY_GATE'":
            "'PROCEED_TO_EXTERNAL_CONTROL_AND_CATALOG_ERROR_GATE'",
        "'KILL_EMPIRICAL_WINDOW_LCC_POWER'": "'KILL_H1_2026_FOURSTAR_POWER'",
        "'cross_fit_splits': CROSS_FIT_SPLITS,\n            'reference_size': REFERENCE_SIZE,\n            'k_neighbor': K_NEIGHBOR,\n            'top_query_events': TOP_QUERY_EVENTS,":
            "'candidate': 'minimum center-plus-three-nearest four-point diameter',",
        "'stage0_result_sha256': hashlib.sha256(args.stage0_result.read_bytes()).hexdigest(),":
            "'null_result_sha256': hashlib.sha256(args.null_result.read_bytes()).hexdigest(),",
        "'crossfit': 'evenyear-crossfit',": "'candidate': 'partition-invariant; no random split',",
        "'# Empirical-window local conformal coherence: untouched even-year power'":
            "'# Partition-invariant four-star coherence: untouched H1 2026 power'",
        "f'- confirmation years: {\", \".join(str(year) for year in EXPECTED_YEARS)}'":
            "f'- confirmation period: January-June 2026 ({\", \".join(str(year) for year in EXPECTED_YEARS)})'",
        "'EVENYEAR_LCC_POWER_REPORT.md'": "'H1_2026_FOURSTAR_POWER_REPORT.md'",
        "'evenyear_lcc_power.json'": "'h1_2026_fourstar_power.json'",
        "'frozen_real_shower_baseline_stage1'": "'frozen_h1_2026_fourstar_power_base'",
    }
    for old, new in replacements.items():
        source = replace_once(source, old, new)

    support_old = """    for year in EXPECTED_YEARS:\n        for sector in range(int(360 / SECTOR_WIDTH_DEG)):\n            empirical_factory.make(\n                year,\n                sector,\n                stable_seed('evenyear-power-support', year, sector),\n            )\n            supported_groups.append((year, sector))\n    expected_groups = len(EXPECTED_YEARS) * int(360 / SECTOR_WIDTH_DEG)\n    if len(supported_groups) != expected_groups:\n        raise RuntimeError(f'Only {len(supported_groups)} of {expected_groups} year-sectors are supported')\n"""
    support_new = """    for year in EXPECTED_YEARS:\n        for sector in range(int(360 / SECTOR_WIDTH_DEG)):\n            try:\n                empirical_factory.make(\n                    year,\n                    sector,\n                    stable_seed('h1-2026-fourstar-power-support', year, sector),\n                )\n            except RuntimeError:\n                continue\n            supported_groups.append((year, sector))\n    if len(supported_groups) < 3:\n        raise RuntimeError(f'Only {len(supported_groups)} supported H1 2026 sectors; need at least 3')\n"""
    source = replace_once(source, support_old, support_new)
    source = replace_once(
        source,
        """            score = crossfit_score(\n                base,\n                episode,\n                ('power-calibration', year, sector, index),\n            )\n""",
        "            score = fourstar_score(base, episode)\n",
    )
    source = replace_once(
        source,
        """            candidate, density, dbscan = score_with_comparators(\n                base,\n                episode,\n                ('power-test-negative', year, sector, index),\n            )\n""",
        "            candidate, density, dbscan = score_with_comparators(base, episode)\n",
    )
    source = replace_once(
        source,
        """                    candidate, density, dbscan = score_with_comparators(\n                        base,\n                        episode,\n                        ('power-positive', shower, year, k, replicate),\n                    )\n""",
        "                    candidate, density, dbscan = score_with_comparators(base, episode)\n",
    )
    source = replace_once(
        source,
        """    audit_years = tuple(int(year) for year in audit.get('configuration', {}).get('years', []))\n    if audit_years != EXPECTED_YEARS:\n        raise RuntimeError(f'Expected audit years {EXPECTED_YEARS}, got {audit_years}')\n""",
        """    audit_years = tuple(int(year) for year in audit.get('configuration', {}).get('years', []))\n    if audit_years != EXPECTED_YEARS:\n        raise RuntimeError(f'Expected audit years {EXPECTED_YEARS}, got {audit_years}')\n    audit_months = tuple(int(month) for month in audit.get('configuration', {}).get('months', []))\n    if audit_months != (1, 2, 3, 4, 5, 6):\n        raise RuntimeError(f'Expected frozen H1 months 1-6, got {audit_months}')\n""",
    )
    source = source.replace("'support': 'evenyear-power-support'", "'support': 'h1-2026-fourstar-power-support'")
    source = source.replace("'calibration': 'evenyear-power-calibration-window'", "'calibration': 'h1-2026-fourstar-power-calibration'")
    source = source.replace("'test_negative': 'evenyear-power-test-negative-window'", "'test_negative': 'h1-2026-fourstar-power-negative'")
    source = source.replace("'positive': 'evenyear-power-positive-window'", "'positive': 'h1-2026-fourstar-power-positive'")
    return source


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('null', 'power'))
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    source = args.input.read_text(encoding='utf-8')
    derived = derive_null(source) if args.mode == 'null' else derive_power(source)
    args.output.write_text(derived, encoding='utf-8')


if __name__ == '__main__':
    main()
