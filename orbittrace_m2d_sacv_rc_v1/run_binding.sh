#!/usr/bin/env bash
set -euo pipefail
ROOT="$PWD"
OUT="$ROOT/output/m2d-sacv-rc-v1-gmn"
IN="$ROOT/input/m2d-sacv-rc-v1-gmn"
rm -rf "$OUT" "$IN" "$ROOT/local-trunk-src" "$ROOT/frozen-v8"
mkdir -p "$OUT/pretruth" "$OUT/truth" "$IN/fair" "$IN/internal" "$IN/ranker" "$IN/v8" "$IN/v3"

echo '== RC-v1 frozen source identities =='
test "$(git hash-object orbittrace_m2d_sacv_rc_v1/PROTOCOL.md)" = 'bae4ef77acddccc8956f04c269399b535c9955a2'
test "$(git hash-object orbittrace_m2d_sacv_rc_v1/build_pretruth.py)" = '5229c50eacb607db158271fc7199ccd626d8c2e5'
test "$(git hash-object orbittrace_m2d_sacv_rc_v1/evaluate_truth.py)" = '71712743c31ca59a8b5c8b02891e2cb53dffc419'
python -m py_compile orbittrace_m2d_sacv_rc_v1/build_pretruth.py orbittrace_m2d_sacv_rc_v1/evaluate_truth.py
python -m pip install --disable-pip-version-check --upgrade pip >/dev/null

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
git -C frozen-v8 show FETCH_HEAD:orbittrace_multi_anchor_energy_v3/multi_anchor_energy_v3.py > "$IN/v3/multi_anchor_energy_v3.py"
test "$(git hash-object "$IN/v3/multi_anchor_energy_v3.py")" = '2ba4835db23f8f623cdd28d0a4e6113b7954ecb2'
rm -f /tmp/run_wavelet_catalogue_v3_development.py
(cd frozen-v8 && python orbittrace_wavelet_catalogue_v3/audit_development_source.py >/dev/null && test "$(cat output/development_source_sha256.txt)" = 'ef3e69317af59fdac7a030edc77f742fc4772473d7f16b719b5d804cd4117f51')

echo '== immutable target-excluded inputs =='
GH_TOKEN="${GH_TOKEN:?}" gh run download 32268943692 --repo "$GITHUB_REPOSITORY" --name orbittrace-internal-mass-gmn-sparse-literature-fairness-v1-pretruth --dir "$IN/fair"
GH_TOKEN="$GH_TOKEN" gh run download 32041661731 --repo "$GITHUB_REPOSITORY" --name orbittrace-support-cut-bifiltration-internal-mass-v1 --dir "$IN/internal"
GH_TOKEN="$GH_TOKEN" gh run download 31344632499 --repo "$GITHUB_REPOSITORY" --name orbittrace-active-urc-ranker-source-export-v1 --dir "$IN/ranker"
GH_TOKEN="$GH_TOKEN" gh run download 31217916558 --repo "$GITHUB_REPOSITORY" --name orbittrace-pooled-year-centroid-v8-development --dir "$IN/v8"
test "$(sha256sum "$IN/fair/GMN_INTERNAL_MASS_SPARSE_LITERATURE_FAIRNESS_V1_PRETRUTH.json" | cut -d' ' -f1)" = '8b0f4629659c1bfd750747303ad04ff67355adf66d4dbe474ce7fba788f5bae5'
test "$(sha256sum "$IN/internal/SUPPORT_CUT_BIFILTRATION_INTERNAL_MASS_V1_PRELABEL.json" | cut -d' ' -f1)" = '7b1ddfcd32cd0b52321e3b3dfc614a88dd9b973f947c1d4d0de74fddf26b59cd'
test "$(sha256sum "$IN/ranker/run_urc_union_ranker.py" | cut -d' ' -f1)" = 'dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
test "$(sha256sum "$IN/v8/pooled_year_centroid_v8_development.json" | cut -d' ' -f1)" = 'fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b'
export PYTHONPATH="$IN/ranker:.:orbittrace_recurrent_eom_hdbscan_v1:$IN/v3:frozen-v8:frozen-v8/orbittrace_wavelet_catalogue_v3"

