#!/usr/bin/env bash
set -euo pipefail

V7='orbittrace_core_halo_p13_literature/run_p13_matched_launcher_v7.sh'
PREP='orbittrace_core_halo_p13_literature/prepare_pretruth_panel_input_p14.py'
CP14='orbittrace_core_halo_p13_literature/finalize_pretruth_checkpoint_p14.py'
OUTER='/tmp/run_p14_via_v7_outer.sh'
P14_COMMIT='213310dc72f691b1558171e8094002ec6b9a7b07'
P14_ARTIFACT=9041190744
P14_DIGEST='sha256:cf0ae11a664a01d274c3b64dc1062789bc84016c00a7958fb470e564fff09f93'

: "${GH_TOKEN:?GH_TOKEN required}"
test -f "$V7" -a -f "$PREP" -a -f "$CP14"
test "$(git hash-object "$V7")" = 'c16ca7fcd15d08f179bca69263d9035c600aeb04'
cp "$PREP" /tmp/prepare_p14_panel.py
cp "$CP14" /tmp/finalize_p14_checkpoint.py
python -m py_compile /tmp/prepare_p14_panel.py /tmp/finalize_p14_checkpoint.py

git fetch --no-tags --depth=1 origin "$P14_COMMIT"
git show FETCH_HEAD:orbittrace_support_safe_rank_p14/support_safe_rank.py > /tmp/p14_support_safe_rank.py
test "$(git hash-object /tmp/p14_support_safe_rank.py)" = 'dfb58023ce26583a532ea5342cde051ff288d44c'
python -m py_compile /tmp/p14_support_safe_rank.py

curl -L --fail --retry 3 -H "Authorization: Bearer $GH_TOKEN" -H 'Accept: application/vnd.github+json' \
  "https://api.github.com/repos/$GITHUB_REPOSITORY/actions/artifacts/$P14_ARTIFACT" -o /tmp/p14-dev-meta.json
python - <<'PY'
import json
m=json.load(open('/tmp/p14-dev-meta.json'))
assert m['id']==9041190744,m
assert m['name']=='orbittrace-support-safe-multiplicity-rank-p14-development',m
assert m['workflow_run']['id']==31324724895,m
assert m['digest']=='sha256:cf0ae11a664a01d274c3b64dc1062789bc84016c00a7958fb470e564fff09f93',m
assert not m['expired'],m
print('PASS_P14_MATCHED_AUTHORITATIVE_DEVELOPMENT_ARTIFACT')
PY

python - "$V7" "$OUTER" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]).read_text()
needle='chmod +x "$OUT"\nexec "$OUT"\n'
if p.count(needle)!=1: raise SystemExit(f'P14 v7 terminal anchor count={p.count(needle)}')
replacement=r'''chmod +x "$OUT"
python - "$OUT" <<'PY_P14_INNER'
from pathlib import Path
import sys
p=Path(sys.argv[1]).read_text()

def once(old,new,label):
    global p
    n=p.count(old)
    if n!=1: raise SystemExit(f'P14 inner anchor {label} count={n}')
    p=p.replace(old,new,1)

once("cp orbittrace_core_halo_p13_literature/prepare_pretruth_panel_input_v2.py /tmp/prepare_p13_panel_v2.py\n","cp /tmp/prepare_p14_panel.py /tmp/prepare_p13_panel_v2.py\n",'prepare source')
once("    --orbit-reader input/source/read_exact_orbits.py \\\n","    --orbit-reader input/source/read_exact_orbits.py \\\n    --p14-rank-module /tmp/p14_support_safe_rank.py \\\n",'P14 rank argument')
once("  python orbittrace_core_halo_p13_literature/finalize_pretruth_checkpoint.py \\\n","  python /tmp/finalize_p14_checkpoint.py \\\n    --base-finalizer orbittrace_core_halo_p13_literature/finalize_pretruth_checkpoint.py \\\n",'P14 checkpoint finalizer')
post="progress 'POSTFREEZE TRUTH PARSERS + EVALUATOR SOURCE'\n"
pos=p.find(post)
if pos<0: raise SystemExit('P14 posttruth boundary missing')
p=p[:pos]+r'''progress 'P14 HARD TWO-PANEL PRETRUTH BARRIER — STOP BEFORE TRUTH'
python - <<'PY_P14_BARRIER'
import hashlib,pickle,json
from pathlib import Path
for panel in ('hdbscan','sugar'):
    path=Path(f'pretruth/checkpoints/{panel}.pkl'); raw=path.read_bytes(); side=path.with_suffix(path.suffix+'.sha256')
    assert side.read_text().strip()==hashlib.sha256(raw).hexdigest()
    c=pickle.loads(raw)
    assert c['classification']=='P3 matched-literature pretruth panel checkpoint'
    assert c['p14_architecture']=='P14_SUPPORT_SAFE_MULTIPLICITY_RANK'
    assert c['p14_source_commit']=='213310dc72f691b1558171e8094002ec6b9a7b07'
    assert c['p14_support_blob']=='dfb58023ce26583a532ea5342cde051ff288d44c'
    assert c['p14_development_artifact_id']==9041190744
    assert c['p14_development_artifact_digest']=='sha256:cf0ae11a664a01d274c3b64dc1062789bc84016c00a7958fb470e564fff09f93'
    assert c['p14_rank_frozen_before_truth'] is True and c['p14_no_fabricated_score'] is True and c['p14_episode_size_128_unchanged'] is True
    assert c['competitor_cluster_values_accessed'] is False and c['known_shower_truth_accessed'] is False
    rank=c['p14_support_safe_rank']; assert rank['fabricated_scores'] is False and rank['episode_size_relaxed'] is False and rank['episode_size']==128
    assert rank['families_scored']+rank['families_unscorable']==rank['families_requested']==len(c['p3_expanded_families'])
    assert hashlib.sha256(json.dumps(rank,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()==c['p14_support_safe_rank_sha256']
    print('P14_PRETRUTH_PANEL',panel,'families',rank['families_requested'],'scored',rank['families_scored'],'unscorable',rank['families_unscorable'],'rank_sha',c['p14_support_safe_rank_sha256'])
print('PASS_P14_BOTH_MATCHED_CHECKPOINTS_FROZEN_BEFORE_TRUTH_OR_CLUSTER_VALUES')
PY_P14_BARRIER
python --version > pretruth/python_version.txt
sha256sum /tmp/prepare_p13_panel_v2.py /tmp/p14_support_safe_rank.py /tmp/finalize_p14_checkpoint.py > pretruth/p14_source_sha256.txt
exit 0
'''
Path(sys.argv[1]).write_text(p)
print('PASS_P14_MATCHED_PRETRUTH_INNER_TRANSFORM')
PY_P14_INNER
chmod +x "$OUT"
exec "$OUT"
'''
p=p.replace(needle,replacement,1)
Path(sys.argv[2]).write_text(p)
print('PASS_P14_MATCHED_PRETRUTH_OUTER_TRANSFORM')
PY

bash -n "$OUTER"
grep -F 'P14 HARD TWO-PANEL PRETRUTH BARRIER — STOP BEFORE TRUTH' "$OUTER"
chmod +x "$OUTER"
exec "$OUTER"
