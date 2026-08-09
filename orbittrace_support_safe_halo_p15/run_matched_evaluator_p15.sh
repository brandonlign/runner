#!/usr/bin/env bash
set -euo pipefail

: "${GH_TOKEN:?GH_TOKEN required}"
: "${BASE_SHA:?BASE_SHA required}"
: "${HEAD_SHA:?HEAD_SHA required}"
: "${GITHUB_REPOSITORY:?GITHUB_REPOSITORY required}"

MARKER='orbittrace_support_safe_halo_p15/P15_MATCHED_EVALUATOR_RUN.md'
SCIENCE_HEAD='7e7cd5b26addb2bea8daef50ce6d86388521ea46'
DEV_NAME='orbittrace-p15-support-safe-halo-development-v2'
PRETRUTH_NAME='orbittrace-p15-matched-pretruth-checkpoints'
DEV_SOURCE='22d34131e873825ca60aefbba0b92088f19f57f589fe629bfbd3b7041d160b4b'
MATCHED_SOURCE='23d309f6702ed0aa6769381963ea64701ae59c97376a0bae536b527fbc978fe6'
P13_FINALIZER_BLOB='a5d812b9956742b51e7e3995a71eb308afa7d095'
P14_FINALIZER_BLOB='d1ce98f443b2039d70421e76dadb6ada77d1b0d5'

progress(){ printf '\n===== %s =====\n' "$*"; }

progress 'ONE-FILE EVALUATOR ACTIVATION + IMMUTABLE PREREQUISITE ARTIFACTS'
git fetch --no-tags origin "$BASE_SHA" "$HEAD_SHA"
mapfile -t changed < <(git diff --name-only "$BASE_SHA" "$HEAD_SHA")
test "${#changed[@]}" -eq 1
test "${changed[0]}" = "$MARKER"
marker="$(git show "$HEAD_SHA:$MARKER")"
test "$(printf '%s\n' "$marker" | sed -n '1p')" = 'EXECUTE_P15_MATCHED_EVALUATOR_AFTER_BOTH_PRETRUTH_CHECKPOINTS'
DEV_RUN="$(printf '%s\n' "$marker" | sed -n '2p')"
DEV_ARTIFACT="$(printf '%s\n' "$marker" | sed -n '3p')"
DEV_DIGEST="$(printf '%s\n' "$marker" | sed -n '4p')"
PRE_RUN="$(printf '%s\n' "$marker" | sed -n '5p')"
PRE_ARTIFACT="$(printf '%s\n' "$marker" | sed -n '6p')"
PRE_DIGEST="$(printf '%s\n' "$marker" | sed -n '7p')"
test "$(printf '%s\n' "$marker" | sed -n '8p')" = "$SCIENCE_HEAD"
test "$(printf '%s\n' "$marker" | wc -l)" -eq 8
for x in "$DEV_RUN" "$DEV_ARTIFACT" "$PRE_RUN" "$PRE_ARTIFACT"; do [[ "$x" =~ ^[0-9]+$ ]]; done
for x in "$DEV_DIGEST" "$PRE_DIGEST"; do [[ "$x" =~ ^sha256:[0-9a-f]{64}$ ]]; done

test "$(git hash-object orbittrace_core_halo_p13_literature/finalize_p3_evaluator_result.py)" = "$P13_FINALIZER_BLOB"
test "$(git hash-object orbittrace_core_halo_p13_literature/finalize_p14_matched_result.py)" = "$P14_FINALIZER_BLOB"
python -m py_compile orbittrace_support_safe_halo_p15/prepare_transport_compatible_p13_finalizer_p15.py orbittrace_support_safe_halo_p15/validate_p15_matched_pretruth_checkpoint.py orbittrace_support_safe_halo_p15/finalize_p15_matched_result.py