echo '== exact target-excluded GMN geometry =='
python -u local-trunk-src/orbittrace_recurrent_local_topomodal_trunk_v1/export_geometry.py \
  --parent-runner orbittrace_recurrent_eom_hdbscan_v1/run_development.py \
  --quality-source "$IN/ranker/run_urc_union_ranker.py" \
  --support-source-parts frozen-v8/orbittrace_fixed4_support_wrapper_development/source_parts \
  --candidate-payload frozen-v8/sonotaco_fixed4_final_development/candidate.py.gz.b64 \
  --baseline-payload frozen-v8/real_shower_meta_stage0/run_baseline_ceiling.py.gz.b64 \
  --scorer-parts frozen-v8/mondrian_clique_development/source_parts_v2 \
  --v8-result-json "$IN/v8/pooled_year_centroid_v8_development.json" \
  --output "$OUT/pretruth/GMN_LABEL_FREE_GEOMETRY.json"
test "$(sha256sum "$OUT/pretruth/GMN_LABEL_FREE_GEOMETRY.json" | cut -d' ' -f1)" = '1fd5cd0577d88784845e0d367ef35491d6afb7caa78bb06fa05d72048daec384'

echo '== freeze recurrence-component extraction before truth =='
python -u orbittrace_m2d_sacv_rc_v1/build_pretruth.py \
  --fair-pretruth "$IN/fair/GMN_INTERNAL_MASS_SPARSE_LITERATURE_FAIRNESS_V1_PRETRUTH.json" \
  --geometry "$OUT/pretruth/GMN_LABEL_FREE_GEOMETRY.json" \
  --output "$OUT/pretruth/M2D_SACV_RC_V1_GMN_PRETRUTH.json"
sha256sum "$OUT/pretruth/M2D_SACV_RC_V1_GMN_PRETRUTH.json" > "$OUT/pretruth/PRETRUTH_SHA256.txt"
git rev-parse HEAD > "$OUT/pretruth/execution_commit.txt"
python - <<'PY'
import hashlib,json
p='output/m2d-sacv-rc-v1-gmn/pretruth/M2D_SACV_RC_V1_GMN_PRETRUTH.json';r=json.load(open(p));assert not r['shower_truth_used'] and not r['target_information_access'] and not r['target_region_events_accessed'] and not r['post_result_parameter_search'];print('RC_V1_PRETRUTH_SEALED',hashlib.sha256(open(p,'rb').read()).hexdigest());print(json.dumps(r['summary'],sort_keys=True))
PY
rm -f "$OUT/pretruth/GMN_LABEL_FREE_GEOMETRY.json"

echo '== truth evaluation after full seal =='
python -u orbittrace_m2d_sacv_rc_v1/evaluate_truth.py \
  --fair-pretruth "$IN/fair/GMN_INTERNAL_MASS_SPARSE_LITERATURE_FAIRNESS_V1_PRETRUTH.json" \
  --rc-pretruth "$OUT/pretruth/M2D_SACV_RC_V1_GMN_PRETRUTH.json" \
  --internal-prelabel "$IN/internal/SUPPORT_CUT_BIFILTRATION_INTERNAL_MASS_V1_PRELABEL.json" \
  --quality-source "$IN/ranker/run_urc_union_ranker.py" \
  --support-source-parts frozen-v8/orbittrace_fixed4_support_wrapper_development/source_parts \
  --candidate-payload frozen-v8/sonotaco_fixed4_final_development/candidate.py.gz.b64 \
  --baseline-payload frozen-v8/real_shower_meta_stage0/run_baseline_ceiling.py.gz.b64 \
  --scorer-parts frozen-v8/mondrian_clique_development/source_parts_v2 \
  --v8-result-json "$IN/v8/pooled_year_centroid_v8_development.json" \
  --output "$OUT/truth/M2D_SACV_RC_V1_GMN_RESULT.json"
sha256sum "$OUT/truth/M2D_SACV_RC_V1_GMN_RESULT.json" > "$OUT/truth/RESULT_SHA256.txt"
python --version > "$OUT/truth/python_version.txt"
python -m pip freeze > "$OUT/truth/environment.txt"
python - <<'PY'
import hashlib,json
p='output/m2d-sacv-rc-v1-gmn/truth/M2D_SACV_RC_V1_GMN_RESULT.json';r=json.load(open(p));print('BINDING_VERDICT',r['verdict']);print(json.dumps(r['aggregates'],indent=2,sort_keys=True));print('RESULT_SHA256',hashlib.sha256(open(p,'rb').read()).hexdigest())
PY
