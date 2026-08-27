#!/usr/bin/env bash
set -euo pipefail

: "${GH_TOKEN:?GH_TOKEN required}"
: "${BASE_SHA:?BASE_SHA required}"
: "${HEAD_SHA:?HEAD_SHA required}"
: "${GITHUB_REPOSITORY:?GITHUB_REPOSITORY required}"

MARKER='orbittrace_support_safe_halo_p15/P15_DEVELOPMENT_ARTIFACT_ADJUDICATION_RUN.md'
ADJ='orbittrace_support_safe_halo_p15/adjudicate_development_artifact_only.py'
P12_ARTIFACT=9035003746
P12_RUN=31302353678
P12_NAME='orbittrace-drift-conditioned-two-view-membership-p12-development'
P12_DIGEST='sha256:4b13435ede6f95bf33c016642cc20f932bf45db58e10a5576f316234c29d8cd7'
P12_JSON_SHA='96698c1a7ba700716a79e7bc8b7bc9acb2f9aec653095a5d7e33b14000b87a38'
P13_ARTIFACT=9035081147
P13_RUN=31303078223
P13_NAME='orbittrace-dual-output-core-halo-p13-development'
P13_DIGEST='sha256:efd9c047fb195800d88da3409fb3765e265becb6d0483367e46b8f232658956a'
P13_JSON_SHA='d298cebec624c991c4abda9dc809d92d8eea101baaf2b6edbb1862b7acc49739'
ADJ_BLOB='84cda1e10fedc750fff03c29b3d91c356483b4f7'

progress(){ printf '\n===== %s =====\n' "$*"; }

progress 'ONE-FILE ARTIFACT-ONLY DEVELOPMENT ACTIVATION'
git fetch --no-tags origin "$BASE_SHA" "$HEAD_SHA"
mapfile -t changed < <(git diff --name-only "$BASE_SHA" "$HEAD_SHA")
test "${#changed[@]}" -eq 1
test "${changed[0]}" = "$MARKER"
marker="$(git show "$HEAD_SHA:$MARKER")"
test "$(printf '%s\n' "$marker" | sed -n '1p')" = 'EXECUTE_P15_DEVELOPMENT_ARTIFACT_ONLY_ADJUDICATION'
test "$(printf '%s\n' "$marker" | sed -n '2p')" = 'P12_9035003746_P13_9035081147'
test "$(printf '%s\n' "$marker" | wc -l)" -eq 2
test "$(git hash-object "$ADJ")" = "$ADJ_BLOB"
python -m py_compile "$ADJ"

git checkout --detach "$BASE_SHA"
test ! -e "$MARKER"
test "$(git hash-object "$ADJ")" = "$ADJ_BLOB"
mkdir -p /tmp/p15-artifact-adjudication/{p12,p13} output

fetch_exact(){
  local aid="$1" run="$2" name="$3" digest="$4" tag="$5"
  curl -L --fail --retry 3 -H "Authorization: Bearer $GH_TOKEN" -H 'Accept: application/vnd.github+json' \
    "https://api.github.com/repos/$GITHUB_REPOSITORY/actions/artifacts/$aid" -o "/tmp/p15-artifact-adjudication/${tag}-meta.json"
  python - "$aid" "$run" "$name" "$digest" "/tmp/p15-artifact-adjudication/${tag}-meta.json" <<'PY_META'
import json,sys
aid,run,name,digest,path=sys.argv[1:]
m=json.load(open(path))
assert m['id']==int(aid),m
assert m['workflow_run']['id']==int(run),m
assert m['name']==name,m
assert m['digest']==digest,m
assert not m['expired'],m
PY_META
  curl -L --fail --retry 3 -H "Authorization: Bearer $GH_TOKEN" -H 'Accept: application/vnd.github+json' \
    "https://api.github.com/repos/$GITHUB_REPOSITORY/actions/artifacts/$aid/zip" -o "/tmp/p15-artifact-adjudication/${tag}.zip"
  printf '%s  %s\n' "${digest#sha256:}" "/tmp/p15-artifact-adjudication/${tag}.zip" | sha256sum -c -
  unzip -q "/tmp/p15-artifact-adjudication/${tag}.zip" -d "/tmp/p15-artifact-adjudication/${tag}"
}

progress 'DOWNLOAD ONLY IMMUTABLE CANONICAL P12/P13 ARTIFACTS'
fetch_exact "$P12_ARTIFACT" "$P12_RUN" "$P12_NAME" "$P12_DIGEST" p12
fetch_exact "$P13_ARTIFACT" "$P13_RUN" "$P13_NAME" "$P13_DIGEST" p13
mapfile -t p12hits < <(find /tmp/p15-artifact-adjudication/p12 -type f -name drift_conditioned_two_view_membership_p12_development.json -print)
mapfile -t p13hits < <(find /tmp/p15-artifact-adjudication/p13 -type f -name dual_output_core_halo_p13_development.json -print)
test "${#p12hits[@]}" -eq 1
test "${#p13hits[@]}" -eq 1
printf '%s  %s\n' "$P12_JSON_SHA" "${p12hits[0]}" | sha256sum -c -
printf '%s  %s\n' "$P13_JSON_SHA" "${p13hits[0]}" | sha256sum -c -

echo PASS_P15_ARTIFACT_ONLY_CANONICAL_INPUTS_PINNED

progress 'ADJUDICATE P15 DEVELOPMENT WITHOUT RERUN OR NEW TRUTH'
python "$ADJ" \
  --canonical-p12 "${p12hits[0]}" \
  --canonical-p13 "${p13hits[0]}" \
  --output output/support_safe_secondary_halo_p15_development_artifact_adjudication.json

grep -F '"verdict": "PASS_SUPPORT_SAFE_SECONDARY_HALO_P15_DEVELOPMENT"' output/support_safe_secondary_halo_p15_development_artifact_adjudication.json
python - <<'PY'
import json
r=json.load(open('output/support_safe_secondary_halo_p15_development_artifact_adjudication.json'))
assert r['adjudication_mode']=='artifact_only_from_immutable_canonical_P12_P13'
assert r['canonical_direction_count']==452
assert r['canonical_minimum_negative_count']>=128
assert r['p15_unavailable_direction_count']==0 and r['p15_unavailable_directions']==[]
assert r['p15_fallback_vacuous_on_development'] is True
assert r['new_truth_query'] is False and r['matched_truth_access'] is False and r['external_data_access'] is False and r['target_information_access'] is False
print('PASS_P15_ARTIFACT_ONLY_DEVELOPMENT_FINAL_GATE')
PY
sha256sum "$ADJ" > output/p15_artifact_adjudicator_source_sha256.txt
