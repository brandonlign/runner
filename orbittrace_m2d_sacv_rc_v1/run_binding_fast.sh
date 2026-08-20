#!/usr/bin/env bash
set -euo pipefail
test "$(git hash-object orbittrace_m2d_sacv_rc_v1/build_pretruth_fast.py)" = '8206d667b6cd9c95da1ff8cc0a3bedf8082d42c6'
python -m py_compile orbittrace_m2d_sacv_rc_v1/build_pretruth_fast.py
cp orbittrace_m2d_sacv_rc_v1/run_binding.sh /tmp/rc-run-binding-fast.sh
sed -i 's#python -u orbittrace_m2d_sacv_rc_v1/build_pretruth.py \\#python -u orbittrace_m2d_sacv_rc_v1/build_pretruth_fast.py \\#' /tmp/rc-run-binding-fast.sh
grep -F 'python -u orbittrace_m2d_sacv_rc_v1/build_pretruth_fast.py \' /tmp/rc-run-binding-fast.sh >/dev/null
bash /tmp/rc-run-binding-fast.sh
