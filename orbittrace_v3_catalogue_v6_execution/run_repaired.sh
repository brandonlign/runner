#!/usr/bin/env bash
set -euo pipefail

mkdir -p frozen-v6/input/fixed4 frozen-v6/output
cd frozen-v6

python orbittrace_wavelet_catalogue_v3/audit_development_source.py
echo 'ef3e69317af59fdac7a030edc77f742fc4772473d7f16b719b5d804cd4117f51  /tmp/run_wavelet_catalogue_v3_development.py' | sha256sum -c -

cat orbittrace_v3_catalogue_v6/exact_parts/part*.b64 \
  | tr -d '\n\r' \
  | base64 --decode \
  | gzip --decompress \
  > /tmp/run_v3_primary_catalogue_v6.frozen.py
echo 'a139802f328e0721a6b48b9b41e098660d03e0e218cec49f1d6251981a2828c9  /tmp/run_v3_primary_catalogue_v6.frozen.py' | sha256sum -c -

python - <<'PY'
import ast
import hashlib
from pathlib import Path

frozen = Path('/tmp/run_v3_primary_catalogue_v6.frozen.py')
repaired = Path('/tmp/run_v3_primary_catalogue_v6.repaired.py')
original = frozen.read_text()
before = '''    primary_capped = cap_anchor_track(list(primary_by_anchor.values()), "v3")
    rescue_capped = cap_anchor_track(list(rescue_by_anchor.values()), "fixed4_rescue")
    capped = primary_capped + rescue_capped

    components = primary_components + rescue_components
'''
after = '''    primary_capped = cap_anchor_track(list(primary_by_anchor.values()), "v3")
    rescue_capped = cap_anchor_track(list(rescue_by_anchor.values()), "fixed4_rescue")
    capped = primary_capped + rescue_capped

    primary_components = component_records_track_v6(old, year, primary_capped, event_lookup, base, "v3")
    rescue_components = component_records_track_v6(old, year, rescue_capped, event_lookup, base, "fixed4_rescue")
    components = primary_components + rescue_components
'''
assert original.count(before) == 1, original.count(before)
patched = original.replace(before, after, 1)
repaired.write_text(patched)
assert patched.count(after) == 1
reversed_text = patched.replace(after, before, 1)
assert reversed_text == original
assert hashlib.sha256(reversed_text.encode()).hexdigest() == 'a139802f328e0721a6b48b9b41e098660d03e0e218cec49f1d6251981a2828c9'

tree = ast.parse(patched)
scan = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'scan_year_v6')
stores = {}
for node in ast.walk(scan):
    if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
        stores.setdefault(node.id, []).append(node.lineno)
assert len(stores.get('primary_components', [])) == 1
assert len(stores.get('rescue_components', [])) == 1

added = [line for line in patched.splitlines() if line not in original.splitlines()]
assert added == [
    '    primary_components = component_records_track_v6(old, year, primary_capped, event_lookup, base, "v3")',
    '    rescue_components = component_records_track_v6(old, year, rescue_capped, event_lookup, base, "fixed4_rescue")',
], added
print('REPAIRED_SOURCE_SHA256=' + hashlib.sha256(patched.encode()).hexdigest())
print('PASS_V6_EXACT_TWO_LINE_COMPONENT_REPAIR')
PY

python -m py_compile \
  /tmp/run_wavelet_catalogue_v3_development.py \
  /tmp/run_v3_primary_catalogue_v6.repaired.py \
  orbittrace_multi_anchor_energy_v3/multi_anchor_energy_v3.py

test "$(git hash-object orbittrace_multi_anchor_energy_v3/multi_anchor_energy_v3.py)" = "2ba4835db23f8f623cdd28d0a4e6113b7954ecb2"
sha256sum /tmp/run_v3_primary_catalogue_v6.frozen.py /tmp/run_v3_primary_catalogue_v6.repaired.py > output/v6_execution_source_sha256.txt
echo 'SOURCE_AUDIT_PR=490' >> output/v6_execution_source_sha256.txt
echo 'SOURCE_AUDIT_RUN=31270057662' >> output/v6_execution_source_sha256.txt

gh run download 31106001133 \
  --repo "$GITHUB_REPOSITORY" \
  --name orbittrace-fixed4-support-normalized-wrapper-development \
  --dir input/fixed4

test -f input/fixed4/orbittrace_fixed4_support_wrapper_development.json
python - <<'PY'
import json
from pathlib import Path
result = json.loads(Path('input/fixed4/orbittrace_fixed4_support_wrapper_development.json').read_text())
assert result['verdict'] == 'FAIL_SUPPORT_NORMALIZED_WRAPPER_DEVELOPMENT'
baseline = result['development']['panel_evaluations']['development']['metrics']['persistence']
assert baseline['recovered_at_100'] == 61
assert baseline['qualified_matches'] == 90
assert abs(baseline['top100_dominant_precision'] - 0.6809376504699393) < 1e-15
print('PASS_V6_FIXED4_BASELINE_GUARD')
PY

export PYTHONPATH="orbittrace_wavelet_catalogue_v3:orbittrace_multi_anchor_energy_v3:/tmp"
export PYTHONUNBUFFERED=1
python -u /tmp/run_v3_primary_catalogue_v6.repaired.py \
  --base-runner /tmp/run_wavelet_catalogue_v3_development.py \
  --support-source-parts orbittrace_fixed4_support_wrapper_development/source_parts \
  --candidate-payload sonotaco_fixed4_final_development/candidate.py.gz.b64 \
  --baseline-payload real_shower_meta_stage0/run_baseline_ceiling.py.gz.b64 \
  --scorer-parts mondrian_clique_development/source_parts_v2 \
  --fixed4-baseline-json input/fixed4/orbittrace_fixed4_support_wrapper_development.json \
  --output output &
pid=$!
start=$(date +%s)
while kill -0 "$pid" 2>/dev/null; do
  sleep 60
  if kill -0 "$pid" 2>/dev/null; then
    now=$(date +%s)
    elapsed=$((now-start))
    echo "V6_HEARTBEAT elapsed_seconds=$elapsed"
    ps -p "$pid" -o pid=,etime=,%cpu=,%mem=,rss=,vsz= || true
  fi
done
wait "$pid"

cat output/V3_PRIMARY_CATALOGUE_V6_DEVELOPMENT.md
python - <<'PY'
import json
from pathlib import Path
result = json.loads(Path('output/v3_primary_catalogue_v6_development.json').read_text())
assert result['verdict'] in {'PASS_V3_PRIMARY_CATALOGUE_V6_DEVELOPMENT','FAIL_V3_PRIMARY_CATALOGUE_V6_DEVELOPMENT'}
config = result['configuration']
assert config['years'] == [2022, 2023]
assert config['blind_exclusion'] == [20.0, 55.0]
assert config['primary_alpha'] == 0.05
assert config['rescue_queue'] == 'fixed4 p <= 1/129; never inserted into v3 primary ranking'
assert all(a['proposal_cap_per_window'] == 512 for a in result['year_audits'])
assert all(a['max_primary_proposals_per_year'] == 36864 for a in result['year_audits'])
print('ORBITTRACE_V6_RESULT_BEGIN')
print(json.dumps({
    'verdict': result['verdict'],
    'evaluation': {k: v for k, v in result['evaluation'].items() if k != 'per_label'},
    'gates': result['gates'],
    'year_audits': result['year_audits'],
}, indent=2))
print('ORBITTRACE_V6_RESULT_END')
PY
