#!/usr/bin/env bash
set -euo pipefail

ROOT="$PWD"
OUT="$ROOT/output/m2d-fixed4-drift-halo-v1"
IN="$ROOT/input/m2d-fixed4-drift-halo"
rm -rf "$OUT" "$IN" "$ROOT/local-trunk-src" "$ROOT/frozen-v8" "$ROOT/frozen-seed"
mkdir -p "$OUT/pretruth" "$OUT/truth" "$IN/fair" "$IN/internal" "$IN/ranker" "$IN/v8" "$IN/v3"

echo '== source firewall =='
test "$(git hash-object orbittrace_m2d_fixed4_drift_halo_v1/PROTOCOL.md)" = 'c11e82664d49f4d18ef974491b1696c3c8fd3454'
test "$(git hash-object orbittrace_m2d_fixed4_drift_halo_v1/build_pretruth.py)" = '3d2d47c72f703a95713c4f17979f38a8aa3ac75c'
test "$(git hash-object orbittrace_m2d_fixed4_drift_halo_v1/evaluate_truth.py)" = 'c80c71b9ec72e9fbb778cb2393a9c9a085779f61'
test "$(git hash-object orbittrace_topomodal_hierarchy_scale_v1/run_diagnostic.py)" = 'c1efa8da34dea140726a4c2fe4943eb29a304538'
python -m py_compile orbittrace_m2d_fixed4_drift_halo_v1/build_pretruth.py orbittrace_m2d_fixed4_drift_halo_v1/evaluate_truth.py

python -m pip install --disable-pip-version-check --upgrade pip >/dev/null

git clone -q --depth 1 --branch agent/orbittrace-recurrent-local-topomodal-trunk-v1 "https://github.com/${GITHUB_REPOSITORY}.git" local-trunk-src
test "$(git -C local-trunk-src hash-object orbittrace_recurrent_local_topomodal_trunk_v1/export_geometry.py)" = '32abfb3e68520cfdc83585a88731fa3982900cde'

git clone -q --no-checkout "https://github.com/${GITHUB_REPOSITORY}.git" frozen-v8
git -C frozen-v8 fetch -q --no-tags --depth=1 origin c9d6c44704013ba0c9430100e98a29a56b453304
git -C frozen-v8 checkout -q FETCH_HEAD
test "$(git -C frozen-v8 hash-object orbittrace_wavelet_catalogue_v3/wavelet_episode_comparator.py)" = '493fcc7f2d2cc75ee35acf17e142e7ce7c1e03e8'

# Freeze the exact previously tested fixed4 consensus seed generator by blob, not
# by mutable branch semantics. Only this seed source is imported by the new halo.
git clone -q --no-checkout "https://github.com/${GITHUB_REPOSITORY}.git" frozen-seed
git -C frozen-seed fetch -q --no-tags --depth=1 origin agent/orbittrace-m2d-fixed4-consensus-core-v1
git -C frozen-seed checkout -q FETCH_HEAD
test "$(git -C frozen-seed hash-object orbittrace_m2d_fixed4_consensus_core_v1/build_pretruth.py)" = '140f21736ea6615fe111e02d91eaa99b19422da7'

python -m pip install --disable-pip-version-check -r frozen-v8/ghoststream_fixed4_application/requirements.txt >/dev/null
python -m pip install --disable-pip-version-check --no-deps gmn-python-api==0.0.13 >/dev/null
python -m pip install --disable-pip-version-check 'numpy==2.1.3' 'scipy==1.14.1' 'scikit-learn==1.7.1' 'hdbscan==0.8.43' 'gudhi==3.12.0' >/dev/null

git -C frozen-v8 fetch -q --no-tags --depth=1 origin d8258581af143308495bd97bedcc142abbbd951a
git -C frozen-v8 show FETCH_HEAD:orbittrace_multi_anchor_energy_v3/multi_anchor_energy_v3.py > "$IN/v3/multi_anchor_energy_v3.py"
test "$(git hash-object "$IN/v3/multi_anchor_energy_v3.py")" = '2ba4835db23f8f623cdd28d0a4e6113b7954ecb2'
rm -f /tmp/run_wavelet_catalogue_v3_development.py
(cd frozen-v8 && python orbittrace_wavelet_catalogue_v3/audit_development_source.py >/dev/null && test "$(cat output/development_source_sha256.txt)" = 'ef3e69317af59fdac7a030edc77f742fc4772473d7f16b719b5d804cd4117f51')

