#!/usr/bin/env bash
set -euo pipefail

ROOT="$PWD"
OUT="$ROOT/output/m2d-crossyear-recurrence-core-v1"
rm -rf "$OUT" "$ROOT/input/m2d-recurrence" "$ROOT/local-trunk-src" "$ROOT/frozen-v8"
mkdir -p "$OUT/pretruth" "$OUT/truth" "$ROOT/input/m2d-recurrence/fair" "$ROOT/input/m2d-recurrence/internal" "$ROOT/input/m2d-recurrence/ranker" "$ROOT/input/m2d-recurrence/v8" "$ROOT/input/m2d-recurrence/v3"

echo '== source firewall =='
test "$(git hash-object orbittrace_m2d_crossyear_recurrence_core_v1/PROTOCOL.md)" = '067b2868d898438a0b320b29d1c4c622115b7320'
test "$(git hash-object orbittrace_m2d_crossyear_recurrence_core_v1/build_pretruth.py)" = 'd3dde3ac8b0a1168a8b6d4632f5169ce631f7810'
test "$(git hash-object orbittrace_m2d_crossyear_recurrence_core_v1/evaluate_truth.py)" = '7b102ce826428cccdc860f455653dc7180530c2a'
test "$(git hash-object orbittrace_topomodal_hierarchy_scale_v1/run_diagnostic.py)" = 'c1efa8da34dea140726a4c2fe4943eb29a304538'
python -m py_compile orbittrace_m2d_crossyear_recurrence_core_v1/build_pretruth.py orbittrace_m2d_crossyear_recurrence_core_v1/evaluate_truth.py

python -m pip install --disable-pip-version-check --upgrade pip >/dev/null

# Exact source checkouts used by the already-binding PR #1377 workflow.
git clone -q --depth 1 --branch agent/orbittrace-recurrent-local-topomodal-trunk-v1 "https://github.com/${GITHUB_REPOSITORY}.git" local-trunk-src
test "$(git -C local-trunk-src hash-object orbittrace_recurrent_local_topomodal_trunk_v1/export_geometry.py)" = '32abfb3e68520cfdc83585a88731fa3982900cde'

git clone -q --no-checkout "https://github.com/${GITHUB_REPOSITORY}.git" frozen-v8
git -C frozen-v8 fetch -q --no-tags --depth=1 origin c9d6c44704013ba0c9430100e98a29a56b453304
git -C frozen-v8 checkout -q FETCH_HEAD
test "$(git -C frozen-v8 hash-object orbittrace_wavelet_catalogue_v3/wavelet_episode_comparator.py)" = '493fcc7f2d2cc75ee35acf17e142e7ce7c1e03e8'

python -m pip install --disable-pip-version-check -r frozen-v8/ghoststream_fixed4_application/requirements.txt >/dev/null
python -m pip install --disable-pip-version-check --no-deps gmn-python-api==0.0.13 >/dev/null
python -m pip install --disable-pip-version-check 'numpy==2.1.3' 'scipy==1.14.1' 'scikit-learn==1.7.1' 'hdbscan==0.8.43' 'gudhi==3.12.0' >/dev/null

git -C frozen-v8 fetch -q --no-tags --depth=1 origin d8258581af143308495bd97bedcc142abbbd951a
git -C frozen-v8 show FETCH_HEAD:orbittrace_multi_anchor_energy_v3/multi_anchor_energy_v3.py > input/m2d-recurrence/v3/multi_anchor_energy_v3.py
test "$(git hash-object input/m2d-recurrence/v3/multi_anchor_energy_v3.py)" = '2ba4835db23f8f623cdd28d0a4e6113b7954ecb2'
rm -f /tmp/run_wavelet_catalogue_v3_development.py
(cd frozen-v8 && python orbittrace_wavelet_catalogue_v3/audit_development_source.py >/dev/null && test "$(cat output/development_source_sha256.txt)" = 'ef3e69317af59fdac7a030edc77f742fc4772473d7f16b719b5d804cd4117f51')

