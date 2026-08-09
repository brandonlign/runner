#!/usr/bin/env bash
set -euo pipefail

: "${GH_TOKEN:?GH_TOKEN required}"
: "${BASE_SHA:?BASE_SHA required}"
: "${HEAD_SHA:?HEAD_SHA required}"

V3='orbittrace_core_halo_p13_literature/run_p13_matched_launcher_v3.sh'
GEN='orbittrace_support_safe_rank_p14/generate_matched_pretruth_direct_v3.py'
OUT='/tmp/p14_matched_pretruth_direct.sh'

test -f "$V3" -a -f "$GEN"
test "$(git hash-object "$V3")" = '1fb46484a51bb7d7edd60c865dcf5341550277a1'
python "$GEN" "$V3" "$OUT"
python -m py_compile "$GEN" orbittrace_support_safe_rank_p14/generate_matched_pretruth_direct_v2.py orbittrace_support_safe_rank_p14/generate_matched_pretruth_direct.py orbittrace_support_safe_rank_p14/apply_p12_snm_id_transport_from_v2.py orbittrace_support_safe_rank_p14/finalize_pretruth_checkpoint_p14_transport_v3.py orbittrace_core_halo_p13_literature/prepare_pretruth_panel_input_p14.py orbittrace_core_halo_p13_literature/finalize_pretruth_checkpoint_p14.py
bash -n "$OUT"
grep -F "LAUNCH_P14_MATCHED_PRETRUTH_DIRECT_V1" "$OUT"
grep -F "PASS_P14_DIRECT_ASSIGNMENT_IDS_FROZEN_CLUSTER_VALUES_UNREAD" "$OUT"
grep -F "PASS_P14_DIRECT_AUDITED_SNM_ID_TRANSPORT_ACTIVE" "$OUT"
grep -F "55a1efed550498d51b859ffec555797ba8473d7d8b5f20ad6831c5f15b43b415" "$OUT"
grep -F -- "--p14-rank-module /tmp/p14_support_safe_rank.py" "$OUT"
grep -F "PASS_P14_BOTH_MATCHED_CHECKPOINTS_FROZEN_BEFORE_TRUTH_OR_CLUSTER_VALUES" "$OUT"
if grep -Fq "OPEN TRUTH + COMPETITOR CLUSTER VALUES EXACTLY ONCE" "$OUT"; then
  echo 'posttruth stage survived P14 direct pretruth generation' >&2
  exit 1
fi
chmod +x "$OUT"
exec "$OUT"
