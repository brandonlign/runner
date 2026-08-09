#!/usr/bin/env bash
set -euo pipefail

: "${GH_TOKEN:?GH_TOKEN required}"
: "${BASE_SHA:?BASE_SHA required}"
: "${HEAD_SHA:?HEAD_SHA required}"
: "${REPO:?REPO required}"

MARKER='orbittrace_core_rank_halo_membership_p16/P16_MATCHED_PRETRUTH_RUN.md'
P15_PRETRUTH_RUN=31331442750
P15_PRETRUTH_HEAD='5d27be8095130484293df962618350e5f25712cc'
P15_PRETRUTH_BRANCH='agent/orbittrace-p15-matched-pretruth-run-artifact-pass-v2'
P15_PRETRUTH_NAME='orbittrace-p15-matched-pretruth-checkpoints'
P16_DEV_RUN=31331471689
P16_DEV_ARTIFACT=9043046136
P16_DEV_NAME='orbittrace-p16-core-rank-halo-membership-canonical-development'
P16_DEV_DIGEST='sha256:fc87c995b489d791b8df279002062b9df601140889f408d4ec3ec3222b91fdc8'
P16_DEV_JSON_SHA='07afd4ecf3b0e6907ca70f62c31f72bc944b861ff7cd75b462acf9cec242b9bb'
P16_DEV_CANONICAL_SHA='5a73952c2f8903b7eddb752054cee5aa46fa48891bb88d6af4bb014bfb61186b'
P16_ADAPTER_BLOB='a143d59be30a03091ae9a46ce169ff9b12280c99'

progress(){ printf '\n===== %s =====\n' "$*"; }

progress 'ONE-FILE P16 PRETRUTH TRANSFORM CHILD'
git fetch --no-tags origin "$BASE_SHA" "$HEAD_SHA"
mapfile -t files < <(git diff --name-only "$BASE_SHA" "$HEAD_SHA")
test "${#files[@]}" -eq 1
test "${files[0]}" = "$MARKER"
marker="$(git show "$HEAD_SHA:$MARKER")"
test "$(printf '%s\n' "$marker" | sed -n '1p')" = 'EXECUTE_P16_MATCHED_PRETRUTH_TRANSFORM_FROM_P15'
test "$(printf '%s\n' "$marker" | sed -n '2p')" = "$P15_PRETRUTH_RUN"
P15_ARTIFACT="$(printf '%s\n' "$marker" | sed -n '3p')"
P15_DIGEST="$(printf '%s\n' "$marker" | sed -n '4p')"
HDB_P15_SHA="$(printf '%s\n' "$marker" | sed -n '5p')"
SUGAR_P15_SHA="$(printf '%s\n' "$marker" | sed -n '6p')"
test "$(printf '%s\n' "$marker" | wc -l)" -eq 6
[[ "$P15_ARTIFACT" =~ ^[0-9]+$ ]]
[[ "$P15_DIGEST" =~ ^sha256:[0-9a-f]{64}$ ]]
[[ "$HDB_P15_SHA" =~ ^[0-9a-f]{64}$ ]]
[[ "$SUGAR_P15_SHA" =~ ^[0-9a-f]{64}$ ]]
git checkout --detach "$BASE_SHA"
test ! -e "$MARKER"
test "$(git hash-object orbittrace_core_rank_halo_membership_p16/promote_halo_membership_checkpoint.py)" = "$P16_ADAPTER_BLOB"
python -m py_compile orbittrace_core_rank_halo_membership_p16/promote_halo_membership_checkpoint.py

progress 'VERIFY EXACT P16 CANONICAL DEVELOPMENT PASS'
curl -L --fail --retry 3 -H "Authorization: Bearer $GH_TOKEN" -H 'Accept: application/vnd.github+json' \
  "https://api.github.com/repos/$REPO/actions/runs/$P16_DEV_RUN" -o /tmp/p16-dev-run.json
curl -L --fail --retry 3 -H "Authorization: Bearer $GH_TOKEN" -H 'Accept: application/vnd.github+json' \
  "https://api.github.com/repos/$REPO/actions/artifacts/$P16_DEV_ARTIFACT" -o /tmp/p16-dev-meta.json
