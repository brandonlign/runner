#!/usr/bin/env bash
set -euo pipefail
ROOT="$PWD"
OUT="$ROOT/output/m2d-sacv-pair-pareto-catalogue-v1-gmn"
IN="$ROOT/input/m2d-sacv-pair-pareto-catalogue-v1-gmn"
rm -rf "$OUT" "$IN" "$ROOT/frozen-v8" "$ROOT/local-trunk-src"
mkdir -p "$OUT/geometry" "$OUT/pretruth" "$OUT/truth" "$IN/internal" "$IN/ranker" "$IN/v8" "$IN/v3" "$IN/fair" "$IN/sacv"

# Scientific files are immutable; this script only repairs transport/runtime reconstruction.
test "$(git hash-object orbittrace_m2d_sacv_pair_pareto_catalogue_v1/PROTOCOL.md)" = 'cfca4d2b219732b2a3b8eedcea8e7746ad4b9e3a'
test "$(git hash-object orbittrace_m2d_sacv_pair_pareto_catalogue_v1/instrument_runtime.py)" = 'e4ff0108d6c5989a5e00bfc92b76154863e22e68'
test "$(git hash-object orbittrace_m2d_sacv_pair_pareto_catalogue_v1/build_pretruth.py)" = '35eced550f1e67652bd4f217a80b2dff435f9e89'
test "$(git hash-object orbittrace_m2d_sacv_pair_pareto_catalogue_v1/evaluate_truth.py)" = '77e94d894d1f02de0d90c2be3aff39244628d7d6'
echo 'd75b76a36911c916620da5e029f82c7987718b1610eb6bd61922015b5ab50d4a  orbittrace_m2d_sacv_v1_source.tgz' | sha256sum -c -
tar -xzf orbittrace_m2d_sacv_v1_source.tgz

