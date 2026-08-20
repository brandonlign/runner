#!/usr/bin/env bash
set -euo pipefail

ROOT="$PWD"
OUT="$ROOT/output/m2d-fixed4-drift-halo-sonotaco-v1"
IN="$ROOT/input/m2d-fixed4-drift-halo-sonotaco"
rm -rf "$OUT" "$IN" "$ROOT/frozen-v8" "$ROOT/frozen-seed" "$ROOT/baseline-sonotaco"
mkdir -p "$OUT/pretruth" "$OUT/truth" "$IN/rows" "$IN/ranker" "$IN/v8" "$IN/gmn"

echo '== pre-transfer source and activation firewall =='
test "$(git hash-object orbittrace_m2d_fixed4_drift_halo_v1/SONOTACO_TRANSFER_PROTOCOL.md)" = 'd4e925951a1a001bcb1b11e98378d9c92d845215'
test "$(git hash-object orbittrace_m2d_fixed4_drift_halo_v1/build_pretruth.py)" = '3d2d47c72f703a95713c4f17979f38a8aa3ac75c'
test "$(git hash-object orbittrace_m2d_fixed4_drift_halo_v1/build_sonotaco_pretruth.py)" = 'a280bb4ffc40b68069e6614cba1ea75b5226844f'
test "$(git hash-object orbittrace_m2d_fixed4_drift_halo_v1/evaluate_sonotaco_truth.py)" = '3d4bbfd979e503c62b972253ce3e8613f3d8c9df'
python -m py_compile orbittrace_m2d_fixed4_drift_halo_v1/build_pretruth.py orbittrace_m2d_fixed4_drift_halo_v1/build_sonotaco_pretruth.py orbittrace_m2d_fixed4_drift_halo_v1/evaluate_sonotaco_truth.py

python -m pip install --disable-pip-version-check --upgrade pip >/dev/null

# Exact baseline SonotaCo catalogue and helper.
git clone -q --no-checkout "https://github.com/${GITHUB_REPOSITORY}.git" baseline-sonotaco
git -C baseline-sonotaco fetch -q --no-tags --depth=1 origin a5dd599ac94ce3c2597755be6c40c945f95929f8
git -C baseline-sonotaco checkout -q FETCH_HEAD
test "$(git -C baseline-sonotaco hash-object orbittrace_internal_mass_sonotaco_development_v1/RANKED_PRETRUTH.json)" = 'e558023e9bb00f75e34a83b84e578012176ce721'
test "$(sha256sum baseline-sonotaco/orbittrace_internal_mass_sonotaco_development_v1/RANKED_PRETRUTH.json | cut -d' ' -f1)" = '9be0e77d650cabd94eccf0623f005705bb86e84793c76190b0065621631f2ecd'
test "$(git -C baseline-sonotaco hash-object orbittrace_internal_mass_sonotaco_development_v1/run_binding.py)" = 'b44e0222e08ae4e85f0ea9a91c95f7b9141f3fb9'

# Exact fixed4 seed and runtime used by the already-frozen GMN method.
git clone -q --no-checkout "https://github.com/${GITHUB_REPOSITORY}.git" frozen-seed
git -C frozen-seed fetch -q --no-tags --depth=1 origin agent/orbittrace-m2d-fixed4-consensus-core-v1
git -C frozen-seed checkout -q FETCH_HEAD
test "$(git -C frozen-seed hash-object orbittrace_m2d_fixed4_consensus_core_v1/build_pretruth.py)" = '140f21736ea6615fe111e02d91eaa99b19422da7'

git clone -q --no-checkout "https://github.com/${GITHUB_REPOSITORY}.git" frozen-v8
git -C frozen-v8 fetch -q --no-tags --depth=1 origin c9d6c44704013ba0c9430100e98a29a56b453304
git -C frozen-v8 checkout -q FETCH_HEAD
python -m pip install --disable-pip-version-check -r frozen-v8/ghoststream_fixed4_application/requirements.txt >/dev/null
python -m pip install --disable-pip-version-check --no-deps gmn-python-api==0.0.13 >/dev/null
python -m pip install --disable-pip-version-check 'numpy==2.1.3' 'scipy==1.14.1' 'scikit-learn==1.7.1' 'hdbscan==0.8.43' 'gudhi==3.12.0' >/dev/null

# Exact GMN PASS is a hard prerequisite. No SonotaCo scientific truth has been downloaded.
GH_TOKEN="${GH_TOKEN:?}" gh run download 32315704010 --repo "$GITHUB_REPOSITORY" --name orbittrace-m2d-fixed4-drift-halo-v1-binding --dir "$IN/gmn"
test "$(sha256sum "$IN/gmn/pretruth/M2D_FIXED4_DRIFT_HALO_V1_PRETRUTH.json" | cut -d' ' -f1)" = '3e0af5135a1c3562ccdc25be25f1ed89480b62f541c8c8d0de159dcb084ef9a8'
test "$(sha256sum "$IN/gmn/truth/M2D_FIXED4_DRIFT_HALO_V1_RESULT.json" | cut -d' ' -f1)" = 'a3903c2c2d1a6e46ea8400d12ca24b7570bad302da67ef489ce1f9a5c76fff63'
python - <<'PY'
import json
r=json.load(open('input/m2d-fixed4-drift-halo-sonotaco/gmn/truth/M2D_FIXED4_DRIFT_HALO_V1_RESULT.json'))
assert r['verdict']=='PASS_M2D_FIXED4_DRIFT_HALO_V1_GMN_DEVELOPMENT'
assert all(r['gates'].values())
print('GMN_PASS_AUTHORIZATION_VERIFIED')
PY