python - <<'PY'
import json
r=json.load(open('/tmp/p16-dev-run.json')); a=json.load(open('/tmp/p16-dev-meta.json'))
assert r['id']==31331471689 and r['status']=='completed' and r['conclusion']=='success',r
assert r['head_sha']=='9feb3269e5c20db109bb5ee36d828354a975dd17',r
assert r['head_branch']=='agent/orbittrace-p16-core-rank-halo-membership-freeze',r
assert a['id']==9043046136 and a['name']=='orbittrace-p16-core-rank-halo-membership-canonical-development',a
assert a['digest']=='sha256:fc87c995b489d791b8df279002062b9df601140889f408d4ec3ec3222b91fdc8' and not a['expired'],a
assert a['workflow_run']['id']==31331471689 and a['workflow_run']['head_sha']=='9feb3269e5c20db109bb5ee36d828354a975dd17',a
PY
curl -L --fail --retry 3 -H "Authorization: Bearer $GH_TOKEN" -H 'Accept: application/vnd.github+json' \
  "https://api.github.com/repos/$REPO/actions/artifacts/$P16_DEV_ARTIFACT/zip" -o /tmp/p16-dev.zip
printf '%s  %s\n' "${P16_DEV_DIGEST#sha256:}" /tmp/p16-dev.zip | sha256sum -c -
rm -rf /tmp/p16-dev && mkdir -p /tmp/p16-dev
unzip -q /tmp/p16-dev.zip -d /tmp/p16-dev
mapfile -t devhits < <(find /tmp/p16-dev -type f -name p16_core_rank_halo_membership_canonical_development.json -print)
test "${#devhits[@]}" -eq 1
printf '%s  %s\n' "$P16_DEV_JSON_SHA" "${devhits[0]}" | sha256sum -c -
test "$(cat "${devhits[0]}.sha256")" = "$P16_DEV_CANONICAL_SHA"
python - "${devhits[0]}" <<'PY'
import json,sys
r=json.load(open(sys.argv[1]))
assert r['verdict']=='PASS_P16_CORE_RANK_HALO_MEMBERSHIP_CANONICAL_DEVELOPMENT_IDENTITY',r
assert r['family_count']==226 and r['already_frozen_halo_additions']==17238,r
assert r['p13_core_pretruth_sha256']=='12e6635085c77c8c705fe225e67811c659e98bf7cd1047649ec2b8d593261b3c',r
assert r['p12_halo_membership_pretruth_sha256']=='f158ebfa3a9a3c8006a7c81cbf0b47f7307aa7f2537e8046621b08037230cca3',r
assert r['new_detector_score_threshold_or_member_proposal'] is False,r
assert r['family_existence_and_rank_core_only'] is True,r
assert r['reported_membership_exact_canonical_label_free_halo'] is True,r
assert r['matched_comparator_access'] is False and r['external_data_access'] is False and r['target_information_access'] is False,r
PY

progress 'VERIFY EXACT P15 PRETRUTH ARTIFACT — NO TRUTH OPENING'
curl -L --fail --retry 3 -H "Authorization: Bearer $GH_TOKEN" -H 'Accept: application/vnd.github+json' \
  "https://api.github.com/repos/$REPO/actions/runs/$P15_PRETRUTH_RUN" -o /tmp/p15-pre-run.json
curl -L --fail --retry 3 -H "Authorization: Bearer $GH_TOKEN" -H 'Accept: application/vnd.github+json' \
  "https://api.github.com/repos/$REPO/actions/artifacts/$P15_ARTIFACT" -o /tmp/p15-pre-meta.json
python - "$P15_ARTIFACT" "$P15_DIGEST" <<'PY'
import json,sys
artifact,digest=sys.argv[1:]
r=json.load(open('/tmp/p15-pre-run.json')); a=json.load(open('/tmp/p15-pre-meta.json'))
assert r['id']==31331442750 and r['status']=='completed' and r['conclusion']=='success',r
assert r['head_sha']=='5d27be8095130484293df962618350e5f25712cc',r
assert r['head_branch']=='agent/orbittrace-p15-matched-pretruth-run-artifact-pass-v2',r
assert a['id']==int(artifact) and a['name']=='orbittrace-p15-matched-pretruth-checkpoints',a
assert a['digest']==digest and not a['expired'],a
assert a['workflow_run']['id']==31331442750 and a['workflow_run']['head_sha']=='5d27be8095130484293df962618350e5f25712cc',a
PY
curl -L --fail --retry 3 -H "Authorization: Bearer $GH_TOKEN" -H 'Accept: application/vnd.github+json' \
  "https://api.github.com/repos/$REPO/actions/artifacts/$P15_ARTIFACT/zip" -o /tmp/p15-pre.zip