# Transport repair: reconstruct the exact archived edge-consensus bundle with
# explicit part order and Python whitespace-safe base64 decoding.
python - <<'PY'
from pathlib import Path
import base64, hashlib
root=Path('orbittrace_m2d_sacv_edge_consensus_v1/source_parts')
parts=['part00.b64','part01a.b64','part01b.b64','part02.b64','part03.b64','part04.b64']
raw=b''.join((root/p).read_bytes() for p in parts)
assert len(raw)==16844, len(raw)
compact=b''.join(raw.split())
data=base64.b64decode(compact, validate=True)
h=hashlib.sha256(data).hexdigest()
assert h=='f7d9fc168fb5f8a589a5d965252979951ae9659ded4dc6662a562276c6273d28', h
Path('/tmp/ec.tgz').write_bytes(data)
print('PASS_EDGE_BUNDLE_RECONSTRUCTION',h,len(data))
PY
tar -xzf /tmp/ec.tgz
echo 'f6c5b2a89d70003b058e772b753c531cb5072b2c1eb52d77166d7a5cbd566ca7  orbittrace_m2d_sacv_fallback_recurrence_v1/patch_source.py' | sha256sum -c -
python orbittrace_m2d_sacv_fallback_recurrence_v1/patch_source.py
echo '435db7a53d4a78547f910d5e1a836bc399a7bd77b227056b4a1c12665d10b13a  orbittrace_m2d_sacv_edge_consensus_v1/build_pretruth.py' | sha256sum -c -
cp orbittrace_m2d_sacv_edge_consensus_v1/build_pretruth.py orbittrace_m2d_sacv_fallback_recurrence_v1/build_pretruth.py
python orbittrace_m2d_sacv_pair_pareto_catalogue_v1/instrument_runtime.py
python -m py_compile orbittrace_m2d_sacv_pair_pareto_catalogue_v1/*.py orbittrace_m2d_sacv_fallback_recurrence_v1/build_pretruth.py

# Exact algorithmic equivalence audit for the frozen 3D Pareto-depth optimization.
python - <<'PY'
import random
from orbittrace_m2d_sacv_pair_pareto_catalogue_v1.build_pretruth import pareto_depth
def brute(rows):
    rem=set(range(len(rows))); d=[0]*len(rows); layer=1
    while rem:
        front=[]
        for i in rem:
            a=rows[i]
            if not any(j!=i and rows[j]['parent_rank']<=a['parent_rank'] and rows[j]['r22']<=a['r22'] and rows[j]['r23']<=a['r23'] and (rows[j]['parent_rank']<a['parent_rank'] or rows[j]['r22']<a['r22'] or rows[j]['r23']<a['r23']) for j in rem):
                front.append(i)
        assert front
        for i in front: d[i]=layer; rem.remove(i)
        layer+=1
    return d
random.seed(1409)
for _ in range(500):
    rows=[]
    for p in range(1,random.randint(2,8)):
        seen=set()
        for _j in range(random.randint(1,10)):
            q=(random.randint(1,8),random.randint(1,8))
            if q in seen: continue
            seen.add(q); rows.append({'parent_rank':p,'r22':q[0],'r23':q[1],'pair_hash':f'{p}:{q}'})
    ref=brute(rows); test=[dict(x) for x in rows]; pareto_depth(test)
    assert [x['pareto_depth'] for x in test]==ref
print('PASS_EXACT_3D_PARETO_DEPTH_EQUIVALENCE')
PY

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

GH_TOKEN="${GH_TOKEN:?}" gh run download 32041661731 --repo "$GITHUB_REPOSITORY" --name orbittrace-support-cut-bifiltration-internal-mass-v1 --dir "$IN/internal"
GH_TOKEN="$GH_TOKEN" gh run download 31344632499 --repo "$GITHUB_REPOSITORY" --name orbittrace-active-urc-ranker-source-export-v1 --dir "$IN/ranker"
GH_TOKEN="$GH_TOKEN" gh run download 31217916558 --repo "$GITHUB_REPOSITORY" --name orbittrace-pooled-year-centroid-v8-development --dir "$IN/v8"
GH_TOKEN="$GH_TOKEN" gh run download 32268943692 --repo "$GITHUB_REPOSITORY" --name orbittrace-internal-mass-gmn-sparse-literature-fairness-v1-pretruth --dir "$IN/fair"
GH_TOKEN="$GH_TOKEN" gh run download 32325172601 --repo "$GITHUB_REPOSITORY" --name orbittrace-m2d-sacv-v1-gmn-development --dir "$IN/sacv"

test "$(sha256sum "$IN/internal/SUPPORT_CUT_BIFILTRATION_INTERNAL_MASS_V1_PRELABEL.json" | cut -d' ' -f1)" = '7b1ddfcd32cd0b52321e3b3dfc614a88dd9b973f947c1d4d0de74fddf26b59cd'
test "$(sha256sum "$IN/ranker/run_urc_union_ranker.py" | cut -d' ' -f1)" = 'dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
test "$(sha256sum "$IN/v8/pooled_year_centroid_v8_development.json" | cut -d' ' -f1)" = 'fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b'
test "$(sha256sum "$IN/fair/GMN_INTERNAL_MASS_SPARSE_LITERATURE_FAIRNESS_V1_PRETRUTH.json" | cut -d' ' -f1)" = '8b0f4629659c1bfd750747303ad04ff67355adf66d4dbe474ce7fba788f5bae5'
test "$(sha256sum "$IN/sacv/pretruth/M2D_SACV_V1_GMN_PRETRUTH.json" | cut -d' ' -f1)" = '77528fbec227bf8d8d311b9054c46db43668d7f12e9460b85db680c4a6ce927b'

export PYTHONPATH="$ROOT:$IN/ranker:orbittrace_recurrent_eom_hdbscan_v1:$IN/v3:frozen-v8:frozen-v8/orbittrace_wavelet_catalogue_v3"
python -u local-trunk-src/orbittrace_recurrent_local_topomodal_trunk_v1/export_geometry.py \
  --parent-runner orbittrace_recurrent_eom_hdbscan_v1/run_development.py \
  --quality-source "$IN/ranker/run_urc_union_ranker.py" \
  --support-source-parts frozen-v8/orbittrace_fixed4_support_wrapper_development/source_parts \
  --candidate-payload frozen-v8/sonotaco_fixed4_final_development/candidate.py.gz.b64 \
  --baseline-payload frozen-v8/real_shower_meta_stage0/run_baseline_ceiling.py.gz.b64 \
  --scorer-parts frozen-v8/mondrian_clique_development/source_parts_v2 \
  --v8-result-json "$IN/v8/pooled_year_centroid_v8_development.json" \
  --output "$OUT/geometry/GMN_LABEL_FREE_GEOMETRY.json"
test "$(sha256sum "$OUT/geometry/GMN_LABEL_FREE_GEOMETRY.json" | cut -d' ' -f1)" = '1fd5cd0577d88784845e0d367ef35491d6afb7caa78bb06fa05d72048daec384'

python -u orbittrace_m2d_sacv_pair_pareto_catalogue_v1/build_pretruth.py \
  --fair-pretruth "$IN/fair/GMN_INTERNAL_MASS_SPARSE_LITERATURE_FAIRNESS_V1_PRETRUTH.json" \
  --geometry "$OUT/geometry/GMN_LABEL_FREE_GEOMETRY.json" \
  --sacv-v1-pretruth "$IN/sacv/pretruth/M2D_SACV_V1_GMN_PRETRUTH.json" \
  --output "$OUT/pretruth/M2D_SACV_PAIR_PARETO_CATALOGUE_V1_GMN_PRETRUTH.json"
sha256sum "$OUT/pretruth/M2D_SACV_PAIR_PARETO_CATALOGUE_V1_GMN_PRETRUTH.json" > "$OUT/pretruth/PRETRUTH_SHA256.txt"
python - <<'PY'
import json
p='output/m2d-sacv-pair-pareto-catalogue-v1-gmn/pretruth/M2D_SACV_PAIR_PARETO_CATALOGUE_V1_GMN_PRETRUTH.json'
r=json.load(open(p))
assert r['shower_truth_used'] is False and r['target_information_access'] is False and r['sonotaco_scientific_access'] is False
assert all(all(v==0 for v in s['capacity_shortfall'].values()) for s in r['subsets']), 'POWER_INCONCLUSIVE_CAPACITY_SHORTFALL'
print('PRETRUTH_SEALED',json.dumps(r['summary'],sort_keys=True))
PY

# Hidden GMN truth may open only after the sealed firewall/capacity assertions above.
python -u orbittrace_m2d_sacv_pair_pareto_catalogue_v1/evaluate_truth.py \
  --candidate-pretruth "$OUT/pretruth/M2D_SACV_PAIR_PARETO_CATALOGUE_V1_GMN_PRETRUTH.json" \
  --fair-pretruth "$IN/fair/GMN_INTERNAL_MASS_SPARSE_LITERATURE_FAIRNESS_V1_PRETRUTH.json" \
  --internal-prelabel "$IN/internal/SUPPORT_CUT_BIFILTRATION_INTERNAL_MASS_V1_PRELABEL.json" \
  --parent-runner orbittrace_recurrent_eom_hdbscan_v1/run_development.py \
  --quality-source "$IN/ranker/run_urc_union_ranker.py" \
  --support-source-parts frozen-v8/orbittrace_fixed4_support_wrapper_development/source_parts \
  --candidate-payload frozen-v8/sonotaco_fixed4_final_development/candidate.py.gz.b64 \
  --baseline-payload frozen-v8/real_shower_meta_stage0/run_baseline_ceiling.py.gz.b64 \
  --scorer-parts frozen-v8/mondrian_clique_development/source_parts_v2 \
  --v8-result-json "$IN/v8/pooled_year_centroid_v8_development.json" \
  --output "$OUT/truth/M2D_SACV_PAIR_PARETO_CATALOGUE_V1_GMN_RESULT.json"
sha256sum "$OUT/truth/M2D_SACV_PAIR_PARETO_CATALOGUE_V1_GMN_RESULT.json" > "$OUT/truth/RESULT_SHA256.txt"
git rev-parse HEAD > "$OUT/truth/execution_commit.txt"
python -m pip freeze > "$OUT/truth/environment.txt"
