from __future__ import annotations

import json
import sys
from pathlib import Path

import orbittrace_m2d_sacv_dual_output_core_v1.evaluate_truth as base

ROLE = 'TARGET_EXCLUDED_SACV_PRIMARY_PLUS_TOPOMODAL_TRUNK_RECURRENT_CORE_FROZEN_BEFORE_SHOWER_TRUTH'
SCHEMA = 'ORBITTRACE_M2D_SACV_TOPOMODAL_TRUNK_CORE_V1_GMN_RESULT'
VERDICT_MAP = {
    'FAIL_M2D_SACV_DUAL_OUTPUT_CORE_V1_PRIMARY_INTEGRITY': 'FAIL_M2D_SACV_TOPOMODAL_TRUNK_CORE_V1_PRIMARY_INTEGRITY',
    'POWER_INCONCLUSIVE_M2D_SACV_DUAL_OUTPUT_CORE_V1_GMN_DEVELOPMENT': 'POWER_INCONCLUSIVE_M2D_SACV_TOPOMODAL_TRUNK_CORE_V1_GMN_DEVELOPMENT',
    'FAIL_M2D_SACV_DUAL_OUTPUT_CORE_V1_GMN_DEVELOPMENT': 'FAIL_M2D_SACV_TOPOMODAL_TRUNK_CORE_V1_GMN_DEVELOPMENT',
    'PASS_M2D_SACV_DUAL_OUTPUT_CORE_V1_GMN_DEVELOPMENT': 'PASS_M2D_SACV_TOPOMODAL_TRUNK_CORE_V1_GMN_DEVELOPMENT',
}


def output_path() -> Path:
    if '--output' not in sys.argv:
        raise RuntimeError('missing --output')
    i = sys.argv.index('--output')
    if i + 1 >= len(sys.argv):
        raise RuntimeError('missing output value')
    return Path(sys.argv[i + 1])


def main() -> int:
    # Reuse the exact #1418 hidden-truth evaluation and all of its primary/core
    # gates byte-for-byte. Only the prospective pretruth role/schema are rebound.
    base.DUAL_ROLE = ROLE
    base.DUAL_SCHEMA = SCHEMA
    rc = base.main()
    p = output_path()
    r = json.loads(p.read_text())
    old = str(r['verdict'])
    if old not in VERDICT_MAP:
        raise RuntimeError(f'unexpected inherited verdict {old}')
    r['verdict'] = VERDICT_MAP[old]
    r['schema'] = SCHEMA
    r['core_kind'] = 'topomodal_trunk_of_frozen_selected_recurrence_component'
    r['core_gates_inherited_unchanged_from_1418'] = True
    p.write_text(json.dumps(r, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({'verdict': r['verdict'], 'inherited_1418_verdict': old, 'result_sha256': base.ev.sha(p)}, indent=2, sort_keys=True))
    return rc


if __name__ == '__main__':
    raise SystemExit(main())