echo '== immutable target-excluded inputs; no current known-shower truth yet =='
GH_TOKEN="${GH_TOKEN:?}" gh run download 32268943692 --repo "$GITHUB_REPOSITORY" --name orbittrace-internal-mass-gmn-sparse-literature-fairness-v1-pretruth --dir "$IN/fair"
GH_TOKEN="$GH_TOKEN" gh run download 32041661731 --repo "$GITHUB_REPOSITORY" --name orbittrace-support-cut-bifiltration-internal-mass-v1 --dir "$IN/internal"
GH_TOKEN="$GH_TOKEN" gh run download 31344632499 --repo "$GITHUB_REPOSITORY" --name orbittrace-active-urc-ranker-source-export-v1 --dir "$IN/ranker"
GH_TOKEN="$GH_TOKEN" gh run download 31217916558 --repo "$GITHUB_REPOSITORY" --name orbittrace-pooled-year-centroid-v8-development --dir "$IN/v8"

test "$(sha256sum "$IN/fair/GMN_INTERNAL_MASS_SPARSE_LITERATURE_FAIRNESS_V1_PRETRUTH.json" | cut -d' ' -f1)" = '8b0f4629659c1bfd750747303ad04ff67355adf66d4dbe474ce7fba788f5bae5'
test "$(sha256sum "$IN/internal/SUPPORT_CUT_BIFILTRATION_INTERNAL_MASS_V1_PRELABEL.json" | cut -d' ' -f1)" = '7b1ddfcd32cd0b52321e3b3dfc614a88dd9b973f947c1d4d0de74fddf26b59cd'
test "$(sha256sum "$IN/ranker/run_urc_union_ranker.py" | cut -d' ' -f1)" = 'dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
test "$(sha256sum "$IN/v8/pooled_year_centroid_v8_development.json" | cut -d' ' -f1)" = 'fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b'

export PYTHONPATH="$IN/ranker:.:orbittrace_recurrent_eom_hdbscan_v1:$IN/v3:frozen-v8:frozen-v8/orbittrace_wavelet_catalogue_v3"

echo '== label-free target-excluded geometry =='
python -u local-trunk-src/orbittrace_recurrent_local_topomodal_trunk_v1/export_geometry.py \
  --parent-runner orbittrace_recurrent_eom_hdbscan_v1/run_development.py \
  --quality-source "$IN/ranker/run_urc_union_ranker.py" \
  --support-source-parts frozen-v8/orbittrace_fixed4_support_wrapper_development/source_parts \
  --candidate-payload frozen-v8/sonotaco_fixed4_final_development/candidate.py.gz.b64 \
  --baseline-payload frozen-v8/real_shower_meta_stage0/run_baseline_ceiling.py.gz.b64 \
  --scorer-parts frozen-v8/mondrian_clique_development/source_parts_v2 \
  --v8-result-json "$IN/v8/pooled_year_centroid_v8_development.json" \
  --output "$OUT/pretruth/GMN_LABEL_FREE_GEOMETRY.json"
sha256sum "$OUT/pretruth/GMN_LABEL_FREE_GEOMETRY.json" > "$OUT/pretruth/GEOMETRY_SHA256.txt"

echo '== build and seal seed + drift model + OAS halo for every candidate before truth =='
python -u orbittrace_m2d_fixed4_drift_halo_v1/build_pretruth.py \
  --fair-pretruth "$IN/fair/GMN_INTERNAL_MASS_SPARSE_LITERATURE_FAIRNESS_V1_PRETRUTH.json" \
  --geometry "$OUT/pretruth/GMN_LABEL_FREE_GEOMETRY.json" \
  --seed-source frozen-seed/orbittrace_m2d_fixed4_consensus_core_v1/build_pretruth.py \
  --quality-source "$IN/ranker/run_urc_union_ranker.py" \
  --support-source-parts frozen-v8/orbittrace_fixed4_support_wrapper_development/source_parts \
  --candidate-payload frozen-v8/sonotaco_fixed4_final_development/candidate.py.gz.b64 \
  --baseline-payload frozen-v8/real_shower_meta_stage0/run_baseline_ceiling.py.gz.b64 \
  --scorer-parts frozen-v8/mondrian_clique_development/source_parts_v2 \
  --v8-result-json "$IN/v8/pooled_year_centroid_v8_development.json" \
  --output "$OUT/pretruth/M2D_FIXED4_DRIFT_HALO_V1_PRETRUTH.json"
