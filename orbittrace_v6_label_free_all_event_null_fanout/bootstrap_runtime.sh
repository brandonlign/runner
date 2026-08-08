#!/usr/bin/env bash
set -euo pipefail

test -d execution
test -d frozen-v6

cd execution
python orbittrace_wavelet_catalogue_v3/audit_development_source.py
echo 'ef3e69317af59fdac7a030edc77f742fc4772473d7f16b719b5d804cd4117f51  /tmp/run_wavelet_catalogue_v3_development.py' | sha256sum -c -
test "$(git hash-object orbittrace_v6_label_free_all_event_null/run_development.py)" = 'd91a1bb22361536c770a8c3786e598586d89b70e'
python -m py_compile orbittrace_v6_label_free_all_event_null/run_development.py orbittrace_v6_label_free_all_event_null/parallel_exact_rescore.py orbittrace_v6_label_free_all_event_null_fanout/*.py
cd ..

cat frozen-v6/orbittrace_v3_catalogue_v6/exact_parts/part*.b64 \
  | tr -d '\n\r' | base64 --decode | gzip --decompress \
  > /tmp/v6.frozen.py
echo 'a139802f328e0721a6b48b9b41e098660d03e0e218cec49f1d6251981a2828c9  /tmp/v6.frozen.py' | sha256sum -c -

PYTHONPATH=execution python - <<'PY'
from pathlib import Path
import hashlib
original=Path('/tmp/v6.frozen.py').read_text()
before='''    primary_capped = cap_anchor_track(list(primary_by_anchor.values()), "v3")
    rescue_capped = cap_anchor_track(list(rescue_by_anchor.values()), "fixed4_rescue")
    capped = primary_capped + rescue_capped

    components = primary_components + rescue_components
'''
after='''    primary_capped = cap_anchor_track(list(primary_by_anchor.values()), "v3")
    rescue_capped = cap_anchor_track(list(rescue_by_anchor.values()), "fixed4_rescue")
    capped = primary_capped + rescue_capped

    primary_components = component_records_track_v6(old, year, primary_capped, event_lookup, base, "v3")
    rescue_components = component_records_track_v6(old, year, rescue_capped, event_lookup, base, "fixed4_rescue")
    components = primary_components + rescue_components
'''
assert original.count(before)==1
patched=original.replace(before,after,1)
assert patched.replace(after,before,1)==original
Path('/tmp/v6.repaired.py').write_text(patched)
assert hashlib.sha256(patched.encode()).hexdigest()=='257aab9d0f4d710a1b62af6088cfb9c0939062018d44dbacd074b4e7898eaa24'
print('PASS_V6_LF_EXACT_RUNTIME_BOOTSTRAP')
PY
