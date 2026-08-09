#!/usr/bin/env bash
set -euo pipefail

: "${GH_TOKEN:?GH_TOKEN required}"
: "${BASE_SHA:?BASE_SHA required}"
: "${HEAD_SHA:?HEAD_SHA required}"
: "${REPO:?REPO required}"

MARKER='orbittrace_support_safe_halo_p15/MATCHED_PRETRUTH_RUN.md'
DEV_RUN=31329529635
DEV_ARTIFACT=9042508082
DEV_ARTIFACT_NAME='orbittrace-p15-support-safe-halo-development-artifact-adjudication'
DEV_ZIP_DIGEST='sha256:f6bee693dfd64f86fcbb7fa2b3760a9258d712d5df29c59e270233d87a6a160f'
DEV_RESULT_SHA='0424308527eb5edb7ec21043f1b7721472ebe5aeaa2f5f7f604185b1e09d006e'
P15_MATCHED_SOURCE_SHA='23d309f6702ed0aa6769381963ea64701ae59c97376a0bae536b527fbc978fe6'

P13_V3_BLOB='1fb46484a51bb7d7edd60c865dcf5341550277a1'
P14_GEN_V3_BLOB='af257d4b4902f9783acecd6df52f111415e5188c'
P15_GEN_BLOB='372f1a57d97e1b0f0ac8f1303ef84f242245bdde'
P15_FINALIZER_BLOB='42fac298751179e5e629431060a1c9d803b1f19d'

progress(){ printf '\n===== %s =====\n' "$*"; }

check_blob(){
  local path="$1" expected="$2" actual
  test -f "$path"
  actual="$(git hash-object "$path")"
  printf 'PIN_BLOB path=%s expected=%s actual=%s\n' "$path" "$expected" "$actual"
  test "$actual" = "$expected"
}

progress 'ONE-FILE CHILD / ARTIFACT-ONLY DEVELOPMENT GATE'
git fetch --no-tags origin "$BASE_SHA" "$HEAD_SHA"
mapfile -t files < <(git diff --name-only "$BASE_SHA" "$HEAD_SHA")
test "${#files[@]}" -eq 1
test "${files[0]}" = "$MARKER"
marker="$(git show "$HEAD_SHA:$MARKER")"
test "$(printf '%s\n' "$marker" | sed -n '1p')" = 'EXECUTE_P15_MATCHED_PRETRUTH_AFTER_ARTIFACT_ONLY_DEVELOPMENT_PASS'
test "$(printf '%s\n' "$marker" | sed -n '2p')" = "$DEV_RUN"
test "$(printf '%s\n' "$marker" | sed -n '3p')" = "$DEV_ARTIFACT"
test "$(printf '%s\n' "$marker" | sed -n '4p')" = "$DEV_ZIP_DIGEST"
test "$(printf '%s\n' "$marker" | sed -n '5p')" = "$DEV_RESULT_SHA"
test "$(printf '%s\n' "$marker" | sed -n '6p')" = "$P15_MATCHED_SOURCE_SHA"
test "$(printf '%s\n' "$marker" | wc -l)" -eq 6

# Execute only frozen base code; the head contributes only the marker above.
git checkout --detach "$BASE_SHA"
test ! -e "$MARKER"

progress 'SOLE ADMISSIBLE P15 DEVELOPMENT PROMOTION ARTIFACT'
curl -L --fail --retry 3 -H "Authorization: Bearer $GH_TOKEN" -H 'Accept: application/vnd.github+json' \
  "https://api.github.com/repos/$REPO/actions/runs/$DEV_RUN" -o /tmp/p15-dev-run.json
curl -L --fail --retry 3 -H "Authorization: Bearer $GH_TOKEN" -H 'Accept: application/vnd.github+json' \
  "https://api.github.com/repos/$REPO/actions/artifacts/$DEV_ARTIFACT" -o /tmp/p15-dev-artifact.json
curl -L --fail --retry 3 -H "Authorization: Bearer $GH_TOKEN" -H 'Accept: application/vnd.github+json' \
  "https://api.github.com/repos/$REPO/actions/artifacts/$DEV_ARTIFACT/zip" -o /tmp/p15-dev.zip
