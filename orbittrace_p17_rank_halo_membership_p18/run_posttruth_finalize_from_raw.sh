#!/usr/bin/env bash
set -euo pipefail

: "${GH_TOKEN:?GH_TOKEN required}"
: "${BASE_SHA:?BASE_SHA required}"
: "${HEAD_SHA:?HEAD_SHA required}"
: "${REPO:?REPO required}"

MARKER='orbittrace_p17_rank_halo_membership_p18/POSTTRUTH_FINALIZE_RUN.md'
RAW_RUN=31336331539
RAW_ARTIFACT=9044444246
RAW_NAME='orbittrace-p18-matched-literature-result'
RAW_DIGEST='sha256:27d2ad9ec26cc03dff28e9aad047f3a68fd8dd5599411d1e5bc0da7867a70688'
RAW_P3_SHA='ebd7fca2380f544e4c641c9ec1575d4a0845ac23da9b80c32d9d362663125bf9'
RAW_HEAD='5ebe328fb1e860efa0d3202cdecfdac00936c059'
PRE_RUN=31335741430
PRE_ARTIFACT=9044259813
PRE_NAME='orbittrace-p18-matched-pretruth-checkpoints'
PRE_DIGEST='sha256:15b7f7e1de2c7a76902916797fb42636998d48af5b49a65a1d94eec94c3682d4'
HDB_SHA='c17c260af8a5ddd0548cef6a7d8b07b86167ed13ea3731a3adbd7248e570a97a'
SUGAR_SHA='d20bbed792d3491be8db01c2932ae4d9ad471fdfe9b3141fe6b4b0812a684e14'
V2_PREP_BLOB='ae12ee38a73ee3f1b958b3ba61a4ef1eaa31f50d'
P18_FINALIZER_BLOB='9f7b8ea6279434e7243ac9debdbf5d5a4a33aadd'
P14_TRANSPORT_FINALIZER_BLOB='1e9160c7beb5bc7651dc2b9f03db6211bc639ac6'
P14_FINALIZER_BLOB='d1ce98f443b2039d70421e76dadb6ada77d1b0d5'
P13_FINALIZER_BLOB='a5d812b9956742b51e7e3995a71eb308afa7d095'

check_blob(){ local p="$1" e="$2"; test "$(git hash-object "$p")" = "$e"; }
download_exact(){
  local aid="$1" run="$2" name="$3" digest="$4" tag="$5"
  curl -L --fail --retry 3 -H "Authorization: Bearer $GH_TOKEN" -H 'Accept: application/vnd.github+json' \
    "https://api.github.com/repos/$REPO/actions/artifacts/$aid" -o "/tmp/${tag}-meta.json"
  python - "$aid" "$run" "$name" "$digest" "/tmp/${tag}-meta.json" <<'PY'
import json,sys
aid,run,name,digest,path=sys.argv[1:]
a=json.load(open(path))
assert a['id']==int(aid) and a['workflow_run']['id']==int(run),a
assert a['name']==name and a['digest']==digest and not a['expired'],a
PY
  curl -L --fail --retry 3 -H "Authorization: Bearer $GH_TOKEN" -H 'Accept: application/vnd.github+json' \
    "https://api.github.com/repos/$REPO/actions/artifacts/$aid/zip" -o "/tmp/${tag}.zip"
  printf '%s  %s\n' "${digest#sha256:}" "/tmp/${tag}.zip" | sha256sum -c -
  rm -rf "/tmp/${tag}" && mkdir -p "/tmp/${tag}"
  unzip -q "/tmp/${tag}.zip" -d "/tmp/${tag}"
}

git fetch --no-tags origin "$BASE_SHA" "$HEAD_SHA"
mapfile -t files < <(git diff --name-only "$BASE_SHA" "$HEAD_SHA")
test "${#files[@]}" -eq 1
test "${files[0]}" = "$MARKER"
test "$(git show "$HEAD_SHA:$MARKER")" = 'EXECUTE_P18_POSTTRUTH_FINALIZATION_FROM_PINNED_RAW_ARTIFACT'
git checkout --detach "$BASE_SHA"
test ! -e "$MARKER"

check_blob orbittrace_p17_rank_halo_membership_p18/prepare_p18_compatible_p13_finalizer_v2.py "$V2_PREP_BLOB"
check_blob orbittrace_p17_rank_halo_membership_p18/finalize_p18_matched_result.py "$P18_FINALIZER_BLOB"
check_blob orbittrace_support_safe_rank_p14/finalize_p14_matched_result_transport_v3.py "$P14_TRANSPORT_FINALIZER_BLOB"
check_blob orbittrace_core_halo_p13_literature/finalize_p14_matched_result.py "$P14_FINALIZER_BLOB"
check_blob orbittrace_core_halo_p13_literature/finalize_p3_evaluator_result.py "$P13_FINALIZER_BLOB"
python -m py_compile \
  orbittrace_p17_rank_halo_membership_p18/prepare_p18_compatible_p13_finalizer_v2.py \
  orbittrace_p17_rank_halo_membership_p18/finalize_p18_matched_result.py

curl -L --fail --retry 3 -H "Authorization: Bearer $GH_TOKEN" -H 'Accept: application/vnd.github+json' \
  "https://api.github.com/repos/$REPO/actions/runs/$RAW_RUN" -o /tmp/raw-run.json
