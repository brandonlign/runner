#!/usr/bin/env bash
set -euo pipefail

: "${GH_TOKEN:?GH_TOKEN required}"
: "${BASE_SHA:?BASE_SHA required}"
: "${HEAD_SHA:?HEAD_SHA required}"
: "${REPO:?REPO required}"

MARKER='orbittrace_p17_rank_halo_membership_p18/MATCHED_TRUTH_RUN.md'
PRETRUTH_NAME='orbittrace-p18-matched-pretruth-checkpoints'
P15_PARENT_BLOB='f5d7177a7f58aa4d5150b43755ec8ca838a29c51'
P18_RUNTIME_HELPER_BLOB='f3ea3bd83eb5f70e7ade2beb406ef8b6a7fdadeb'
P18_PREP_BLOB='cb5a66e7481fa4542b28135dc4c8c89ef33b276f'
P18_FINALIZER_BLOB='9f7b8ea6279434e7243ac9debdbf5d5a4a33aadd'
P18_PROTOCOL_BLOB='444c08ed2678a1b2eb6949a043799d63c3ec1a1b'
P14_TRANSPORT_FINALIZER_BLOB='1e9160c7beb5bc7651dc2b9f03db6211bc639ac6'
P14_FINALIZER_BLOB='d1ce98f443b2039d70421e76dadb6ada77d1b0d5'
P13_FINALIZER_BLOB='a5d812b9956742b51e7e3995a71eb308afa7d095'

progress(){ printf '\n===== %s =====\n' "$*"; }
check_blob(){ local p="$1" e="$2" a; a="$(git hash-object "$p")"; printf 'PIN_BLOB %s expected=%s actual=%s\n' "$p" "$e" "$a"; test "$a" = "$e"; }

progress 'ONE-FILE P18 TRUTH CHILD / IMMUTABLE PRETRUTH IDENTITIES'
git fetch --no-tags origin "$BASE_SHA" "$HEAD_SHA"
mapfile -t files < <(git diff --name-only "$BASE_SHA" "$HEAD_SHA")
test "${#files[@]}" -eq 1
test "${files[0]}" = "$MARKER"
marker="$(git show "$HEAD_SHA:$MARKER")"
test "$(printf '%s\n' "$marker" | sed -n '1p')" = 'EXECUTE_P18_MATCHED_TRUTH_ONCE'
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

progress 'PIN FROZEN P18 + INHERITED EVALUATOR SOURCES'
check_blob orbittrace_support_safe_halo_p15/run_matched_evaluator_after_pretruth.sh "$P15_PARENT_BLOB"
check_blob orbittrace_p17_rank_halo_membership_p18/prepare_p18_matched_truth_runtime.py "$P18_RUNTIME_HELPER_BLOB"
check_blob orbittrace_p17_rank_halo_membership_p18/prepare_p18_compatible_p13_finalizer.py "$P18_PREP_BLOB"
check_blob orbittrace_p17_rank_halo_membership_p18/finalize_p18_matched_result.py "$P18_FINALIZER_BLOB"
check_blob orbittrace_p17_rank_halo_membership_p18/P18_MATCHED_TRUTH_OPENING_PROTOCOL.md "$P18_PROTOCOL_BLOB"
check_blob orbittrace_support_safe_rank_p14/finalize_p14_matched_result_transport_v3.py "$P14_TRANSPORT_FINALIZER_BLOB"
check_blob orbittrace_core_halo_p13_literature/finalize_p14_matched_result.py "$P14_FINALIZER_BLOB"
check_blob orbittrace_core_halo_p13_literature/finalize_p3_evaluator_result.py "$P13_FINALIZER_BLOB"
python -m py_compile \
  orbittrace_p17_rank_halo_membership_p18/prepare_p18_matched_truth_runtime.py \
  orbittrace_p17_rank_halo_membership_p18/prepare_p18_compatible_p13_finalizer.py \
  orbittrace_p17_rank_halo_membership_p18/finalize_p18_matched_result.py \
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

progress 'VERIFY EXACT P18 PRETRUTH ARTIFACT BEFORE ANY TRUTH ACCESS'
curl -L --fail --retry 3 -H "Authorization: Bearer $GH_TOKEN" -H 'Accept: application/vnd.github+json' \
  "https://api.github.com/repos/$REPO/actions/runs/$PRE_RUN" -o /tmp/p18-pre-run.json