echo '== immutable artifacts, still no current truth evaluation =='
GH_TOKEN="${GH_TOKEN:?}" gh run download 32268943692 --repo "$GITHUB_REPOSITORY" --name orbittrace-internal-mass-gmn-sparse-literature-fairness-v1-pretruth --dir input/m2d-recurrence/fair
GH_TOKEN="$GH_TOKEN" gh run download 32041661731 --repo "$GITHUB_REPOSITORY" --name orbittrace-support-cut-bifiltration-internal-mass-v1 --dir input/m2d-recurrence/internal
GH_TOKEN="$GH_TOKEN" gh run download 31344632499 --repo "$GITHUB_REPOSITORY" --name orbittrace-active-urc-ranker-source-export-v1 --dir input/m2d-recurrence/ranker
GH_TOKEN="$GH_TOKEN" gh run download 31217916558 --repo "$GITHUB_REPOSITORY" --name orbittrace-pooled-year-centroid-v8-development --dir input/m2d-recurrence/v8

test "$(sha256sum input/m2d-recurrence/fair/GMN_INTERNAL_MASS_SPARSE_LITERATURE_FAIRNESS_V1_PRETRUTH.json | cut -d' ' -f1)" = '8b0f4629659c1bfd750747303ad04ff67355adf66d4dbe474ce7fba788f5bae5'
test "$(sha256sum input/m2d-recurrence/internal/SUPPORT_CUT_BIFILTRATION_INTERNAL_MASS_V1_PRELABEL.json | cut -d' ' -f1)" = '7b1ddfcd32cd0b52321e3b3dfc614a88dd9b973f947c1d4d0de74fddf26b59cd'
test "$(sha256sum input/m2d-recurrence/ranker/run_urc_union_ranker.py | cut -d' ' -f1)" = 'dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
test "$(sha256sum input/m2d-recurrence/v8/pooled_year_centroid_v8_development.json | cut -d' ' -f1)" = 'fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b'

echo '== label-free target-excluded geometry =='
export PYTHONPATH="input/m2d-recurrence/ranker:.:orbittrace_recurrent_eom_hdbscan_v1:input/m2d-recurrence/v3:frozen-v8:frozen-v8/orbittrace_wavelet_catalogue_v3"
python -u local-trunk-src/orbittrace_recurrent_local_topomodal_trunk_v1/export_geometry.py \
  --parent-runner orbittrace_recurrent_eom_hdbscan_v1/run_development.py \
  --quality-source input/m2d-recurrence/ranker/run_urc_union_ranker.py \
  --support-source-parts frozen-v8/orbittrace_fixed4_support_wrapper_development/source_parts \
  --candidate-payload frozen-v8/sonotaco_fixed4_final_development/candidate.py.gz.b64 \
  --baseline-payload frozen-v8/real_shower_meta_stage0/run_baseline_ceiling.py.gz.b64 \
  --scorer-parts frozen-v8/mondrian_clique_development/source_parts_v2 \
  --v8-result-json input/m2d-recurrence/v8/pooled_year_centroid_v8_development.json \
  --output "$OUT/pretruth/GMN_LABEL_FREE_GEOMETRY.json"
sha256sum "$OUT/pretruth/GMN_LABEL_FREE_GEOMETRY.json" > "$OUT/pretruth/GEOMETRY_SHA256.txt"

echo '== build and cryptographically seal complete core catalogue before truth =='
python -u orbittrace_m2d_crossyear_recurrence_core_v1/build_pretruth.py \
  --fair-pretruth input/m2d-recurrence/fair/GMN_INTERNAL_MASS_SPARSE_LITERATURE_FAIRNESS_V1_PRETRUTH.json \
  --geometry "$OUT/pretruth/GMN_LABEL_FREE_GEOMETRY.json" \
  --structural-source orbittrace_topomodal_hierarchy_scale_v1/run_diagnostic.py \
  --output "$OUT/pretruth/M2D_CROSSYEAR_RECURRENCE_CORE_V1_PRETRUTH.json"
