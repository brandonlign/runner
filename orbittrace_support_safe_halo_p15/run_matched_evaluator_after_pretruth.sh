#!/usr/bin/env bash
set -euo pipefail

: "${GH_TOKEN:?GH_TOKEN required}"
: "${BASE_SHA:?BASE_SHA required}"
: "${HEAD_SHA:?HEAD_SHA required}"
: "${REPO:?REPO required}"

MARKER='orbittrace_support_safe_halo_p15/MATCHED_EVALUATOR_RUN.md'
DEV_RUN=31329529635
DEV_ARTIFACT=9042508082
DEV_NAME='orbittrace-p15-support-safe-halo-development-artifact-adjudication'
DEV_DIGEST='sha256:f6bee693dfd64f86fcbb7fa2b3760a9258d712d5df29c59e270233d87a6a160f'
DEV_RESULT_SHA='0424308527eb5edb7ec21043f1b7721472ebe5aeaa2f5f7f604185b1e09d006e'
PRETRUTH_NAME='orbittrace-p15-matched-pretruth-checkpoints'

P15_VALIDATOR_BLOB='d8653b898ca8c106d79df01c855783797294c30c'
P15_FINALIZER_BLOB='17e446565aa324e3de374246abc5a0693fc8467b'
P14_PREP_BLOB='ee932b83ad63d10fb81c5b8c85bb151c4467f8f7'
P14_TRANSPORT_FINALIZER_BLOB='1e9160c7beb5bc7651dc2b9f03db6211bc639ac6'
P13_FINALIZER_BLOB='a5d812b9956742b51e7e3995a71eb308afa7d095'
P14_FINALIZER_BLOB='d1ce98f443b2039d70421e76dadb6ada77d1b0d5'

progress(){ printf '\n===== %s =====\n' "$*"; }
check_blob(){ local p="$1" e="$2" a; a="$(git hash-object "$p")"; printf 'PIN_BLOB %s expected=%s actual=%s\n' "$p" "$e" "$a"; test "$a" = "$e"; }

progress 'ONE-FILE EVALUATOR CHILD / PRETRUTH ARTIFACT IDENTITIES'
git fetch --no-tags origin "$BASE_SHA" "$HEAD_SHA"
mapfile -t files < <(git diff --name-only "$BASE_SHA" "$HEAD_SHA")
test "${#files[@]}" -eq 1
test "${files[0]}" = "$MARKER"
marker="$(git show "$HEAD_SHA:$MARKER")"
test "$(printf '%s\n' "$marker" | sed -n '1p')" = 'EXECUTE_P15_MATCHED_EVALUATOR_AFTER_PRETRUTH_FREEZE'
PRE_RUN="$(printf '%s\n' "$marker" | sed -n '2p')"
PRE_ARTIFACT="$(printf '%s\n' "$marker" | sed -n '3p')"
PRE_DIGEST="$(printf '%s\n' "$marker" | sed -n '4p')"
HDB_CP_SHA="$(printf '%s\n' "$marker" | sed -n '5p')"
SUGAR_CP_SHA="$(printf '%s\n' "$marker" | sed -n '6p')"
test "$(printf '%s\n' "$marker" | wc -l)" -eq 6
[[ "$PRE_RUN" =~ ^[0-9]+$ ]]
[[ "$PRE_ARTIFACT" =~ ^[0-9]+$ ]]
[[ "$PRE_DIGEST" =~ ^sha256:[0-9a-f]{64}$ ]]
[[ "$HDB_CP_SHA" =~ ^[0-9a-f]{64}$ ]]
[[ "$SUGAR_CP_SHA" =~ ^[0-9a-f]{64}$ ]]

git checkout --detach "$BASE_SHA"
test ! -e "$MARKER"