download_exact_artifact "$PRE_ARTIFACT" "$PRE_RUN" "$PRETRUTH_NAME" "$PRE_DIGEST" p18-pre
python - "$PRE_RUN" <<'PY_RUN'
import json,sys
r=json.load(open('/tmp/p18-pre-run.json'))
assert r['id']==int(sys.argv[1]) and r['status']=='completed' and r['conclusion']=='success',r
assert r['name']=='OrbitTrace P18 matched pretruth checkpoint transform',r
assert r['event']=='pull_request',r
assert r['head_branch']=='agent/orbittrace-p18-pretruth-transform-run-v1',r
print('PASS_P18_MATCHED_TRUTH_EXACT_PRETRUTH_RUN')
PY_RUN
mapfile -t manifests < <(find /tmp/p18-pre -type f -name P18_MANIFEST.json -print | sort)
test "${#manifests[@]}" -eq 1
manifest="${manifests[0]}"
rm -rf pretruth && mkdir -p pretruth/checkpoints output
for panel in hdbscan sugar; do
  mapfile -t hits < <(find /tmp/p18-pre -type f -path "*/${panel}.pkl" -print | sort)
  test "${#hits[@]}" -eq 1
  test -f "${hits[0]}.sha256"
  cp "${hits[0]}" "pretruth/checkpoints/${panel}.pkl"
  cp "${hits[0]}.sha256" "pretruth/checkpoints/${panel}.pkl.sha256"