sha256sum "$OUT/pretruth/M2D_CROSSYEAR_RECURRENCE_CORE_V1_PRETRUTH.json" > "$OUT/pretruth/PRETRUTH_SHA256.txt"
git rev-parse HEAD > "$OUT/pretruth/execution_commit.txt"
python - <<'PY'
import json,hashlib
p='output/m2d-crossyear-recurrence-core-v1/pretruth/M2D_CROSSYEAR_RECURRENCE_CORE_V1_PRETRUTH.json'
r=json.load(open(p)); h=hashlib.sha256(open(p,'rb').read()).hexdigest()
assert r['shower_truth_used'] is False and r['target_information_access'] is False and r['target_region_events_accessed'] is False
assert r['sonotaco_scientific_access'] is False and r['external_survey_scientific_access'] is False
print('PRETRUTH_SEALED_BEFORE_TRUTH',h)
print(json.dumps(r['overall_summary'],sort_keys=True))
PY

# Remove the large geometry before truth; the evaluator receives only frozen IDs.
rm -f "$OUT/pretruth/GMN_LABEL_FREE_GEOMETRY.json"
test -s "$OUT/pretruth/PRETRUTH_SHA256.txt"

echo '== binding hidden-truth evaluation; detector/core construction is now over =='
python -u orbittrace_m2d_crossyear_recurrence_core_v1/evaluate_truth.py \
  --fair-pretruth input/m2d-recurrence/fair/GMN_INTERNAL_MASS_SPARSE_LITERATURE_FAIRNESS_V1_PRETRUTH.json \
  --core-pretruth "$OUT/pretruth/M2D_CROSSYEAR_RECURRENCE_CORE_V1_PRETRUTH.json" \
  --internal-prelabel input/m2d-recurrence/internal/SUPPORT_CUT_BIFILTRATION_INTERNAL_MASS_V1_PRELABEL.json \
  --parent-runner orbittrace_recurrent_eom_hdbscan_v1/run_development.py \
  --quality-source input/m2d-recurrence/ranker/run_urc_union_ranker.py \
  --support-source-parts frozen-v8/orbittrace_fixed4_support_wrapper_development/source_parts \
  --candidate-payload frozen-v8/sonotaco_fixed4_final_development/candidate.py.gz.b64 \
  --baseline-payload frozen-v8/real_shower_meta_stage0/run_baseline_ceiling.py.gz.b64 \
  --scorer-parts frozen-v8/mondrian_clique_development/source_parts_v2 \
  --v8-result-json input/m2d-recurrence/v8/pooled_year_centroid_v8_development.json \
  --output "$OUT/truth/M2D_CROSSYEAR_RECURRENCE_CORE_V1_RESULT.json"
sha256sum "$OUT/truth/M2D_CROSSYEAR_RECURRENCE_CORE_V1_RESULT.json" > "$OUT/truth/RESULT_SHA256.txt"
python --version > "$OUT/truth/python_version.txt"
python -m pip freeze > "$OUT/truth/environment.txt"

python - <<'PY'
import json,hashlib
p='output/m2d-crossyear-recurrence-core-v1/truth/M2D_CROSSYEAR_RECURRENCE_CORE_V1_RESULT.json'
r=json.load(open(p))
print('BINDING_VERDICT',r['verdict'])
for comp in ('sugar2017','hdbscan2025'):
 a=r['aggregates'][comp]
 print(comp,'F1',a['envelope']['mean_macro_f1'],'->',a['core']['mean_macro_f1'],'precision',a['envelope']['mean_macro_precision'],'->',a['core']['mean_macro_precision'],'recovered',a['envelope']['total_recovered_f1_gt_05'],'->',a['core']['total_recovered_f1_gt_05'],'pairedF1',a['paired']['parent_mean_f1'],'->',a['paired']['core_mean_f1'])
print('RESULT_SHA256',hashlib.sha256(open(p,'rb').read()).hexdigest())
PY