progress 'PIN MERGED EVALUATOR WRAPPER SOURCE'
check_blob orbittrace_support_safe_halo_p15/validate_p15_pretruth_checkpoints.py "$P15_VALIDATOR_BLOB"
check_blob orbittrace_support_safe_halo_p15/finalize_p15_matched_result.py "$P15_FINALIZER_BLOB"
check_blob orbittrace_support_safe_rank_p14/prepare_transport_compatible_p13_finalizer.py "$P14_PREP_BLOB"
check_blob orbittrace_support_safe_rank_p14/finalize_p14_matched_result_transport_v3.py "$P14_TRANSPORT_FINALIZER_BLOB"
check_blob orbittrace_core_halo_p13_literature/finalize_p3_evaluator_result.py "$P13_FINALIZER_BLOB"
check_blob orbittrace_core_halo_p13_literature/finalize_p14_matched_result.py "$P14_FINALIZER_BLOB"
python -m py_compile \
  orbittrace_support_safe_halo_p15/validate_p15_pretruth_checkpoints.py \
  orbittrace_support_safe_halo_p15/finalize_p15_matched_result.py \
  orbittrace_support_safe_rank_p14/prepare_transport_compatible_p13_finalizer.py \
  orbittrace_support_safe_rank_p14/finalize_p14_matched_result_transport_v3.py

download_exact_artifact(){
  local aid="$1" run="$2" name="$3" digest="$4" tag="$5"
  curl -L --fail --retry 3 -H "Authorization: Bearer $GH_TOKEN" -H 'Accept: application/vnd.github+json' \
    "https://api.github.com/repos/$REPO/actions/artifacts/$aid" -o "/tmp/${tag}-meta.json"
  python - "$aid" "$run" "$name" "$digest" "/tmp/${tag}-meta.json" <<'PY_META'
import json,sys
aid,run,name,digest,path=sys.argv[1:]
m=json.load(open(path))
assert m['id']==int(aid) and m['workflow_run']['id']==int(run),m
assert m['name']==name and m['digest']==digest and not m['expired'],m
PY_META
  curl -L --fail --retry 3 -H "Authorization: Bearer $GH_TOKEN" -H 'Accept: application/vnd.github+json' \
    "https://api.github.com/repos/$REPO/actions/artifacts/$aid/zip" -o "/tmp/${tag}.zip"
  printf '%s  %s\n' "${digest#sha256:}" "/tmp/${tag}.zip" | sha256sum -c -
  rm -rf "/tmp/${tag}" && mkdir -p "/tmp/${tag}"
  unzip -q "/tmp/${tag}.zip" -d "/tmp/${tag}"
}

progress 'VERIFY SOLE ADMISSIBLE P15 DEVELOPMENT PASS AGAIN'
download_exact_artifact "$DEV_ARTIFACT" "$DEV_RUN" "$DEV_NAME" "$DEV_DIGEST" p15-dev
mapfile -t devhits < <(find /tmp/p15-dev -type f -name support_safe_secondary_halo_p15_development_artifact_adjudication.json -print)
test "${#devhits[@]}" -eq 1
printf '%s  %s\n' "$DEV_RESULT_SHA" "${devhits[0]}" | sha256sum -c -
python - "${devhits[0]}" <<'PY_DEV'
import json,sys
r=json.load(open(sys.argv[1]))
assert r['verdict']=='PASS_SUPPORT_SAFE_SECONDARY_HALO_P15_DEVELOPMENT',r
assert r['adjudication_mode']=='artifact_only_from_immutable_canonical_P12_P13',r
assert r['canonical_direction_count']==452 and r['canonical_minimum_negative_count']==2197,r
assert r['p15_unavailable_direction_count']==0 and r['p15_unavailable_directions']==[],r
assert r['p15_fallback_vacuous_on_development'] is True,r
assert r['new_truth_query'] is False and r['matched_truth_access'] is False and r['external_data_access'] is False and r['target_information_access'] is False,r
PY_DEV

progress 'VERIFY BOTH P15 PRETRUTH CHECKPOINTS + HASHES'
download_exact_artifact "$PRE_ARTIFACT" "$PRE_RUN" "$PRETRUTH_NAME" "$PRE_DIGEST" p15-pre
rm -rf pretruth && mkdir -p pretruth/checkpoints
for panel in hdbscan sugar; do
  mapfile -t hits < <(find /tmp/p15-pre -type f -path "*/checkpoints/${panel}.pkl" -print)
  test "${#hits[@]}" -eq 1
  test -f "${hits[0]}.sha256"
  cp "${hits[0]}" "pretruth/checkpoints/${panel}.pkl"
  cp "${hits[0]}.sha256" "pretruth/checkpoints/${panel}.pkl.sha256"
