#!/usr/bin/env bash
set -euo pipefail
ROOT="$PWD"
OUT="$ROOT/output/m2d-sacv-pareto-pair-catalogue-v1-gmn"
IN="$ROOT/input/m2d-sacv-pareto-pair-catalogue-v1-gmn"
rm -rf "$OUT" "$IN" "$ROOT/frozen-v8" "$ROOT/local-trunk-src"
mkdir -p "$OUT/pretruth" "$OUT/truth" "$IN/fair" "$IN/ranker" "$IN/v8" "$IN/v3" "$IN/sacvbase" "$IN/sacvsource"

# Frozen scientific source. This runner is transport/provenance only.
test "$(git hash-object orbittrace_m2d_sacv_pareto_pair_catalogue_v1/PROTOCOL.md)" = '67dcab7a002f945170124a5355c62ffb21c896ed'
test "$(git hash-object orbittrace_m2d_sacv_pareto_pair_catalogue_v1/build_prelabel.py)" = '733bc8a7d8dcbbea601647b643edf722d6f7bdbd'
test "$(git hash-object orbittrace_m2d_sacv_pareto_pair_catalogue_v1/evaluate_truth.py)" = '86d0cbaaa3a8245a5a7afdf5b838d90fe988d362'
test "$(git hash-object orbittrace_m2d_sacv_pair_v2/build_pretruth.py)" = '1cd766ad29d1f78a26f92365bb8a588f3e794d36'
python -m py_compile orbittrace_m2d_sacv_pareto_pair_catalogue_v1/build_prelabel.py orbittrace_m2d_sacv_pareto_pair_catalogue_v1/evaluate_truth.py orbittrace_m2d_sacv_pair_v2/build_pretruth.py

python -m pip install --disable-pip-version-check --upgrade pip >/dev/null
git clone -q --no-checkout "https://github.com/${GITHUB_REPOSITORY}.git" frozen-v8
git -C frozen-v8 fetch -q --no-tags --depth=1 origin c9d6c44704013ba0c9430100e98a29a56b453304
git -C frozen-v8 checkout -q FETCH_HEAD
python -m pip install --disable-pip-version-check -r frozen-v8/ghoststream_fixed4_application/requirements.txt >/dev/null
python -m pip install --disable-pip-version-check --no-deps gmn-python-api==0.0.13 >/dev/null
python -m pip install --disable-pip-version-check 'numpy==2.1.3' 'scipy==1.14.1' 'scikit-learn==1.7.1' 'hdbscan==0.8.43' 'gudhi==3.12.0' >/dev/null

git clone -q --depth 1 --branch agent/orbittrace-recurrent-local-topomodal-trunk-v1 "https://github.com/${GITHUB_REPOSITORY}.git" local-trunk-src
test "$(git -C local-trunk-src hash-object orbittrace_recurrent_local_topomodal_trunk_v1/export_geometry.py)" = '32abfb3e68520cfdc83585a88731fa3982900cde'
git -C frozen-v8 fetch -q --no-tags --depth=1 origin d8258581af143308495bd97bedcc142abbbd951a
git -C frozen-v8 show FETCH_HEAD:orbittrace_multi_anchor_energy_v3/multi_anchor_energy_v3.py > "$IN/v3/multi_anchor_energy_v3.py"
test "$(git hash-object "$IN/v3/multi_anchor_energy_v3.py")" = '2ba4835db23f8f623cdd28d0a4e6113b7954ecb2'
rm -f /tmp/run_wavelet_catalogue_v3_development.py
(cd frozen-v8 && python orbittrace_wavelet_catalogue_v3/audit_development_source.py >/dev/null && test "$(cat output/development_source_sha256.txt)" = 'ef3e69317af59fdac7a030edc77f742fc4772473d7f16b719b5d804cd4117f51')

GH_TOKEN="${GH_TOKEN:?}" gh run download 32268943692 --repo "$GITHUB_REPOSITORY" --name orbittrace-internal-mass-gmn-sparse-literature-fairness-v1-pretruth --dir "$IN/fair"
GH_TOKEN="$GH_TOKEN" gh run download 31344632499 --repo "$GITHUB_REPOSITORY" --name orbittrace-active-urc-ranker-source-export-v1 --dir "$IN/ranker"
GH_TOKEN="$GH_TOKEN" gh run download 31217916558 --repo "$GITHUB_REPOSITORY" --name orbittrace-pooled-year-centroid-v8-development --dir "$IN/v8"
GH_TOKEN="$GH_TOKEN" gh run download 32324386269 --repo "$GITHUB_REPOSITORY" --name orbittrace-m2d-sacv-v1-gmn-development --dir "$IN/sacvbase"
GH_TOKEN="$GH_TOKEN" gh run download 32329571638 --repo "$GITHUB_REPOSITORY" --name orbittrace-sacv-frozen-source-text --dir "$IN/sacvsource"

