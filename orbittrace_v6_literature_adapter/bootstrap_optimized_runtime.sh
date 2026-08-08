#!/usr/bin/env bash
set -euo pipefail

mkdir -p runtime
python orbittrace_wavelet_catalogue_v3/audit_development_source.py
cp /tmp/run_wavelet_catalogue_v3_development.py runtime/run_wavelet_catalogue_v3_development.py
echo 'ef3e69317af59fdac7a030edc77f742fc4772473d7f16b719b5d804cd4117f51  runtime/run_wavelet_catalogue_v3_development.py' | sha256sum -c -

cat orbittrace_v3_catalogue_v6/exact_parts/part*.b64 \
  | tr -d '\n\r' | base64 --decode | gzip --decompress \
  > runtime/run_v3_primary_catalogue_v6.frozen.py
echo 'a139802f328e0721a6b48b9b41e098660d03e0e218cec49f1d6251981a2828c9  runtime/run_v3_primary_catalogue_v6.frozen.py' | sha256sum -c -
python - <<'PY'
import hashlib
from pathlib import Path
frozen=Path('runtime/run_v3_primary_catalogue_v6.frozen.py')
repaired=Path('runtime/run_v3_primary_catalogue_v6.repaired.py')
original=frozen.read_text()
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
repaired.write_text(patched)
assert hashlib.sha256(original.encode()).hexdigest()=='a139802f328e0721a6b48b9b41e098660d03e0e218cec49f1d6251981a2828c9'
assert hashlib.sha256(patched.encode()).hexdigest()=='257aab9d0f4d710a1b62af6088cfb9c0939062018d44dbacd074b4e7898eaa24'
print('PASS_EXACT_TWO_LINE_V3_PRIMARY_REPAIR')
PY

test "$(git -C exact rev-parse HEAD)" = 'ffe8351b9ee8df4418fb4926fab782d66180e276'
test "$(git -C exact hash-object orbittrace_literature_matched_v8/run_exact_row_benchmark.py)" = '09beb3e22b661ed88b35c89fa96c716f42215c80'
test "$(git -C exact hash-object orbittrace_literature_matched_v8/run_exact_row_final.py)" = '3b2e34493be0f1353c65c817cbb2ffd532b9a1fb'
python - <<'PY'
from pathlib import Path
old='7dbb920532f7dc429a6cd5961d80d480c5ff53c0122cf6e9ec04638c0730ed60'
new='35f629b1dff4d04cdc13aa8224171ec1ab8e06b52836900d66ff978b5c235761'
source=Path('exact/orbittrace_literature_matched_v8/run_exact_row_benchmark.py').read_text()
wrapper=Path('exact/orbittrace_literature_matched_v8/run_exact_row_final.py').read_text()
assert source.count(old)==1 and source.count(new)==0
assert f'benchmark.ASSIGNMENT_SHA256["hdbscan"][2023] = "{new}"' in wrapper
patched=source.replace(old,new,1)
assert patched.replace(new,old,1)==source
Path('runtime/run_exact_row_blind_safe.py').write_text(patched)
print('PASS_BLIND_SAFE_HDBSCAN_2023_INPUT_DIGEST_CORRECTION')
PY

python -m py_compile \
  runtime/run_wavelet_catalogue_v3_development.py \
  runtime/run_v3_primary_catalogue_v6.repaired.py \
  runtime/run_exact_row_blind_safe.py \
  orbittrace_v6_literature_adapter/parallel_exact_rescore.py \
  orbittrace_v6_literature_adapter/prepare_id_manifest.py \
  orbittrace_v6_literature_adapter/run_pretruth_year.py \
  orbittrace_v6_literature_adapter/combine_pretruth.py \
  orbittrace_v6_literature_adapter/evaluate_frozen.py
sha256sum runtime/*.py > runtime/runtime_sha256.txt
echo PASS_OPTIMIZED_MATCHED_RUNTIME_BOOTSTRAP