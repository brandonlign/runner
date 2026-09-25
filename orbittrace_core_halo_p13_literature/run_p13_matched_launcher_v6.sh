#!/usr/bin/env bash
set -euo pipefail

BASE='orbittrace_core_halo_p13_literature/run_p13_matched_launcher_v5.sh'
SPLIT='orbittrace_core_halo_p13_literature/split_strict_manifest.py'
CHECKPOINT='orbittrace_core_halo_p13_literature/STRICT_MANIFEST_V5_CHECKPOINT.md'
OUT='/tmp/run_p13_matched_launcher_v6_generated.sh'
SPLIT_OUT='/tmp/split_strict_manifest_v6.py'

test -f "$BASE" -a -f "$SPLIT" -a -f "$CHECKPOINT"
test "$(git hash-object "$BASE")" = '8bb5da25f850e743d654c800a6bb2b6a41e29ce2'
grep -F '9040867805' "$CHECKPOINT"
grep -F '1c6960eb8dd1c29e1787dd3cd2da58ca0397c73dc21c432caa5b15c2cc1f3204' "$CHECKPOINT"
grep -F 'e7a5dbe6b974d60486d94a5e763b992f97035f0d5b1b0a4e47aba5bddfa92b6e' "$CHECKPOINT"

curl -L --fail --retry 3 -H "Authorization: Bearer $GH_TOKEN" -H 'Accept: application/vnd.github+json' \
  "https://api.github.com/repos/$GITHUB_REPOSITORY/actions/artifacts/9040867805" -o /tmp/v5-checkpoint-meta.json
python - <<'PY'
import json
m=json.load(open('/tmp/v5-checkpoint-meta.json'))
assert m['id']==9040867805,m
assert m['name']=='orbittrace-p13-matched-literature-launcher-v5',m
assert m['workflow_run']['id']==31323525922,m
assert m['digest']=='sha256:dd8728116992ff82451df94e2f296fdcce0e83e833ec4fe725639c24a0b2dd41',m
assert not m['expired'],m
print('PASS_P13_V6_V5_STRICT_MANIFEST_ARTIFACT_METADATA')
PY

python - "$SPLIT" "$SPLIT_OUT" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]).read_text()
stale='8e7580c52e41e6996d6e46f289a7b916565a4efc512c5549ee83f249d0e81ee3'
correct='8e7580c52e41e6994d6e46f289a7b916565a4efc512c5549ee83f249d0e81ee3'
if p.count(stale)!=1: raise SystemExit(f'v6 split-helper stale SHA count={p.count(stale)}')
p=p.replace(stale,correct,1)
if stale in p: raise SystemExit('stale HDBSCAN-2025 SHA survived v6 split helper')
Path(sys.argv[2]).write_text(p)
print('PASS_P13_V6_SPLIT_HELPER_SINGLE_PROVENANCE_CORRECTION')
PY
python -m py_compile "$SPLIT_OUT"

python - "$BASE" "$OUT" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]).read_text()

def once(old,new,label):
    global p
    n=p.count(old)
    if n!=1: raise SystemExit(f'v6 wrapper anchor {label} count={n}')
    p=p.replace(old,new,1)

once("OUT='/tmp/run_p13_matched_launcher_v5_inner.sh'","OUT='/tmp/run_p13_matched_launcher_v6_inner.sh'",'inner path')
if p.count('LAUNCH_V5.md')!=2: raise SystemExit(f"v6 LAUNCH_V5 path count={p.count('LAUNCH_V5.md')}")
p=p.replace('LAUNCH_V5.md','LAUNCH_V6.md')
if p.count('LAUNCH_P13_MATCHED_TECHNICAL_RECOVERY_V5')!=2: raise SystemExit('v6 V5 activation marker count changed')
p=p.replace('LAUNCH_P13_MATCHED_TECHNICAL_RECOVERY_V5','LAUNCH_P13_MATCHED_TECHNICAL_RECOVERY_V6')
once('31323275459','31323525922','parent run marker')

anchor="Path(sys.argv[2]).write_text(src)"
injection=r'''split_old="python orbittrace_core_halo_p13_literature/split_strict_manifest.py --input pretruth/strict_manifest.json --output-dir pretruth/strict\n"
split_new="echo '1c6960eb8dd1c29e1787dd3cd2da58ca0397c73dc21c432caa5b15c2cc1f3204  pretruth/strict_manifest.json' | sha256sum -c -\ntest \"$(cat pretruth/strict_manifest.json.sha256)\" = 'e7a5dbe6b974d60486d94a5e763b992f97035f0d5b1b0a4e47aba5bddfa92b6e'\npython /tmp/split_strict_manifest_v6.py --input pretruth/strict_manifest.json --output-dir pretruth/strict\n"
if src.count(split_old)!=1: raise SystemExit(f'v6 split invocation anchor count={src.count(split_old)}')
src=src.replace(split_old,split_new,1)
'''
once(anchor,injection+anchor,'split continuation injection')
p=p.replace('P13_V5','P13_V6').replace('v5 marker anchor','v6 marker anchor').replace('v5 transport anchor','v6 transport anchor').replace('v5 inherited stale SHA','v6 inherited stale SHA').replace('v5 correction','v6 correction')
Path(sys.argv[2]).write_text(p)
print('PASS_P13_V6_WRAPPER_FROZEN_MANIFEST_CONTINUATION_TRANSFORM')
PY

bash -n "$OUT"
grep -F 'LAUNCH_P13_MATCHED_TECHNICAL_RECOVERY_V6' "$OUT"
grep -F '1c6960eb8dd1c29e1787dd3cd2da58ca0397c73dc21c432caa5b15c2cc1f3204  pretruth/strict_manifest.json' "$OUT"
grep -F 'python /tmp/split_strict_manifest_v6.py' "$OUT"
chmod +x "$OUT"
exec "$OUT"