fetch_artifact(){
  local aid="$1" run="$2" digest="$3" name="$4" tag="$5"
  curl -L --fail --retry 3 -H "Authorization: Bearer $GH_TOKEN" -H 'Accept: application/vnd.github+json' \
    "https://api.github.com/repos/$GITHUB_REPOSITORY/actions/artifacts/$aid" -o "/tmp/${tag}-meta.json"
  python - "$aid" "$run" "$digest" "$name" "/tmp/${tag}-meta.json" <<'PY_META'
import json,sys
said,srun,sdigest,sname,path=sys.argv[1:]
m=json.load(open(path))
assert m['id']==int(said),m
assert m['workflow_run']['id']==int(srun),m
assert m['digest']==sdigest,m
assert m['name']==sname,m
assert not m['expired'],m
PY_META
  curl -L --fail --retry 3 -H "Authorization: Bearer $GH_TOKEN" -H 'Accept: application/vnd.github+json' \
    "https://api.github.com/repos/$GITHUB_REPOSITORY/actions/artifacts/$aid/zip" -o "/tmp/${tag}.zip"
  printf '%s  %s\n' "${digest#sha256:}" "/tmp/${tag}.zip" | sha256sum -c -
  rm -rf "/tmp/${tag}" && mkdir -p "/tmp/${tag}" && unzip -q "/tmp/${tag}.zip" -d "/tmp/${tag}"
}
fetch_artifact "$DEV_ARTIFACT" "$DEV_RUN" "$DEV_DIGEST" "$DEV_NAME" p15-dev
fetch_artifact "$PRE_ARTIFACT" "$PRE_RUN" "$PRE_DIGEST" "$PRETRUTH_NAME" p15-pre

mapfile -t devs < <(find /tmp/p15-dev -type f -name support_safe_secondary_halo_p15_development.json -print)
test "${#devs[@]}" -eq 1
python - "${devs[0]}" "$DEV_SOURCE" <<'PY_DEV'
import json,sys
r=json.load(open(sys.argv[1])); source=sys.argv[2]
assert r['verdict']=='PASS_SUPPORT_SAFE_SECONDARY_HALO_P15_DEVELOPMENT',r
assert r['p15_source_sha256']==source,r
assert r['p15_parent_p12_exact_json_identity'] is True and r['p15_fallback_vacuous_on_development'] is True,r
assert r['directions']==452 and r['unavailable_directions']==0 and r['minimum_negative_count']>=128,r
assert r['matched_truth_access'] is False and r['external_data_access'] is False and r['target_information_access'] is False,r
PY_DEV

rm -rf pretruth && mkdir -p pretruth/checkpoints
for panel in hdbscan sugar; do
  mapfile -t hits < <(find /tmp/p15-pre -type f -path "*/checkpoints/${panel}.pkl" -print)
  test "${#hits[@]}" -eq 1
  cp "${hits[0]}" "pretruth/checkpoints/${panel}.pkl"
  cp "${hits[0]}.sha256" "pretruth/checkpoints/${panel}.pkl.sha256"
done
python orbittrace_support_safe_halo_p15/validate_p15_matched_pretruth_checkpoint.py \
  --hdbscan pretruth/checkpoints/hdbscan.pkl --sugar pretruth/checkpoints/sugar.pkl

echo PASS_P15_MATCHED_EVALUATOR_PREREQUISITES_FROZEN_BEFORE_TRUTH

progress 'STAGE EXACT POSTFREEZE SOURCES — STILL NO TRUTH INDEXING'
mkdir -p input/{v3,parser,mapping,evaluator,archives} output
python orbittrace_wavelet_catalogue_v3/audit_development_source.py
echo 'ef3e69317af59fdac7a030edc77f742fc4772473d7f16b719b5d804cd4117f51  /tmp/run_wavelet_catalogue_v3_development.py' | sha256sum -c -
git fetch --no-tags --depth=1 origin d8258581af143308495bd97bedcc142abbbd951a
git show FETCH_HEAD:orbittrace_multi_anchor_energy_v3/multi_anchor_energy_v3.py > input/v3/multi_anchor_energy_v3.py
test "$(git hash-object input/v3/multi_anchor_energy_v3.py)" = '2ba4835db23f8f623cdd28d0a4e6113b7954ecb2'