sha256sum "$OUT/pretruth/M2D_FIXED4_DRIFT_HALO_V1_PRETRUTH.json" > "$OUT/pretruth/PRETRUTH_SHA256.txt"
git rev-parse HEAD > "$OUT/pretruth/execution_commit.txt"
python - <<'PY'
import hashlib,json
p='output/m2d-fixed4-drift-halo-v1/pretruth/M2D_FIXED4_DRIFT_HALO_V1_PRETRUTH.json'
r=json.load(open(p)); h=hashlib.sha256(open(p,'rb').read()).hexdigest()
assert r['shower_truth_used'] is False and r['target_information_access'] is False and r['target_region_events_accessed'] is False
assert r['sonotaco_scientific_access'] is False and r['external_survey_scientific_access'] is False
assert r['post_result_parameter_search'] is False
print('PRETRUTH_SEALED_BEFORE_TRUTH',h)
print(json.dumps(r['overall_summary'],sort_keys=True))
PY

# Geometry is no longer needed. The evaluator only receives the frozen ID halo.
rm -f "$OUT/pretruth/GMN_LABEL_FREE_GEOMETRY.json"
test -s "$OUT/pretruth/PRETRUTH_SHA256.txt"

echo '== binding same-discovery hidden-truth evaluation =='
python -u orbittrace_m2d_fixed4_drift_halo_v1/evaluate_truth.py \
  --fair-pretruth "$IN/fair/GMN_INTERNAL_MASS_SPARSE_LITERATURE_FAIRNESS_V1_PRETRUTH.json" \
  --halo-pretruth "$OUT/pretruth/M2D_FIXED4_DRIFT_HALO_V1_PRETRUTH.json" \
  --internal-prelabel "$IN/internal/SUPPORT_CUT_BIFILTRATION_INTERNAL_MASS_V1_PRELABEL.json" \
  --parent-runner orbittrace_recurrent_eom_hdbscan_v1/run_development.py \
  --quality-source "$IN/ranker/run_urc_union_ranker.py" \
  --support-source-parts frozen-v8/orbittrace_fixed4_support_wrapper_development/source_parts \
  --candidate-payload frozen-v8/sonotaco_fixed4_final_development/candidate.py.gz.b64 \
  --baseline-payload frozen-v8/real_shower_meta_stage0/run_baseline_ceiling.py.gz.b64 \
  --scorer-parts frozen-v8/mondrian_clique_development/source_parts_v2 \
  --v8-result-json "$IN/v8/pooled_year_centroid_v8_development.json" \
  --output "$OUT/truth/M2D_FIXED4_DRIFT_HALO_V1_RESULT.json"
sha256sum "$OUT/truth/M2D_FIXED4_DRIFT_HALO_V1_RESULT.json" > "$OUT/truth/RESULT_SHA256.txt"
python --version > "$OUT/truth/python_version.txt"
python -m pip freeze > "$OUT/truth/environment.txt"
python - <<'PY'
import hashlib,json
p='output/m2d-fixed4-drift-halo-v1/truth/M2D_FIXED4_DRIFT_HALO_V1_RESULT.json'
r=json.load(open(p))
print('BINDING_VERDICT',r['verdict'])
for comp in ('sugar2017','hdbscan2025'):
 a=r['aggregates'][comp]['paired_same_discovery']
 print(comp,'paired',a)
 print(comp,'gates',r['aggregates'][comp]['gates'])
print('RESULT_SHA256',hashlib.sha256(open(p,'rb').read()).hexdigest())
PY
