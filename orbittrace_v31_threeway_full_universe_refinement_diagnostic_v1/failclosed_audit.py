#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from orbittrace_v31_threeway_full_universe_refinement_diagnostic_v1 import diagnose as d


def _stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    rec = sum(bool(r['recoverable']) for r in rows)
    return {
        'count': len(rows),
        'recoverable_count': rec,
        'recoverable_fraction': None if not rows else float(rec / len(rows)),
    }


def failclosed_compare_strata(threeway: list[dict[str, Any]], joint_only: list[dict[str, Any]]) -> dict[str, Any]:
    if threeway and joint_only:
        out = d.compare_strata(threeway, joint_only)
        out['comparison_defined'] = True
        return out
    return {
        'threeway': _stats(threeway),
        'joint_only': _stats(joint_only),
        'threeway_minus_joint_only_recoverable_fraction': None,
        'risk_ratio': None,
        'risk_ratio_infinite': False,
        'risk_ratio_condition_pass': False,
        'direction_pass': False,
        'comparison_defined': False,
        'fail_closed_reason': 'required preregistered comparison stratum is empty',
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--vector', type=Path, required=True)
    p.add_argument('--cross-result', type=Path, required=True)
    p.add_argument('--hdb-root', type=Path, required=True)
    p.add_argument('--truth-root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    d.compare_strata = failclosed_compare_strata
    return d.audit_vector(a.vector, a.cross_result, a.hdb_root, a.truth_root, a.output)


if __name__ == '__main__':
    raise SystemExit(main())