test "$(sha256sum "$IN/fair/GMN_INTERNAL_MASS_SPARSE_LITERATURE_FAIRNESS_V1_PRETRUTH.json" | cut -d' ' -f1)" = '8b0f4629659c1bfd750747303ad04ff67355adf66d4dbe474ce7fba788f5bae5'
test "$(sha256sum "$IN/ranker/run_urc_union_ranker.py" | cut -d' ' -f1)" = 'dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
test "$(sha256sum "$IN/v8/pooled_year_centroid_v8_development.json" | cut -d' ' -f1)" = 'fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b'
test "$(sha256sum "$IN/sacvbase/pretruth/M2D_SACV_V1_GMN_PRETRUTH.json" | cut -d' ' -f1)" = '77528fbec227bf8d8d311b9054c46db43668d7f12e9460b85db680c4a6ce927b'
test "$(sha256sum "$IN/sacvsource/build_pretruth.py" | cut -d' ' -f1)" = 'cd5a7505c1d095e03de683f78dce8af5cb465ba32ca1dfa3e8b9eb3e78d0fd64'
python - <<'PY'
import ast
s=open('input/m2d-sacv-pareto-pair-catalogue-v1-gmn/sacvsource/build_pretruth.py').read()
assert "key=(float(excess[k]),int(ps[k]),-float(contam[k]),-r)" in s
assert "key>best['key']" in s and "eid<best['id']" in s
ast.parse(s)
print('PASS_EXACT_PRETARGET_SACV_SELECTOR_AUDIT')
PY

# Critical technical repair from run 32377760443: scripts invoked by path need
# repository root explicitly available for the inherited pair-v2 namespace.
export PYTHONPATH="$ROOT:$IN/ranker:orbittrace_recurrent_eom_hdbscan_v1:$IN/v3:frozen-v8:frozen-v8/orbittrace_wavelet_catalogue_v3"

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

python -u orbittrace_m2d_sacv_pareto_pair_catalogue_v1/build_prelabel.py \
  --fair-pretruth "$IN/fair/GMN_INTERNAL_MASS_SPARSE_LITERATURE_FAIRNESS_V1_PRETRUTH.json" \
  --geometry "$OUT/pretruth/GMN_LABEL_FREE_GEOMETRY.json" \
  --sacv-v1-pretruth "$IN/sacvbase/pretruth/M2D_SACV_V1_GMN_PRETRUTH.json" \
  --output "$OUT/pretruth"

# Binding firewall: hidden truth cannot open unless the complete catalogue is
# already sealed and all ten zero-label gates pass.
python - <<'PY'
import hashlib,json
p='output/m2d-sacv-pareto-pair-catalogue-v1-gmn/pretruth/M2D_SACV_PARETO_PAIR_CATALOGUE_V1_PRELABEL.json'
a='output/m2d-sacv-pareto-pair-catalogue-v1-gmn/pretruth/M2D_SACV_PARETO_PAIR_CATALOGUE_V1_PRETRUTH.json'
pre=json.load(open(p)); audit=json.load(open(a)); h=hashlib.sha256(open(p,'rb').read()).hexdigest()
assert audit['verdict']=='PASS_M2D_SACV_PARETO_PAIR_CATALOGUE_V1_PRETRUTH'
assert audit['prelabel_sha256']==h
assert len(audit['gates'])==10 and all(audit['gates'].values())
assert pre['summary']['validated_pair_candidates']>0 and pre['summary']['all_panel_capacity_ok'] is True
assert audit['shower_truth_used'] is False and audit['target_information_access'] is False and audit['sonotaco_scientific_access'] is False
print(json.dumps({'verdict':audit['verdict'],'prelabel_sha256':h,'summary':audit['summary']},indent=2,sort_keys=True))
PY
sha256sum "$OUT/pretruth/M2D_SACV_PARETO_PAIR_CATALOGUE_V1_PRELABEL.json" "$OUT/pretruth/M2D_SACV_PARETO_PAIR_CATALOGUE_V1_PRETRUTH.json" > "$OUT/pretruth/PRETRUTH_SHA256.txt"
git rev-parse HEAD > "$OUT/pretruth/execution_commit.txt"
rm -f "$OUT/pretruth/GMN_LABEL_FREE_GEOMETRY.json"

# Hidden shower truth opens only after the preceding assertions have returned 0.
python -u orbittrace_m2d_sacv_pareto_pair_catalogue_v1/evaluate_truth.py \
  --prelabel "$OUT/pretruth/M2D_SACV_PARETO_PAIR_CATALOGUE_V1_PRELABEL.json" \
  --pretruth "$OUT/pretruth/M2D_SACV_PARETO_PAIR_CATALOGUE_V1_PRETRUTH.json" \
  --parent-runner orbittrace_recurrent_eom_hdbscan_v1/run_development.py \
  --quality-source "$IN/ranker/run_urc_union_ranker.py" \
  --support-source-parts frozen-v8/orbittrace_fixed4_support_wrapper_development/source_parts \
  --candidate-payload frozen-v8/sonotaco_fixed4_final_development/candidate.py.gz.b64 \
  --baseline-payload frozen-v8/real_shower_meta_stage0/run_baseline_ceiling.py.gz.b64 \
  --scorer-parts frozen-v8/mondrian_clique_development/source_parts_v2 \
  --v8-result-json "$IN/v8/pooled_year_centroid_v8_development.json" \
  --output "$OUT/truth"

sha256sum "$OUT/truth/M2D_SACV_PARETO_PAIR_CATALOGUE_V1_GMN_RESULT.json" > "$OUT/truth/RESULT_SHA256.txt"
git rev-parse HEAD > "$OUT/truth/execution_commit.txt"
python --version > "$OUT/truth/python_version.txt"
python -m pip freeze > "$OUT/truth/environment.txt"