fetch_exact_assignment(){
  local aid="$1" zipsha="$2" member="$3" membersha="$4" out="$5" tag="$6"
  curl -L --fail --retry 3 -H "Authorization: Bearer $GH_TOKEN" -H 'Accept: application/vnd.github+json' \
    "https://api.github.com/repos/$GITHUB_REPOSITORY/actions/artifacts/$aid/zip" -o "/tmp/${tag}.zip"
  printf '%s  %s\n' "$zipsha" "/tmp/${tag}.zip" | sha256sum -c -
  rm -rf "/tmp/${tag}" && mkdir -p "/tmp/${tag}" && unzip -q "/tmp/${tag}.zip" -d "/tmp/${tag}"
  mapfile -t hits < <(find "/tmp/${tag}" -type f -name "$member" -print)
  test "${#hits[@]}" -eq 1
  cp "${hits[0]}" "$out"
  printf '%s  %s\n' "$membersha" "$out" | sha256sum -c -
}
fetch_exact_assignment 9012424187 2a953a237d32abfed8cfef110689623ec47e9acc9ed15eddee23a39d358d1bd4 full_catalogue_assignments.jsonl.gz 35f629b1dff4d04cdc13aa8224171ec1ab8e06b52836900d66ff978b5c235761 input/hdbscan_2023.jsonl.gz hdbscan2023
fetch_exact_assignment 8955917326 82e95052eb75349031341ea600aebf8f74d6842f03c0e47edf7cdea6de471a89 full_catalogue_assignments.jsonl.gz 8e7580c52e41e6994d6e46f289a7b916565a4efc512c5549ee83f249d0e81ee3 input/hdbscan_2025.jsonl.gz hdbscan2025
fetch_exact_assignment 8957940764 ea77c5111a7be51ff2bb45b16df934f7c808c695d08ac12003025de971df4fdf sugar_uncertainty_assignments.json.gz 2b9e86572f10af447071cb10c56f643c1ad8babfe0d9aa667994ba3639834389 input/sugar_2023.json.gz sugar2023
fetch_exact_assignment 8957263372 9df4a48f4808180d534086e560e68ae56486f60171510207acd7bd6fedeebbc9 sugar_uncertainty_assignments.json.gz 77844d700bb14bb9952307fad13eb66cbc62e6a1555e5edd9c8aa0d26968b06e input/sugar_2025.json.gz sugar2025

curl -L --fail --retry 3 'https://www.astro.sk/iaumdcDB/public/data/SNMv3/023a.zip' -o input/archives/023a.zip
curl -L --fail --retry 3 'https://www.astro.sk/iaumdcDB/public/data/SNMv3/025a.zip' -o input/archives/025a.zip
echo '9f44696f99164801ff405dab90f68df3666b0d6734fed464a95e7ed0d6f5f430  input/archives/023a.zip' | sha256sum -c -
echo 'f4eb716a4b900658fcc658a633d918eca28946f59da75935f1fd5f6bc539bf52  input/archives/025a.zip' | sha256sum -c -

gh run download 30920687116 --repo "$GITHUB_REPOSITORY" --name sonotaco-2023-confirmation-source-repair-v2 --dir input/parser
cp "$(find input/parser -type f -name run_sonotaco_2023_fixed4_confirmation.py -print -quit)" input/parser_2023.py
echo 'bc2636005cc25da33e8accb6bdb70beea6ab900862cd1e6342a481395ac8f3e6  input/parser_2023.py' | sha256sum -c -
gh run download 30855193522 --repo "$GITHUB_REPOSITORY" --name real-shower-meta-data-audit --dir input/mapping
cp "$(find input/mapping -type f -name audit.json -print -quit)" input/mapping_audit.json
echo 'f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778  input/mapping_audit.json' | sha256sum -c -
git fetch --no-tags --depth=1 origin b1fa693471be78d1634632de942b6f95222c8a92
git show FETCH_HEAD:orbittrace_crossfit_seed_floor_membership_p3_literature/evaluate_frozen.py > input/evaluator/evaluate_frozen.py
git show FETCH_HEAD:orbittrace_crossfit_seed_floor_membership_p3_literature/evaluate_frozen_blindsafe.py > input/evaluator/evaluate_frozen_blindsafe.py
python -m py_compile input/parser_2023.py input/evaluator/evaluate_frozen.py input/evaluator/evaluate_frozen_blindsafe.py exact-lit/orbittrace_literature_matched_v8/sonotaco_2025_native_adapter_wrapper.py