done
printf '%s  %s\n' "$HDB_CP_SHA" pretruth/checkpoints/hdbscan.pkl | sha256sum -c -
printf '%s  %s\n' "$SUGAR_CP_SHA" pretruth/checkpoints/sugar.pkl | sha256sum -c -
test "$(cat pretruth/checkpoints/hdbscan.pkl.sha256)" = "$HDB_CP_SHA"
test "$(cat pretruth/checkpoints/sugar.pkl.sha256)" = "$SUGAR_CP_SHA"
python orbittrace_support_safe_halo_p15/validate_p15_pretruth_checkpoints.py \
  --hdbscan pretruth/checkpoints/hdbscan.pkl \
  --sugar pretruth/checkpoints/sugar.pkl

echo PASS_P15_MATCHED_EVALUATOR_PREREQUISITES_FROZEN_BEFORE_TRUTH

progress 'STAGE EXACT POSTFREEZE SOURCES — VALUES STILL UNINDEXED'
mkdir -p input/{v3,evaluator,archives} output /tmp/p15-eval/{parser,mapping}
python orbittrace_wavelet_catalogue_v3/audit_development_source.py
echo 'ef3e69317af59fdac7a030edc77f742fc4772473d7f16b719b5d804cd4117f51  /tmp/run_wavelet_catalogue_v3_development.py' | sha256sum -c -
git fetch --no-tags --depth=1 origin d8258581af143308495bd97bedcc142abbbd951a
git show FETCH_HEAD:orbittrace_multi_anchor_energy_v3/multi_anchor_energy_v3.py > input/v3/multi_anchor_energy_v3.py
test "$(git hash-object input/v3/multi_anchor_energy_v3.py)" = '2ba4835db23f8f623cdd28d0a4e6113b7954ecb2'

fetch_assignment(){
  local aid="$1" zipsha="$2" member="$3" membersha="$4" out="$5" tag="$6"
  curl -L --fail --retry 3 -H "Authorization: Bearer $GH_TOKEN" -H 'Accept: application/vnd.github+json' \
    "https://api.github.com/repos/$REPO/actions/artifacts/$aid/zip" -o "/tmp/${tag}.zip"
  printf '%s  %s\n' "$zipsha" "/tmp/${tag}.zip" | sha256sum -c -
  rm -rf "/tmp/${tag}" && mkdir -p "/tmp/${tag}"
  unzip -q "/tmp/${tag}.zip" -d "/tmp/${tag}"
  mapfile -t hits < <(find "/tmp/${tag}" -type f -name "$member" -print)
  test "${#hits[@]}" -eq 1
  cp "${hits[0]}" "$out"
  printf '%s  %s\n' "$membersha" "$out" | sha256sum -c -
}
fetch_assignment 9012424187 2a953a237d32abfed8cfef110689623ec47e9acc9ed15eddee23a39d358d1bd4 full_catalogue_assignments.jsonl.gz 35f629b1dff4d04cdc13aa8224171ec1ab8e06b52836900d66ff978b5c235761 input/hdbscan_2023.jsonl.gz hdbscan2023
fetch_assignment 8955917326 82e95052eb75349031341ea600aebf8f74d6842f03c0e47edf7cdea6de471a89 full_catalogue_assignments.jsonl.gz 8e7580c52e41e6994d6e46f289a7b916565a4efc512c5549ee83f249d0e81ee3 input/hdbscan_2025.jsonl.gz hdbscan2025
fetch_assignment 8957940764 ea77c5111a7be51ff2bb45b16df934f7c808c695d08ac12003025de971df4fdf sugar_uncertainty_assignments.json.gz 2b9e86572f10af447071cb10c56f643c1ad8babfe0d9aa667994ba3639834389 input/sugar_2023.json.gz sugar2023
fetch_assignment 8957263372 9df4a48f4808180d534086e560e68ae56486f60171510207acd7bd6fedeebbc9 sugar_uncertainty_assignments.json.gz 77844d700bb14bb9952307fad13eb66cbc62e6a1555e5edd9c8aa0d26968b06e input/sugar_2025.json.gz sugar2025