printf '%s  %s\n' "${DEV_ZIP_DIGEST#sha256:}" /tmp/p15-dev.zip | sha256sum -c -
rm -rf /tmp/p15-dev && mkdir -p /tmp/p15-dev
unzip -q /tmp/p15-dev.zip -d /tmp/p15-dev
python - "$DEV_RUN" "$DEV_ARTIFACT" "$DEV_ARTIFACT_NAME" "$DEV_ZIP_DIGEST" "$DEV_RESULT_SHA" <<'PY_DEV'
import hashlib,json,sys
from pathlib import Path
run_id,artifact_id,name,digest,result_sha=sys.argv[1:]
run=json.load(open('/tmp/p15-dev-run.json')); art=json.load(open('/tmp/p15-dev-artifact.json'))
assert run['id']==int(run_id) and run['status']=='completed' and run['conclusion']=='success',run
assert run['head_branch']=='agent/orbittrace-p15-development-artifact-adjudication-run-v2',run
assert art['id']==int(artifact_id) and art['name']==name and art['workflow_run']['id']==int(run_id),art
assert art['digest']==digest and not art['expired'],art
hits=list(Path('/tmp/p15-dev').rglob('support_safe_secondary_halo_p15_development_artifact_adjudication.json'))
assert len(hits)==1,hits
raw=hits[0].read_bytes(); assert hashlib.sha256(raw).hexdigest()==result_sha
r=json.loads(raw)
assert r['verdict']=='PASS_SUPPORT_SAFE_SECONDARY_HALO_P15_DEVELOPMENT',r
assert r['adjudication_mode']=='artifact_only_from_immutable_canonical_P12_P13',r
assert r['p15_development_source_sha256']=='22d34131e873825ca60aefbba0b92088f19f57f589fe629bfbd3b7041d160b4b',r
assert r['fixed_min_direction_negatives']==128 and r['canonical_direction_count']==452,r
assert r['canonical_minimum_negative_count']==2197,r
assert r['p15_unavailable_direction_count']==0 and r['p15_unavailable_directions']==[],r
assert r['p15_availability_sha256']=='4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945',r
assert r['p15_fallback_vacuous_on_development'] is True,r
assert r['p15_no_padding_resampling_or_relaxation'] is True and r['p15_secondary_characterization_only'] is True,r
assert r['canonical_p12_result_sha256']=='96698c1a7ba700716a79e7bc8b7bc9acb2f9aec653095a5d7e33b14000b87a38',r
assert r['canonical_p13_result_sha256']=='d298cebec624c991c4abda9dc809d92d8eea101baaf2b6edbb1862b7acc49739',r
assert r['canonical_p13_core_pretruth_sha256']=='12e6635085c77c8c705fe225e67811c659e98bf7cd1047649ec2b8d593261b3c',r
assert r['canonical_p13_halo_pretruth_sha256']=='f158ebfa3a9a3c8006a7c81cbf0b47f7307aa7f2537e8046621b08037230cca3',r
assert r['new_truth_query'] is False and r['matched_truth_access'] is False and r['external_data_access'] is False and r['target_information_access'] is False,r
print('PASS_P15_MATCHED_ARTIFACT_ONLY_DEVELOPMENT_GATE')
PY_DEV

progress 'EXPLICIT FROZEN PRETRUTH SOURCE IDENTITIES'
check_blob orbittrace_core_halo_p13_literature/run_p13_matched_launcher_v3.sh "$P13_V3_BLOB"
check_blob orbittrace_support_safe_rank_p14/generate_matched_pretruth_direct_v3.py "$P14_GEN_V3_BLOB"
check_blob orbittrace_support_safe_halo_p15/generate_matched_pretruth_p15.py "$P15_GEN_BLOB"
check_blob orbittrace_support_safe_halo_p15/finalize_pretruth_checkpoint_p15.py "$P15_FINALIZER_BLOB"
grep -F "MATCHED_P15_SHA256='$P15_MATCHED_SOURCE_SHA'" orbittrace_support_safe_halo_p15/apply_support_safe_halo_p15.py

test -f orbittrace_support_safe_halo_p15/P15_POSTHOC_TOLERANCE_ADJUDICATION_NO_GO.md
test ! -e orbittrace_support_safe_halo_p15/adjudicate_development_semantic_v3.py
test ! -e .github/workflows/orbittrace_p15_semantic_development_adjudication_v3.yml

echo PASS_P15_MATCHED_EXPLICIT_SOURCE_GUARDS

progress 'GENERATE P15 PRETRUTH-ONLY SHELL'
python orbittrace_support_safe_halo_p15/generate_matched_pretruth_p15.py \
  orbittrace_core_halo_p13_literature/run_p13_matched_launcher_v3.sh /tmp/p15_matched_pretruth.sh
bash -n /tmp/p15_matched_pretruth.sh
for token in \
  'PASS_P15_MATCHED_SUPPORT_SAFE_HALO_SOURCE_ACTIVE' \
  'PASS_P14_BOTH_MATCHED_CHECKPOINTS_FROZEN_BEFORE_TRUTH_OR_CLUSTER_VALUES' \
  'p15_halo_availability_frozen_before_truth' \
  'exit 0'; do
  grep -F "$token" /tmp/p15_matched_pretruth.sh
done
if grep -Eq 'OPEN TRUTH \+ COMPETITOR CLUSTER VALUES EXACTLY ONCE|evaluate_frozen_blindsafe.py|finalize_p3_evaluator_result.py|OrbitTrace-April|target_coordinate' /tmp/p15_matched_pretruth.sh; then
  echo 'posttruth or target surface survived generated P15 pretruth shell' >&2
  exit 1
fi

echo PASS_P15_MATCHED_GENERATED_SHELL_PRETRUTH_ONLY
chmod +x /tmp/p15_matched_pretruth.sh
exec /tmp/p15_matched_pretruth.sh
