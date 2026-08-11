#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from orbittrace_v31_threeway_full_universe_refinement_diagnostic_v1 import diagnose as d


_original_require = d.require


def repaired_require(ok: bool, msg: str) -> None:
    # The frozen protocol requires both comparison strata to exist because its
    # PASS gate requires a defined risk ratio. An empty stratum is therefore a
    # scientific non-pass, not a provenance/runtime exception. Bypass only the
    # obsolete crash guard; every other require() remains exact and binding.
    if not ok and msg.endswith('empty group refinement stratum'):
        return
    _original_require(ok, msg)


def safe_stats(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    rec = sum(bool(r['recoverable']) for r in rows)
    return {
        'count': len(rows),
        'recoverable_count': rec,
        'recoverable_fraction': None if not rows else float(rec / len(rows)),
    }


def safe_compare(threeway: list[dict[str, Any]], joint_only: list[dict[str, Any]]) -> dict[str, Any]:
    a = safe_stats(threeway, 'threeway')
    b = safe_stats(joint_only, 'joint_only')
    pa = a['recoverable_fraction']
    pb = b['recoverable_fraction']
    if pa is None or pb is None:
        return {
            'threeway': a,
            'joint_only': b,
            'threeway_minus_joint_only_recoverable_fraction': None,
            'risk_ratio': None,
            'risk_ratio_infinite': False,
            'risk_ratio_condition_pass': False,
            'direction_pass': False,
            'comparison_defined': False,
        }
    infinite = bool(pb == 0.0 and pa > 0.0)
    rr = None if pb == 0.0 else float(pa / pb)
    rr_pass = bool(infinite or (rr is not None and rr > 1.0))
    return {
        'threeway': a,
        'joint_only': b,
        'threeway_minus_joint_only_recoverable_fraction': float(pa - pb),
        'risk_ratio': rr,
        'risk_ratio_infinite': infinite,
        'risk_ratio_condition_pass': rr_pass,
        'direction_pass': bool(pa > pb and rr_pass),
        'comparison_defined': True,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--vector', type=Path, required=True)
    p.add_argument('--cross-result', type=Path, required=True)
    p.add_argument('--hdb-root', type=Path, required=True)
    p.add_argument('--truth-root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()

    d.require = repaired_require
    d.compare_strata = safe_compare
    return d.audit_vector(a.vector, a.cross_result, a.hdb_root, a.truth_root, a.output)


if __name__ == '__main__':
    raise SystemExit(main())