curl -L --fail --retry 3 'https://www.astro.sk/iaumdcDB/public/data/SNMv3/023a.zip' -o input/archives/023a.zip
curl -L --fail --retry 3 'https://www.astro.sk/iaumdcDB/public/data/SNMv3/025a.zip' -o input/archives/025a.zip
echo '9f44696f99164801ff405dab90f68df3666b0d6734fed464a95e7ed0d6f5f430  input/archives/023a.zip' | sha256sum -c -
echo 'f4eb716a4b900658fcc658a633d918eca28946f59da75935f1fd5f6bc539bf52  input/archives/025a.zip' | sha256sum -c -

gh run download 30920687116 --repo "$REPO" --name sonotaco-2023-confirmation-source-repair-v2 --dir /tmp/p15-eval/parser
mapfile -t parserhits < <(find /tmp/p15-eval/parser -type f -name run_sonotaco_2023_fixed4_confirmation.py -print)
test "${#parserhits[@]}" -eq 1
cp "${parserhits[0]}" input/parser_2023.py
echo 'bc2636005cc25da33e8accb6bdb70beea6ab900862cd1e6342a481395ac8f3e6  input/parser_2023.py' | sha256sum -c -
gh run download 30855193522 --repo "$REPO" --name real-shower-meta-data-audit --dir /tmp/p15-eval/mapping
mapfile -t maphits < <(find /tmp/p15-eval/mapping -type f -name audit.json -print)
test "${#maphits[@]}" -eq 1
cp "${maphits[0]}" input/mapping_audit.json
echo 'f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778  input/mapping_audit.json' | sha256sum -c -

git fetch --no-tags --depth=1 origin b1fa693471be78d1634632de942b6f95222c8a92
git show FETCH_HEAD:orbittrace_crossfit_seed_floor_membership_p3_literature/evaluate_frozen.py > input/evaluator/evaluate_frozen.py
git show FETCH_HEAD:orbittrace_crossfit_seed_floor_membership_p3_literature/evaluate_frozen_blindsafe.py > input/evaluator/evaluate_frozen_blindsafe.py
python -m py_compile input/parser_2023.py input/evaluator/evaluate_frozen.py input/evaluator/evaluate_frozen_blindsafe.py exact-lit/orbittrace_literature_matched_v8/sonotaco_2025_native_adapter_wrapper.py

python orbittrace_support_safe_rank_p14/prepare_transport_compatible_p13_finalizer.py \
  orbittrace_core_halo_p13_literature/finalize_p3_evaluator_result.py /tmp/finalize_p13_transport.py
python -m py_compile /tmp/finalize_p13_transport.py

echo PASS_P15_MATCHED_POSTFREEZE_SOURCE_STAGING_COMPLETE

progress 'OPEN MATCHED TRUTH + COMPETITOR CLUSTER VALUES EXACTLY ONCE'
export PYTHONPATH="exact-lit:input/v3:exact-lit/orbittrace_wavelet_catalogue_v3:."
python -u input/evaluator/evaluate_frozen_blindsafe.py \
  --hdbscan-pretruth pretruth/checkpoints/hdbscan.pkl \
  --sugar-pretruth pretruth/checkpoints/sugar.pkl \
  --exact-row-runner exact-lit/orbittrace_literature_matched_v8/run_exact_row_benchmark.py \
  --base-runner /tmp/run_wavelet_catalogue_v3_development.py \
  --support-source-parts exact-lit/orbittrace_fixed4_support_wrapper_development/source_parts \
  --candidate-payload exact-lit/sonotaco_fixed4_final_development/candidate.py.gz.b64 \
  --baseline-payload exact-lit/real_shower_meta_stage0/run_baseline_ceiling.py.gz.b64 \
  --scorer-parts exact-lit/mondrian_clique_development/source_parts_v2 \
  --parser-2023 input/parser_2023.py \
  --parser-2025 exact-lit/orbittrace_literature_matched_v8/sonotaco_2025_native_adapter_wrapper.py \
  --mapping-audit input/mapping_audit.json \
  --archive-2023 input/archives/023a.zip --archive-2025 input/archives/025a.zip \
  --hdbscan-2023 input/hdbscan_2023.jsonl.gz --hdbscan-2025 input/hdbscan_2025.jsonl.gz \
  --sugar-2023 input/sugar_2023.json.gz --sugar-2025 input/sugar_2025.json.gz \
  --output output/p3_evaluator_result.json