done
printf '%s  %s\n' "$HDB_CP_SHA" pretruth/checkpoints/hdbscan.pkl | sha256sum -c -
printf '%s  %s\n' "$SUGAR_CP_SHA" pretruth/checkpoints/sugar.pkl | sha256sum -c -
test "$(cat pretruth/checkpoints/hdbscan.pkl.sha256)" = "$HDB_CP_SHA"
test "$(cat pretruth/checkpoints/sugar.pkl.sha256)" = "$SUGAR_CP_SHA"
python - "$manifest" "$HDB_CP_SHA" "$SUGAR_CP_SHA" <<'PY_MANIFEST'
import json,sys
path,hdb,sugar=sys.argv[1:]
m=json.load(open(path))
assert m['classification']=='P18_MATCHED_PRETRUTH',m
assert m['p17_matched_source_sha256']=='c0c39d1bd660efbe5e5353b5a33185428a6f60f4a3759be3acd16a15a063012a',m
assert m['p18_transform_blob']=='3f53e1ffeabb1b32d2de124cbf903d193012b9af',m
assert m['primary_matched_challenger']=='P18 only; P17 core-only diagnostic ablation',m
assert m['family_existence_and_rank_core_only'] is True and m['reported_membership_exact_frozen_label_free_halo'] is True,m
assert m['new_detector_score_distance_threshold_family_proposal_growth_merge_or_rank'] is False,m
assert m['competitor_cluster_values_accessed'] is False and m['known_shower_truth_accessed'] is False,m
assert m['external_data_access'] is False and m['target_information_access'] is False,m
assert m['panels']['hdbscan']['p18_checkpoint_sha256']==hdb,m
assert m['panels']['sugar']['p18_checkpoint_sha256']==sugar,m
print('PASS_P18_MATCHED_TRUTH_PRETRUTH_MANIFEST_FIREWALL')
PY_MANIFEST
python - <<'PY_CP'
import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('p18final','orbittrace_p17_rank_halo_membership_p18/finalize_p18_matched_result.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
for panel in ('hdbscan','sugar'):
    m.checkpoint(Path(f'pretruth/checkpoints/{panel}.pkl'),panel)
print('PASS_P18_MATCHED_TRUTH_BOTH_CHECKPOINTS_FULLY_VALIDATED')
PY_CP

echo PASS_P18_MATCHED_TRUTH_HARD_BARRIER_BEFORE_TRUTH

progress 'RECONSTRUCT EXACT INHERITED POSTFREEZE STAGING + ONE-TIME EVALUATOR'
python orbittrace_p17_rank_halo_membership_p18/prepare_p18_matched_truth_runtime.py \
  --parent orbittrace_support_safe_halo_p15/run_matched_evaluator_after_pretruth.sh \
  --stage-output /tmp/p18_stage.sh \
  --evaluator-output /tmp/p18_evaluator_once.sh
bash -n /tmp/p18_stage.sh
bash -n /tmp/p18_evaluator_once.sh
test "$(grep -Fc 'python -u input/evaluator/evaluate_frozen_blindsafe.py' /tmp/p18_evaluator_once.sh)" -eq 1
if grep -Eq 'OrbitTrace-April|target_coordinate' /tmp/p18_stage.sh /tmp/p18_evaluator_once.sh; then
  echo 'target surface leaked into matched runtime' >&2
  exit 1
fi
chmod +x /tmp/p18_stage.sh /tmp/p18_evaluator_once.sh
/tmp/p18_stage.sh

echo PASS_P18_MATCHED_POSTFREEZE_SOURCE_STAGING_COMPLETE

progress 'OPEN MATCHED TRUTH + COMPETITOR CLUSTER VALUES EXACTLY ONCE'
/tmp/p18_evaluator_once.sh

python /tmp/finalize_p18_p13.py \
  --p3-result output/p3_evaluator_result.json \
  --hdbscan-checkpoint pretruth/checkpoints/hdbscan.pkl \
  --sugar-checkpoint pretruth/checkpoints/sugar.pkl \
  --output output/p13_matched_literature_result.json

python orbittrace_p17_rank_halo_membership_p18/finalize_p18_matched_result.py \
  --base-p14-transport-finalizer orbittrace_support_safe_rank_p14/finalize_p14_matched_result_transport_v3.py \
  --base-p14-finalizer orbittrace_core_halo_p13_literature/finalize_p14_matched_result.py \
  --p13-result output/p13_matched_literature_result.json \
  --hdbscan-checkpoint pretruth/checkpoints/hdbscan.pkl \
  --sugar-checkpoint pretruth/checkpoints/sugar.pkl \
  --output output/p18_matched_literature_result.json

progress 'FINAL FROZEN P18 MATCHED ADVANCEMENT GATE'
python - "$PRE_RUN" "$PRE_ARTIFACT" "$PRE_DIGEST" "$HDB_CP_SHA" "$SUGAR_CP_SHA" <<'PY_FINAL'
import hashlib,json,sys
from pathlib import Path
pre_run,pre_art,pre_digest,hdb_sha,sugar_sha=sys.argv[1:]
r=json.load(open('output/p18_matched_literature_result.json'))
assert r['verdict'] in {'PASS_P18_MATCHED_SPARSE_SUPERIORITY_BOTH_COMPARATORS_BOTH_YEARS','FAIL_P18_MATCHED_SPARSE_SUPERIORITY_NO_GO'},r
assert r['architecture']=='P18_P17_RANK_LABEL_FREE_HALO_MEMBERSHIP',r
assert r['primary_matched_challenger'].startswith('P18 only;'),r
assert r['p18_no_posttruth_core_halo_switch'] is True,r
assert r['sparse_superiority_required_against_both_comparators_in_both_years'] is True,r
assert r['pairwise_only_no_cross_denominator_comparison'] is True and r['broad_only_does_not_authorize_external'] is True,r
assert r['target_access_authorized'] is False,r
passed=r['verdict'].startswith('PASS_')
assert bool(r['external_validation_authorized'])==passed,r
if passed:
    assert all(r['panels'][p]['sparse_pairwise_pass'] and all(r['panels'][p]['year_sparse_pass'].values()) for p in ('hdbscan','sugar')),r
prov={
  'classification':'P18 matched execution provenance',
  'pretruth_run':int(pre_run),
  'pretruth_artifact_id':int(pre_art),
  'pretruth_artifact_digest':pre_digest,
  'hdbscan_checkpoint_sha256':hdb_sha,
  'sugar_checkpoint_sha256':sugar_sha,
  'p17_development_run':31332157812,
  'p17_development_artifact_id':9043232586,
  'p16_architecture_run':31331471689,
  'p16_architecture_artifact_id':9043046136,
  'p17_matched_source_sha256':'c0c39d1bd660efbe5e5353b5a33185428a6f60f4a3759be3acd16a15a063012a',
  'p18_transform_blob':'3f53e1ffeabb1b32d2de124cbf903d193012b9af',
  'matched_result_sha256':hashlib.sha256(Path('output/p18_matched_literature_result.json').read_bytes()).hexdigest(),
  'target_access_authorized':False,
}
Path('output/p18_matched_execution_provenance.json').write_text(json.dumps(prov,indent=2,sort_keys=True)+'\n')
print('P18_MATCHED_FINAL_BEGIN'); print(json.dumps(r,indent=2,sort_keys=True)); print('P18_MATCHED_FINAL_END')
PY_FINAL