echo '== label-free SonotaCo inputs only =='
GH_TOKEN="$GH_TOKEN" gh run download 31354363306 --repo "$GITHUB_REPOSITORY" --name orbittrace-final-sonotaco-label-free-preparation-v2 --dir "$IN/rows"
GH_TOKEN="$GH_TOKEN" gh run download 31344632499 --repo "$GITHUB_REPOSITORY" --name orbittrace-active-urc-ranker-source-export-v1 --dir "$IN/ranker"
GH_TOKEN="$GH_TOKEN" gh run download 31217916558 --repo "$GITHUB_REPOSITORY" --name orbittrace-pooled-year-centroid-v8-development --dir "$IN/v8"
test "$(sha256sum "$IN/ranker/run_urc_union_ranker.py" | cut -d' ' -f1)" = 'dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
test "$(sha256sum "$IN/v8/pooled_year_centroid_v8_development.json" | cut -d' ' -f1)" = 'fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b'
test ! -e "$IN/truth"

export PYTHONPATH="$IN/ranker:.:orbittrace_recurrent_eom_hdbscan_v1:frozen-v8:frozen-v8/orbittrace_wavelet_catalogue_v3"

echo '== build and seal all 888 SonotaCo halos before truth =='
python -u orbittrace_m2d_fixed4_drift_halo_v1/build_sonotaco_pretruth.py \
  --rows-root "$IN/rows" \
  --parent-ranked baseline-sonotaco/orbittrace_internal_mass_sonotaco_development_v1/RANKED_PRETRUTH.json \
  --method-source orbittrace_m2d_fixed4_drift_halo_v1/build_pretruth.py \
  --seed-source frozen-seed/orbittrace_m2d_fixed4_consensus_core_v1/build_pretruth.py \
  --baseline-runner baseline-sonotaco/orbittrace_internal_mass_sonotaco_development_v1/run_binding.py \
  --quality-source "$IN/ranker/run_urc_union_ranker.py" \
  --support-source-parts frozen-v8/orbittrace_fixed4_support_wrapper_development/source_parts \
  --candidate-payload frozen-v8/sonotaco_fixed4_final_development/candidate.py.gz.b64 \
  --baseline-payload frozen-v8/real_shower_meta_stage0/run_baseline_ceiling.py.gz.b64 \
  --scorer-parts frozen-v8/mondrian_clique_development/source_parts_v2 \
  --v8-result-json "$IN/v8/pooled_year_centroid_v8_development.json" \
  --output "$OUT/pretruth/M2D_FIXED4_DRIFT_HALO_V1_SONOTACO_PRETRUTH.json"
sha256sum "$OUT/pretruth/M2D_FIXED4_DRIFT_HALO_V1_SONOTACO_PRETRUTH.json" > "$OUT/pretruth/PRETRUTH_SHA256.txt"
git rev-parse HEAD > "$OUT/pretruth/execution_commit.txt"
python - <<'PY'
import hashlib,json
p='output/m2d-fixed4-drift-halo-sonotaco-v1/pretruth/M2D_FIXED4_DRIFT_HALO_V1_SONOTACO_PRETRUTH.json'
r=json.load(open(p)); h=hashlib.sha256(open(p,'rb').read()).hexdigest()
assert r['truth_artifact_downloaded'] is False and r['truth_used'] is False and r['shower_labels_accessed'] is False
assert r['target_information_access'] is False and r['post_result_parameter_search'] is False
assert r['candidate_count']==888
print('SONOTACO_HALO_PRETRUTH_SEALED',h)
print(json.dumps(r['summary'],sort_keys=True))
PY

echo '== truth opens only after complete halo seal =='
mkdir -p "$IN/truth"
GH_TOKEN="$GH_TOKEN" gh run download 31405109267 --repo "$GITHUB_REPOSITORY" --name orbittrace-v15-exposed-matched-sonotaco-literature-result-v1 --dir "$IN/truth"

python -u orbittrace_m2d_fixed4_drift_halo_v1/evaluate_sonotaco_truth.py \
  --rows-root "$IN/rows" \
  --truth-root "$IN/truth" \
  --parent-ranked baseline-sonotaco/orbittrace_internal_mass_sonotaco_development_v1/RANKED_PRETRUTH.json \
  --halo-pretruth "$OUT/pretruth/M2D_FIXED4_DRIFT_HALO_V1_SONOTACO_PRETRUTH.json" \
  --baseline-runner baseline-sonotaco/orbittrace_internal_mass_sonotaco_development_v1/run_binding.py \
  --output "$OUT/truth/M2D_FIXED4_DRIFT_HALO_V1_SONOTACO_RESULT.json"
sha256sum "$OUT/truth/M2D_FIXED4_DRIFT_HALO_V1_SONOTACO_RESULT.json" > "$OUT/truth/RESULT_SHA256.txt"
python --version > "$OUT/truth/python_version.txt"
python -m pip freeze > "$OUT/truth/environment.txt"
python - <<'PY'
import hashlib,json
p='output/m2d-fixed4-drift-halo-sonotaco-v1/truth/M2D_FIXED4_DRIFT_HALO_V1_SONOTACO_RESULT.json'
r=json.load(open(p))
print('BINDING_VERDICT',r['verdict'])
print(json.dumps(r['routes'],indent=2,sort_keys=True))
print('RESULT_SHA256',hashlib.sha256(open(p,'rb').read()).hexdigest())
PY