printf '%s  %s\n' "${P15_DIGEST#sha256:}" /tmp/p15-pre.zip | sha256sum -c -
rm -rf /tmp/p15-pre && mkdir -p /tmp/p15-pre
unzip -q /tmp/p15-pre.zip -d /tmp/p15-pre
mkdir -p pretruth/p15 pretruth/p16 output
for panel in hdbscan sugar; do
  mapfile -t hits < <(find /tmp/p15-pre -type f -path "*/checkpoints/${panel}.pkl" -print)
  test "${#hits[@]}" -eq 1
  cp "${hits[0]}" "pretruth/p15/${panel}.pkl"
  cp "${hits[0]}.sha256" "pretruth/p15/${panel}.pkl.sha256"
done
printf '%s  %s\n' "$HDB_P15_SHA" pretruth/p15/hdbscan.pkl | sha256sum -c -
printf '%s  %s\n' "$SUGAR_P15_SHA" pretruth/p15/sugar.pkl | sha256sum -c -
test "$(cat pretruth/p15/hdbscan.pkl.sha256)" = "$HDB_P15_SHA"
test "$(cat pretruth/p15/sugar.pkl.sha256)" = "$SUGAR_P15_SHA"

progress 'TRANSFORM FROZEN P15 CHECKPOINTS TO P16 — STILL PRETRUTH'
for panel in hdbscan sugar; do
  python orbittrace_core_rank_halo_membership_p16/promote_halo_membership_checkpoint.py \
    --input "pretruth/p15/${panel}.pkl" --output "pretruth/p16/${panel}.pkl"
done
python - <<'PY'
import hashlib,json,pickle
from pathlib import Path
panels={}
for panel in ('hdbscan','sugar'):
    p=Path(f'pretruth/p16/{panel}.pkl'); raw=p.read_bytes(); cp=pickle.loads(raw)
    assert p.with_suffix(p.suffix+'.sha256').read_text().strip()==hashlib.sha256(raw).hexdigest()
    assert cp['panel']==panel and cp['years']==[2023,2025] and cp['blind_exclusion']==[20.0,55.0]
    assert cp['competitor_cluster_values_accessed'] is False and cp['known_shower_truth_accessed'] is False
    assert cp['p16_architecture']=='P16_CORE_RANK_LABEL_FREE_HALO_MEMBERSHIP'
    assert cp['p16_core_order_unchanged'] is True and cp['p16_membership_frozen_before_truth'] is True
    assert cp['p16_no_new_detector_score_threshold_or_proposal'] is True and cp['p16_new_members_can_seed_growth'] is False
    assert cp['p16_core_order_pretruth_sha256']==cp['v8_order_pretruth_sha256']
    assert cp['p16_reported_membership_pretruth_sha256']==cp['p3_membership_pretruth_sha256']
    panels[panel]={
      'p15_checkpoint_sha256':hashlib.sha256(Path(f'pretruth/p15/{panel}.pkl').read_bytes()).hexdigest(),
      'p16_checkpoint_sha256':hashlib.sha256(raw).hexdigest(),
      'core_order_sha256':cp['p16_core_order_pretruth_sha256'],
      'reported_membership_sha256':cp['p16_reported_membership_pretruth_sha256'],
      'core_halo_correspondence_sha256':cp['p16_core_halo_correspondence_sha256'],
      'already_frozen_halo_additions':cp['p16_total_already_frozen_halo_additions'],
      'p15_unavailable_directions':cp['p15_unavailable_direction_count'],
    }
out={
  'classification':'P16_MATCHED_PRETRUTH_CHECKPOINT_TRANSFORM',
  'p15_pretruth_run_id':31331442750,
  'p16_development_run_id':31331471689,
  'family_existence_and_rank_core_only':True,
  'reported_membership_exact_frozen_p15_p12_halo':True,
  'new_detector_score_threshold_or_member_proposal':False,
  'competitor_cluster_values_accessed':False,
  'known_shower_truth_accessed':False,
  'external_data_access':False,
  'target_information_access':False,
  'panels':panels,
}
Path('output/p16_matched_pretruth_manifest.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
PY

echo PASS_P16_BOTH_MATCHED_CHECKPOINTS_FROZEN_BEFORE_TRUTH_OR_CLUSTER_VALUES