python /tmp/finalize_p13_transport.py \
  --p3-result output/p3_evaluator_result.json \
  --hdbscan-checkpoint pretruth/checkpoints/hdbscan.pkl \
  --sugar-checkpoint pretruth/checkpoints/sugar.pkl \
  --output output/p13_matched_literature_result.json

python orbittrace_support_safe_halo_p15/finalize_p15_matched_result.py \
  --base-p14-transport-finalizer orbittrace_support_safe_rank_p14/finalize_p14_matched_result_transport_v3.py \
  --base-p14-finalizer orbittrace_core_halo_p13_literature/finalize_p14_matched_result.py \
  --p13-result output/p13_matched_literature_result.json \
  --hdbscan-checkpoint pretruth/checkpoints/hdbscan.pkl \
  --sugar-checkpoint pretruth/checkpoints/sugar.pkl \
  --output output/p15_matched_literature_result.json

progress 'FINAL FROZEN P15 MATCHED ADVANCEMENT GATE'
python - "$PRE_RUN" "$PRE_ARTIFACT" "$PRE_DIGEST" "$HDB_CP_SHA" "$SUGAR_CP_SHA" <<'PY_FINAL'
import hashlib,json,sys
from pathlib import Path
pre_run,pre_art,pre_digest,hdb_sha,sugar_sha=sys.argv[1:]
r=json.load(open('output/p15_matched_literature_result.json'))
assert r['verdict'] in {'PASS_P15_MATCHED_SPARSE_SUPERIORITY_BOTH_COMPARATORS_BOTH_YEARS','FAIL_P15_MATCHED_SPARSE_SUPERIORITY_NO_GO'},r
assert r['architecture']=='P15_SUPPORT_SAFE_SECONDARY_HALO_AVAILABILITY',r
assert r['sparse_superiority_required_against_both_comparators_in_both_years'] is True,r
assert r['pairwise_only_no_cross_denominator_comparison'] is True and r['broad_only_does_not_authorize_external'] is True,r
assert r['target_access_authorized'] is False,r
passed=r['verdict'].startswith('PASS_')
assert bool(r['external_validation_authorized'])==passed,r
if passed:
    assert all(r['panels'][p]['sparse_pairwise_pass'] and all(r['panels'][p]['year_sparse_pass'].values()) for p in ('hdbscan','sugar')),r
prov={
  'classification':'P15 matched execution provenance',
  'development_run':31329529635,
  'development_artifact_id':9042508082,
  'development_artifact_digest':'sha256:f6bee693dfd64f86fcbb7fa2b3760a9258d712d5df29c59e270233d87a6a160f',
  'development_result_sha256':'0424308527eb5edb7ec21043f1b7721472ebe5aeaa2f5f7f604185b1e09d006e',
  'pretruth_run':int(pre_run),'pretruth_artifact_id':int(pre_art),'pretruth_artifact_digest':pre_digest,
  'hdbscan_checkpoint_sha256':hdb_sha,'sugar_checkpoint_sha256':sugar_sha,
  'matched_result_sha256':hashlib.sha256(Path('output/p15_matched_literature_result.json').read_bytes()).hexdigest(),
  'target_access_authorized':False,
}
Path('output/p15_matched_execution_provenance.json').write_text(json.dumps(prov,indent=2,sort_keys=True)+'\n')
print('P15_MATCHED_FINAL_BEGIN'); print(json.dumps(r,indent=2,sort_keys=True)); print('P15_MATCHED_FINAL_END')
PY_FINAL
