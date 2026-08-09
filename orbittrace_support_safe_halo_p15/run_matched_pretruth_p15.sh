#!/usr/bin/env bash
set -euo pipefail

: "${GH_TOKEN:?GH_TOKEN required}"
: "${BASE_SHA:?BASE_SHA required}"
: "${HEAD_SHA:?HEAD_SHA required}"
: "${GITHUB_REPOSITORY:?GITHUB_REPOSITORY required}"

MARKER='orbittrace_support_safe_halo_p15/P15_MATCHED_PRETRUTH_RUN.md'
GEN='orbittrace_support_safe_halo_p15/generate_matched_pretruth_p15.py'
V3='orbittrace_core_halo_p13_literature/run_p13_matched_launcher_v3.sh'
OUT='/tmp/p15_matched_pretruth.sh'
SCIENCE_HEAD='7e7cd5b26addb2bea8daef50ce6d86388521ea46'
P15_DEV_SOURCE_SHA='22d34131e873825ca60aefbba0b92088f19f57f589fe629bfbd3b7041d160b4b'
P15_MATCHED_SOURCE_SHA='23d309f6702ed0aa6769381963ea64701ae59c97376a0bae536b527fbc978fe6'
DEV_ARTIFACT_NAME='orbittrace-p15-support-safe-halo-development-v2'

progress(){ printf '\n===== %s =====\n' "$*"; }

progress 'ONE-FILE ACTIVATION + EXACT P15 DEVELOPMENT PASS ARTIFACT'
git fetch --no-tags origin "$BASE_SHA" "$HEAD_SHA"
mapfile -t changed < <(git diff --name-only "$BASE_SHA" "$HEAD_SHA")
test "${#changed[@]}" -eq 1
test "${changed[0]}" = "$MARKER"
marker="$(git show "$HEAD_SHA:$MARKER")"
test "$(printf '%s\n' "$marker" | sed -n '1p')" = 'EXECUTE_P15_MATCHED_PRETRUTH_AFTER_EXACT_DEVELOPMENT_PASS'
DEV_RUN="$(printf '%s\n' "$marker" | sed -n '2p')"
DEV_ARTIFACT="$(printf '%s\n' "$marker" | sed -n '3p')"
DEV_DIGEST="$(printf '%s\n' "$marker" | sed -n '4p')"
test "$(printf '%s\n' "$marker" | sed -n '5p')" = "$SCIENCE_HEAD"
test "$(printf '%s\n' "$marker" | wc -l)" -eq 5
[[ "$DEV_RUN" =~ ^[0-9]+$ ]]
[[ "$DEV_ARTIFACT" =~ ^[0-9]+$ ]]
[[ "$DEV_DIGEST" =~ ^sha256:[0-9a-f]{64}$ ]]

curl -L --fail --retry 3 -H "Authorization: Bearer $GH_TOKEN" -H 'Accept: application/vnd.github+json' \
  "https://api.github.com/repos/$GITHUB_REPOSITORY/actions/artifacts/$DEV_ARTIFACT" -o /tmp/p15-dev-meta.json
python - "$DEV_RUN" "$DEV_ARTIFACT" "$DEV_DIGEST" "$DEV_ARTIFACT_NAME" <<'PY_META'
import json,sys
run,aid,digest,name=sys.argv[1],int(sys.argv[2]),sys.argv[3],sys.argv[4]
m=json.load(open('/tmp/p15-dev-meta.json'))
assert m['id']==aid,m
assert m['name']==name,m
assert m['workflow_run']['id']==int(run),m
assert m['digest']==digest,m
assert not m['expired'],m
print('PASS_P15_MATCHED_ACTIVATION_DEVELOPMENT_ARTIFACT_METADATA')
PY_META

curl -L --fail --retry 3 -H "Authorization: Bearer $GH_TOKEN" -H 'Accept: application/vnd.github+json' \
  "https://api.github.com/repos/$GITHUB_REPOSITORY/actions/artifacts/$DEV_ARTIFACT/zip" -o /tmp/p15-dev.zip
printf '%s  %s\n' "${DEV_DIGEST#sha256:}" /tmp/p15-dev.zip | sha256sum -c -
rm -rf /tmp/p15-dev && mkdir -p /tmp/p15-dev && unzip -q /tmp/p15-dev.zip -d /tmp/p15-dev
mapfile -t summaries < <(find /tmp/p15-dev -type f -name support_safe_secondary_halo_p15_development.json -print)
test "${#summaries[@]}" -eq 1
python - "${summaries[0]}" "$P15_DEV_SOURCE_SHA" <<'PY_DEV'
import json,sys
r=json.load(open(sys.argv[1])); source=sys.argv[2]
assert r['verdict']=='PASS_SUPPORT_SAFE_SECONDARY_HALO_P15_DEVELOPMENT',r
assert r['p15_source_sha256']==source,r
assert r['p15_parent_p12_exact_json_identity'] is True,r
assert r['p15_fallback_vacuous_on_development'] is True,r
assert r['directions']==452,r
assert r['unavailable_directions']==0,r
assert r['minimum_negative_count']>=128,r
assert r['matched_truth_access'] is False,r
assert r['external_data_access'] is False,r
assert r['target_information_access'] is False,r
print('PASS_P15_MATCHED_ACTIVATION_EXACT_DEVELOPMENT_SCIENTIFIC_GATE')
PY_DEV

progress 'GENERATE ALREADY-FROZEN P15 PRETRUTH-ONLY SHELL'
test "$(git hash-object "$V3")" = '1fb46484a51bb7d7edd60c865dcf5341550277a1'
python "$GEN" "$V3" "$OUT"
bash -n "$OUT"
grep -F "$P15_MATCHED_SOURCE_SHA" "$OUT"
grep -F 'PASS_P15_BOTH_MATCHED_CHECKPOINTS_FROZEN_BEFORE_TRUTH_OR_CLUSTER_VALUES' "$OUT"
if grep -Fq 'OPEN TRUTH + COMPETITOR CLUSTER VALUES EXACTLY ONCE' "$OUT"; then
  echo 'truth stage survived P15 pretruth generation' >&2
  exit 1
fi
if grep -Eq 'evaluate_frozen_blindsafe.py|finalize_p3_evaluator_result.py|OrbitTrace-April|target_coordinate' "$OUT"; then
  echo 'posttruth or target surface survived P15 pretruth generation' >&2
  exit 1
fi
chmod +x "$OUT"
exec "$OUT"