curl -L --fail --retry 3 -H "Authorization: Bearer $GH_TOKEN" -H 'Accept: application/vnd.github+json' \
  "https://api.github.com/repos/$REPO/actions/runs/$PRE_RUN" -o /tmp/pre-run.json
download_exact "$RAW_ARTIFACT" "$RAW_RUN" "$RAW_NAME" "$RAW_DIGEST" raw
download_exact "$PRE_ARTIFACT" "$PRE_RUN" "$PRE_NAME" "$PRE_DIGEST" pre
python - <<'PY'
import json
raw=json.load(open('/tmp/raw-run.json')); pre=json.load(open('/tmp/pre-run.json'))
assert raw['id']==31336331539 and raw['status']=='completed' and raw['conclusion']=='failure',raw
assert raw['head_sha']=='5ebe328fb1e860efa0d3202cdecfdac00936c059',raw
assert raw['head_branch']=='agent/orbittrace-p18-matched-truth-run-v1',raw
assert raw['name']=='OrbitTrace P18 one-time matched truth opening',raw
assert pre['id']==31335741430 and pre['status']=='completed' and pre['conclusion']=='success',pre
assert pre['name']=='OrbitTrace P18 matched pretruth checkpoint transform',pre
print('PASS_P18_POSTTRUTH_PINNED_RUN_METADATA')
PY

mapfile -t rawhits < <(find /tmp/raw -type f -name p3_evaluator_result.json -print | sort)
test "${#rawhits[@]}" -eq 1
printf '%s  %s\n' "$RAW_P3_SHA" "${rawhits[0]}" | sha256sum -c -
mkdir -p input output pretruth/checkpoints
cp "${rawhits[0]}" input/p3_evaluator_result.json
mapfile -t hh < <(find /tmp/pre -type f -path '*/hdbscan.pkl' -print | sort)
mapfile -t sh < <(find /tmp/pre -type f -path '*/sugar.pkl' -print | sort)
test "${#hh[@]}" -eq 1 && test "${#sh[@]}" -eq 1
cp "${hh[0]}" pretruth/checkpoints/hdbscan.pkl
cp "${hh[0]}.sha256" pretruth/checkpoints/hdbscan.pkl.sha256
cp "${sh[0]}" pretruth/checkpoints/sugar.pkl
cp "${sh[0]}.sha256" pretruth/checkpoints/sugar.pkl.sha256
printf '%s  %s\n' "$HDB_SHA" pretruth/checkpoints/hdbscan.pkl | sha256sum -c -
printf '%s  %s\n' "$SUGAR_SHA" pretruth/checkpoints/sugar.pkl | sha256sum -c -

python orbittrace_p17_rank_halo_membership_p18/prepare_p18_compatible_p13_finalizer_v2.py \
  orbittrace_core_halo_p13_literature/finalize_p3_evaluator_result.py /tmp/finalize_p18_p13_v2.py
python -m py_compile /tmp/finalize_p18_p13_v2.py
python /tmp/finalize_p18_p13_v2.py \
  --p3-result input/p3_evaluator_result.json \
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

python - <<'PY'
import hashlib,json
from pathlib import Path
raw=json.load(open('input/p3_evaluator_result.json'))
out=json.load(open('output/p18_matched_literature_result.json'))
passed=bool(raw['sparse_stream_superiority'])
assert out['verdict']==('PASS_P18_MATCHED_SPARSE_SUPERIORITY_BOTH_COMPARATORS_BOTH_YEARS' if passed else 'FAIL_P18_MATCHED_SPARSE_SUPERIORITY_NO_GO'),out
assert bool(out['external_validation_authorized'])==passed,out
assert out['target_access_authorized'] is False,out
assert out['sparse_superiority_required_against_both_comparators_in_both_years'] is True,out
assert out['p18_no_posttruth_core_halo_switch'] is True,out
prov={
 'classification':'P18 artifact-only posttruth finalization',
 'raw_truth_run':31336331539,
 'raw_truth_artifact_id':9044444246,
 'raw_truth_artifact_digest':'sha256:27d2ad9ec26cc03dff28e9aad047f3a68fd8dd5599411d1e5bc0da7867a70688',
 'raw_p3_evaluator_sha256':'ebd7fca2380f544e4c641c9ec1575d4a0845ac23da9b80c32d9d362663125bf9',
 'pretruth_run':31335741430,
 'pretruth_artifact_id':9044259813,
 'p18_checkpoint_sha256':{'hdbscan':'c17c260af8a5ddd0548cef6a7d8b07b86167ed13ea3731a3adbd7248e570a97a','sugar':'d20bbed792d3491be8db01c2932ae4d9ad471fdfe9b3141fe6b4b0812a684e14'},
 'posttruth_repair':'add missed checkpoint output-role assertion to already-frozen P18 P13 compatibility finalizer',
 'scientific_gate_math_changed':False,
 'detector_or_membership_recomputed':False,
 'comparator_truth_reopened':False,
 'external_data_access':False,
 'target_information_access':False,
 'final_result_sha256':hashlib.sha256(Path('output/p18_matched_literature_result.json').read_bytes()).hexdigest(),
}
Path('output/p18_posttruth_finalization_provenance.json').write_text(json.dumps(prov,indent=2,sort_keys=True)+'\n')
print('PASS_P18_ARTIFACT_ONLY_POSTTRUTH_FINALIZATION')
print(json.dumps(out,indent=2,sort_keys=True))
PY
