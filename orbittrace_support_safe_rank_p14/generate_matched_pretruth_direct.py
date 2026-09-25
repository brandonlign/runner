#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

V3_BLOB='1fb46484a51bb7d7edd60c865dcf5341550277a1'
P14_COMMIT='213310dc72f691b1558171e8094002ec6b9a7b07'
P14_BLOB='dfb58023ce26583a532ea5342cde051ff288d44c'


def once(text:str,old:str,new:str,label:str)->str:
    n=text.count(old)
    if n!=1: raise RuntimeError(f'P14 direct transform {label} count={n}')
    return text.replace(old,new,1)


def replace_between(text:str,start:str,end:str,repl:str,label:str)->str:
    i=text.find(start); j=text.find(end,i+len(start)) if i>=0 else -1
    if i<0 or j<0: raise RuntimeError(f'P14 direct transform span missing {label}')
    if text.find(start,i+1)>=0: raise RuntimeError(f'P14 direct transform span nonunique {label}')
    return text[:i]+repl+text[j:]


def main()->int:
    if len(sys.argv)!=3: raise SystemExit('usage: generate_matched_pretruth_direct.py EXACT_V3 OUTPUT')
    src=Path(sys.argv[1]).read_text(); t=src

    guard_start="progress 'TECHNICAL CHILD / SCIENTIFIC ACTIVATION GUARDS'\n"
    prereq="progress 'AUTHORITATIVE P13 DEVELOPMENT PREREQUISITE'\n"
    new_guard=r'''progress 'P14 PRETRUTH CHILD / PROMOTED METHOD GUARDS'
git fetch --no-tags origin "$BASE_SHA" "$HEAD_SHA"
mapfile -t launcher_files < <(git diff --name-only "$BASE_SHA" "$HEAD_SHA")
test "${#launcher_files[@]}" -eq 1
test "${launcher_files[0]}" = 'orbittrace_support_safe_rank_p14/LAUNCH_PRETRUTH.md'
launch_marker="$(git show "$HEAD_SHA":orbittrace_support_safe_rank_p14/LAUNCH_PRETRUTH.md)"
test "$(printf '%s\n' "$launch_marker" | sed -n '1p')" = 'LAUNCH_P14_MATCHED_PRETRUTH_DIRECT_V1'
test "$(printf '%s\n' "$launch_marker" | sed -n '2p')" = '691'
test "$(printf '%s\n' "$launch_marker" | sed -n '3p')" = '31325324850'
test "$(printf '%s\n' "$launch_marker" | wc -l)" -eq 3
cp orbittrace_core_halo_p13_literature/prepare_pretruth_panel_input_p14.py /tmp/prepare_p13_panel_v2.py
cp orbittrace_core_halo_p13_literature/finalize_pretruth_checkpoint_p14.py /tmp/finalize_p14_checkpoint.py
python -m py_compile /tmp/prepare_p13_panel_v2.py /tmp/finalize_p14_checkpoint.py

git fetch --no-tags --depth=1 origin 213310dc72f691b1558171e8094002ec6b9a7b07
git show FETCH_HEAD:orbittrace_support_safe_rank_p14/support_safe_rank.py > /tmp/p14_support_safe_rank.py
test "$(git hash-object /tmp/p14_support_safe_rank.py)" = 'dfb58023ce26583a532ea5342cde051ff288d44c'
python -m py_compile /tmp/p14_support_safe_rank.py

curl -L --fail --retry 3 -H "Authorization: Bearer $GH_TOKEN" -H 'Accept: application/vnd.github+json' "https://api.github.com/repos/$REPO/actions/artifacts/9041190744" -o /tmp/p14-meta.json
python - <<'PY_P14_DEV'
import json
m=json.load(open('/tmp/p14-meta.json'))
assert m['id']==9041190744 and m['name']=='orbittrace-support-safe-multiplicity-rank-p14-development'
assert m['workflow_run']['id']==31324724895
assert m['digest']=='sha256:cf0ae11a664a01d274c3b64dc1062789bc84016c00a7958fb470e564fff09f93' and not m['expired']
print('PASS_P14_DIRECT_AUTHORITATIVE_DEVELOPMENT')
PY_P14_DEV

'''+prereq
    t=replace_between(t,guard_start,prereq,new_guard,'activation/P14 guard')

    compile_anchor="python -m py_compile /tmp/prepare_p13_panel_v2.py /tmp/p12_panel.py input/source/prepare_strict_id_manifest.py input/source/read_exact_orbits.py\n"
    compile_repl=r'''test "$(git hash-object input/source/read_exact_orbits.py)" = '2accb52e550da95b9855038ed68304b05c747c92'
python - <<'PY_READER'
from pathlib import Path
p=Path('input/source/read_exact_orbits.py'); x=p.read_text()
old="            require(len(header)==EXPECTED_HEADER_COUNTS[year],f'SNMv3 header count changed {year}: {len(header)}')\n"
new="            require(len(header)>max(EXPECTED_SHARED_INDICES.values()),f'SNMv3 header too short for required pinned fields {year}: {len(header)}')\n"
assert x.count(old)==1,x.count(old); p.write_text(x.replace(old,new,1)); print('PASS_P14_DIRECT_ORBIT_READER_SCHEMA_CORRECTION')
PY_READER
python -m py_compile /tmp/prepare_p13_panel_v2.py /tmp/p12_panel.py input/source/prepare_strict_id_manifest.py input/source/read_exact_orbits.py
'''
    t=once(t,compile_anchor,compile_repl,'orbit-reader schema correction')

    assign_start="progress 'ASSIGNMENT FILES — ID-ONLY PRETRUTH ACCESS'\n"
    archive_start="progress 'EXACT RAW BENCHMARK ARCHIVES'\n"
    assignment=r'''progress 'ASSIGNMENT FILES — EXACT ARTIFACT ID / ID-ONLY PRETRUTH ACCESS'
fetch_exact_assignment_artifact(){
  local artifact_id="$1" zip_sha="$2" member="$3" member_sha="$4" output="$5" tag="$6"
  local zip="/tmp/${tag}.zip" dir="/tmp/${tag}"
  rm -rf "$dir" "$zip"; mkdir -p "$dir"
  curl -L --fail --retry 3 -H "Authorization: Bearer $GH_TOKEN" -H 'Accept: application/vnd.github+json' "https://api.github.com/repos/$REPO/actions/artifacts/$artifact_id/zip" -o "$zip"
  echo "$zip_sha  $zip" | sha256sum -c -
  unzip -q "$zip" -d "$dir"
  mapfile -t hits < <(find "$dir" -type f -name "$member" -print | sort)
  test "${#hits[@]}" -eq 1
  cp "${hits[0]}" "$output"
  echo "$member_sha  $output" | sha256sum -c -
}
fetch_exact_assignment_artifact 9012424187 2a953a237d32abfed8cfef110689623ec47e9acc9ed15eddee23a39d358d1bd4 full_catalogue_assignments.jsonl.gz 35f629b1dff4d04cdc13aa8224171ec1ab8e06b52836900d66ff978b5c235761 input/hdbscan_2023.jsonl.gz hdbscan2023
fetch_exact_assignment_artifact 8955917326 82e95052eb75349031341ea600aebf8f74d6842f03c0e47edf7cdea6de471a89 full_catalogue_assignments.jsonl.gz 8e7580c52e41e6994d6e46f289a7b916565a4efc512c5549ee83f249d0e81ee3 input/hdbscan_2025.jsonl.gz hdbscan2025
fetch_exact_assignment_artifact 8957940764 ea77c5111a7be51ff2bb45b16df934f7c808c695d08ac12003025de971df4fdf sugar_uncertainty_assignments.json.gz 2b9e86572f10af447071cb10c56f643c1ad8babfe0d9aa667994ba3639834389 input/sugar_2023.json.gz sugar2023
fetch_exact_assignment_artifact 8957263372 9df4a48f4808180d534086e560e68ae56486f60171510207acd7bd6fedeebbc9 sugar_uncertainty_assignments.json.gz 77844d700bb14bb9952307fad13eb66cbc62e6a1555e5edd9c8aa0d26968b06e input/sugar_2025.json.gz sugar2025
python input/source/prepare_strict_id_manifest.py --hdbscan-2023 input/hdbscan_2023.jsonl.gz --hdbscan-2025 input/hdbscan_2025.jsonl.gz --sugar-2023 input/sugar_2023.json.gz --sugar-2025 input/sugar_2025.json.gz --output pretruth/strict_manifest.json
echo '1c6960eb8dd1c29e1787dd3cd2da58ca0397c73dc21c432caa5b15c2cc1f3204  pretruth/strict_manifest.json' | sha256sum -c -
test "$(cat pretruth/strict_manifest.json.sha256)" = 'e7a5dbe6b974d60486d94a5e763b992f97035f0d5b1b0a4e47aba5bddfa92b6e'
python - <<'PY_SPLIT'
from pathlib import Path
p=Path('orbittrace_core_halo_p13_literature/split_strict_manifest.py'); x=p.read_text()
stale='8e7580c52e41e6996d6e46f289a7b916565a4efc512c5549ee83f249d0e81ee3'; correct='8e7580c52e41e6994d6e46f289a7b916565a4efc512c5549ee83f249d0e81ee3'
assert x.count(stale)==1,x.count(stale); Path('/tmp/split_p14.py').write_text(x.replace(stale,correct,1))
print('PASS_P14_DIRECT_SPLIT_PROVENANCE_CORRECTION')
PY_SPLIT
python /tmp/split_p14.py --input pretruth/strict_manifest.json --output-dir pretruth/strict
echo '23891b5af09b271416e00aa9edbdc7be32dcfbef79af893308541a6574ef8090  pretruth/strict/hdbscan_2023.json' | sha256sum -c -
echo '95d7a85461fdc2b97f8f92a9bc5f937b41ad3c0fc8cd46c5f5dae52440a356ac  pretruth/strict/hdbscan_2025.json' | sha256sum -c -
echo '08968b485aad5723c25929b8a22beacfa497e4ee554dfe0ba2cdd44b8bb3d769  pretruth/strict/sugar_2023.json' | sha256sum -c -
echo '4ea49b397f6b62825d8f41453a4fe995f576198b50ee501106f2cef1727d4747  pretruth/strict/sugar_2025.json' | sha256sum -c -
echo PASS_P14_DIRECT_ASSIGNMENT_IDS_FROZEN_CLUSTER_VALUES_UNREAD

'''+archive_start
    t=replace_between(t,assign_start,archive_start,assignment,'exact assignment transport')

    orbit_arg="    --orbit-reader input/source/read_exact_orbits.py \\\n"
    t=once(t,orbit_arg,orbit_arg+"    --p14-rank-module /tmp/p14_support_safe_rank.py \\\n",'P14 rank argument')
    finalize="  python orbittrace_core_halo_p13_literature/finalize_pretruth_checkpoint.py \\\n"
    t=once(t,finalize,"  python /tmp/finalize_p14_checkpoint.py \\\n    --base-finalizer orbittrace_core_halo_p13_literature/finalize_pretruth_checkpoint.py \\\n",'P14 checkpoint finalizer')

    post="progress 'POSTFREEZE TRUTH PARSERS + EVALUATOR SOURCE'\n"
    pos=t.find(post)
    if pos<0: raise RuntimeError('P14 direct posttruth boundary missing')
    barrier=r'''progress 'P14 HARD TWO-PANEL PRETRUTH BARRIER — STOP BEFORE TRUTH'
python - <<'PY_P14_BARRIER'
import hashlib,json,pickle
from pathlib import Path
for panel in ('hdbscan','sugar'):
    p=Path(f'pretruth/checkpoints/{panel}.pkl'); raw=p.read_bytes(); assert p.with_suffix(p.suffix+'.sha256').read_text().strip()==hashlib.sha256(raw).hexdigest()
    c=pickle.loads(raw); assert c['classification']=='P3 matched-literature pretruth panel checkpoint'
    assert c['p14_architecture']=='P14_SUPPORT_SAFE_MULTIPLICITY_RANK' and c['p14_source_commit']=='213310dc72f691b1558171e8094002ec6b9a7b07' and c['p14_support_blob']=='dfb58023ce26583a532ea5342cde051ff288d44c'
    assert c['p14_development_artifact_id']==9041190744 and c['p14_development_artifact_digest']=='sha256:cf0ae11a664a01d274c3b64dc1062789bc84016c00a7958fb470e564fff09f93'
    assert c['p14_rank_frozen_before_truth'] is True and c['p14_no_fabricated_score'] is True and c['p14_episode_size_128_unchanged'] is True
    assert c['competitor_cluster_values_accessed'] is False and c['known_shower_truth_accessed'] is False
    rank=c['p14_support_safe_rank']; assert rank['episode_size']==128 and rank['fabricated_scores'] is False and rank['episode_size_relaxed'] is False
    assert rank['families_scored']+rank['families_unscorable']==rank['families_requested']==len(c['p3_expanded_families'])
    assert hashlib.sha256(json.dumps(rank,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()==c['p14_support_safe_rank_sha256']
    print('P14_PRETRUTH_PANEL',panel,'families',rank['families_requested'],'scored',rank['families_scored'],'unscorable',rank['families_unscorable'],'rank_sha',c['p14_support_safe_rank_sha256'])
print('PASS_P14_BOTH_MATCHED_CHECKPOINTS_FROZEN_BEFORE_TRUTH_OR_CLUSTER_VALUES')
PY_P14_BARRIER
python --version > pretruth/python_version.txt
sha256sum /tmp/prepare_p13_panel_v2.py /tmp/p14_support_safe_rank.py /tmp/finalize_p14_checkpoint.py > pretruth/p14_source_sha256.txt
exit 0
'''
    t=t[:pos]+barrier

    required=(
        'LAUNCH_P14_MATCHED_PRETRUTH_DIRECT_V1','9041190744','dfb58023ce26583a532ea5342cde051ff288d44c',
        'fetch_exact_assignment_artifact 8955917326','8e7580c52e41e6994d6e46f289a7b916565a4efc512c5549ee83f249d0e81ee3',
        '1c6960eb8dd1c29e1787dd3cd2da58ca0397c73dc21c432caa5b15c2cc1f3204','PASS_P14_DIRECT_ORBIT_READER_SCHEMA_CORRECTION',
        '--p14-rank-module /tmp/p14_support_safe_rank.py','/tmp/finalize_p14_checkpoint.py','PASS_P14_BOTH_MATCHED_CHECKPOINTS_FROZEN_BEFORE_TRUTH_OR_CLUSTER_VALUES')
    for x in required:
        if x not in t: raise RuntimeError(f'P14 direct generated invariant missing: {x}')
    forbidden=('OPEN TRUTH + COMPETITOR CLUSTER VALUES EXACTLY ONCE','evaluate_frozen_blindsafe.py','finalize_p3_evaluator_result.py','OrbitTrace-April','target_coordinate')
    for x in forbidden:
        if x in t: raise RuntimeError(f'P14 direct forbidden posttruth/target token survived: {x}')
    Path(sys.argv[2]).write_text(t)
    print('PASS_P14_DIRECT_PRETRUTH_LAUNCHER_GENERATED')
    return 0


if __name__=='__main__': raise SystemExit(main())