python orbittrace_support_safe_halo_p15/prepare_transport_compatible_p13_finalizer_p15.py \
  orbittrace_core_halo_p13_literature/finalize_p3_evaluator_result.py /tmp/finalize_p13_p15.py
python -m py_compile /tmp/finalize_p13_p15.py

echo PASS_P15_MATCHED_POSTFREEZE_SOURCES_STAGED

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

python /tmp/finalize_p13_p15.py \
  --p3-result output/p3_evaluator_result.json \
  --hdbscan-checkpoint pretruth/checkpoints/hdbscan.pkl \
  --sugar-checkpoint pretruth/checkpoints/sugar.pkl \
  --output output/p13_matched_literature_result.json

python orbittrace_support_safe_halo_p15/finalize_p15_matched_result.py \
  --base-p14-finalizer orbittrace_core_halo_p13_literature/finalize_p14_matched_result.py \
  --p15-validator orbittrace_support_safe_halo_p15/validate_p15_matched_pretruth_checkpoint.py \
  --p13-result output/p13_matched_literature_result.json \
  --hdbscan-checkpoint pretruth/checkpoints/hdbscan.pkl \
  --sugar-checkpoint pretruth/checkpoints/sugar.pkl \
  --p15-development-verdict PASS_SUPPORT_SAFE_SECONDARY_HALO_P15_DEVELOPMENT \
  --p15-development-run "$DEV_RUN" \
  --p15-development-artifact-id "$DEV_ARTIFACT" \
  --p15-development-artifact-digest "$DEV_DIGEST" \
  --output output/p15_matched_literature_result.json

progress 'FINAL FROZEN P15 MATCHED GATE'
python - <<'PY'
import json
r=json.load(open('output/p15_matched_literature_result.json'))
assert r['verdict'] in {'PASS_P15_MATCHED_SPARSE_SUPERIORITY_BOTH_COMPARATORS_BOTH_YEARS','FAIL_P15_MATCHED_SPARSE_SUPERIORITY_NO_GO'}
assert r['years']==[2023,2025] and r['blind_exclusion']==[20.0,55.0]
assert r['architecture']=='P15_SUPPORT_SAFE_SECONDARY_HALO_AVAILABILITY'
assert r['sparse_superiority_required_against_both_comparators_in_both_years'] is True
assert r['pairwise_only_no_cross_denominator_comparison'] is True and r['broad_only_does_not_authorize_external'] is True
assert r['target_access_authorized'] is False
if r['verdict'].startswith('PASS_'):
    assert r['classification']=='SPARSE_STREAM_SUPERIORITY' and r['external_validation_authorized'] is True
    assert all(r['panels'][p]['sparse_pairwise_pass'] and all(r['panels'][p]['year_sparse_pass'].values()) for p in ('hdbscan','sugar'))
else:
    assert r['classification']=='NO_LITERATURE_SUPERIORITY' and r['external_validation_authorized'] is False
print('ORBITTRACE_P15_MATCHED_FINAL_BEGIN'); print(json.dumps(r,indent=2,sort_keys=True)); print('ORBITTRACE_P15_MATCHED_FINAL_END')
PY
python --version > output/python_version.txt
python -m pip freeze > output/environment.txt
sha256sum /tmp/finalize_p13_p15.py orbittrace_support_safe_halo_p15/validate_p15_matched_pretruth_checkpoint.py orbittrace_support_safe_halo_p15/finalize_p15_matched_result.py > output/p15_evaluator_source_sha256.txt
