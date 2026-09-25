#!/usr/bin/env bash
set -euo pipefail

BASE='orbittrace_core_halo_p13_literature/run_p13_matched_launcher_v5.sh'
SPLIT='orbittrace_core_halo_p13_literature/split_strict_manifest.py'
SCHEMA_NOTE='orbittrace_core_halo_p13_literature/SNMV3_HEADER_COUNT_GUARD_CORRECTION.md'
OUT='/tmp/run_p13_matched_launcher_v7_generated.sh'
SPLIT_OUT='/tmp/split_strict_manifest_v7.py'

test -f "$BASE" -a -f "$SPLIT" -a -f "$SCHEMA_NOTE"
test "$(git hash-object "$BASE")" = '8bb5da25f850e743d654c800a6bb2b6a41e29ce2'
grep -F '2accb52e550da95b9855038ed68304b05c747c92' "$SCHEMA_NOTE"
grep -F 'SNMv3 header too short for required pinned fields' "$SCHEMA_NOTE"

curl -L --fail --retry 3 -H "Authorization: Bearer $GH_TOKEN" -H 'Accept: application/vnd.github+json' \
  "https://api.github.com/repos/$GITHUB_REPOSITORY/actions/artifacts/9040984565" -o /tmp/v6-pretruth-meta.json
python - <<'PY'
import json
m=json.load(open('/tmp/v6-pretruth-meta.json'))
assert m['id']==9040984565,m
assert m['name']=='orbittrace-p13-matched-literature-launcher-v6',m
assert m['workflow_run']['id']==31323952130,m
assert m['digest']=='sha256:52e9382cf9267c1e8926f96d5c4b7e1230cd28a791e9a52365c61ceb17b358c9',m
assert not m['expired'],m
print('PASS_P13_V7_V6_PRETRUTH_ARTIFACT_METADATA')
PY

python - "$SPLIT" "$SPLIT_OUT" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]).read_text()
stale='8e7580c52e41e6996d6e46f289a7b916565a4efc512c5549ee83f249d0e81ee3'
correct='8e7580c52e41e6994d6e46f289a7b916565a4efc512c5549ee83f249d0e81ee3'
if p.count(stale)!=1: raise SystemExit(f'v7 split-helper stale SHA count={p.count(stale)}')
p=p.replace(stale,correct,1)
if stale in p: raise SystemExit('stale HDBSCAN-2025 SHA survived v7 split helper')
Path(sys.argv[2]).write_text(p)
print('PASS_P13_V7_SPLIT_HELPER_SINGLE_PROVENANCE_CORRECTION')
PY
python -m py_compile "$SPLIT_OUT"

python - "$BASE" "$OUT" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]).read_text()

def once(old,new,label):
    global p
    n=p.count(old)
    if n!=1: raise SystemExit(f'v7 wrapper anchor {label} count={n}')
    p=p.replace(old,new,1)

once("OUT='/tmp/run_p13_matched_launcher_v5_inner.sh'","OUT='/tmp/run_p13_matched_launcher_v7_inner.sh'",'inner path')
if p.count('LAUNCH_V5.md')!=2: raise SystemExit(f"v7 LAUNCH_V5 path count={p.count('LAUNCH_V5.md')}")
p=p.replace('LAUNCH_V5.md','LAUNCH_V7.md')
if p.count('LAUNCH_P13_MATCHED_TECHNICAL_RECOVERY_V5')!=2: raise SystemExit('v7 V5 activation marker count changed')
p=p.replace('LAUNCH_P13_MATCHED_TECHNICAL_RECOVERY_V5','LAUNCH_P13_MATCHED_TECHNICAL_RECOVERY_V7')
once('31323275459','31323952130','parent technical run marker')

anchor="Path(sys.argv[2]).write_text(src)"
injection=r'''split_old="python orbittrace_core_halo_p13_literature/split_strict_manifest.py --input pretruth/strict_manifest.json --output-dir pretruth/strict\n"
split_new="echo '1c6960eb8dd1c29e1787dd3cd2da58ca0397c73dc21c432caa5b15c2cc1f3204  pretruth/strict_manifest.json' | sha256sum -c -\ntest \"$(cat pretruth/strict_manifest.json.sha256)\" = 'e7a5dbe6b974d60486d94a5e763b992f97035f0d5b1b0a4e47aba5bddfa92b6e'\npython /tmp/split_strict_manifest_v7.py --input pretruth/strict_manifest.json --output-dir pretruth/strict\necho '23891b5af09b271416e00aa9edbdc7be32dcfbef79af893308541a6574ef8090  pretruth/strict/hdbscan_2023.json' | sha256sum -c -\necho '95d7a85461fdc2b97f8f92a9bc5f937b41ad3c0fc8cd46c5f5dae52440a356ac  pretruth/strict/hdbscan_2025.json' | sha256sum -c -\necho '08968b485aad5723c25929b8a22beacfa497e4ee554dfe0ba2cdd44b8bb3d769  pretruth/strict/sugar_2023.json' | sha256sum -c -\necho '4ea49b397f6b62825d8f41453a4fe995f576198b50ee501106f2cef1727d4747  pretruth/strict/sugar_2025.json' | sha256sum -c -\ntest \"$(cat pretruth/strict/hdbscan_2023.json.sha256)\" = '6c8126809f4c98c10d51d3d3d5e56dc47241205cafaea467c79f73c1117f48c2'\ntest \"$(cat pretruth/strict/hdbscan_2025.json.sha256)\" = 'daadf3b235250bfbb0cb728c4f2520a9aac6c33d56a19bb0c6d87faab0d63d9b'\ntest \"$(cat pretruth/strict/sugar_2023.json.sha256)\" = '3a87c9403402d74065ff8c860b6f3b5450d6383df710edb491a3a1ee99973c33'\ntest \"$(cat pretruth/strict/sugar_2025.json.sha256)\" = '98be22c0d9c03c11ae2dd75e0eb6c0931ed3c9d60bb5cd5ce74007128d0c7263'\n"
if src.count(split_old)!=1: raise SystemExit(f'v7 split invocation anchor count={src.count(split_old)}')
src=src.replace(split_old,split_new,1)

compile_old="python -m py_compile /tmp/prepare_p13_panel_v2.py /tmp/p12_panel.py input/source/prepare_strict_id_manifest.py input/source/read_exact_orbits.py\n"
compile_new="test \"$(git hash-object input/source/read_exact_orbits.py)\" = '2accb52e550da95b9855038ed68304b05c747c92'\npython - <<'PY_READER'\nfrom pathlib import Path\np=Path('input/source/read_exact_orbits.py')\nt=p.read_text()\nold=\"            require(len(header)==EXPECTED_HEADER_COUNTS[year],f'SNMv3 header count changed {year}: {len(header)}')\\n\"\nnew=\"            require(len(header)>max(EXPECTED_SHARED_INDICES.values()),f'SNMv3 header too short for required pinned fields {year}: {len(header)}')\\n\"\nif t.count(old)!=1: raise SystemExit(f'orbit-reader header-count anchor count={t.count(old)}')\nt=t.replace(old,new,1)\np.write_text(t)\nprint('PASS_P13_V7_ORBIT_READER_TOTAL_COUNT_GUARD_ONLY_CORRECTED')\nPY_READER\npython -m py_compile /tmp/prepare_p13_panel_v2.py /tmp/p12_panel.py input/source/prepare_strict_id_manifest.py input/source/read_exact_orbits.py\n"
if src.count(compile_old)!=1: raise SystemExit(f'v7 orbit-reader compile anchor count={src.count(compile_old)}')
src=src.replace(compile_old,compile_new,1)
'''
once(anchor,injection+anchor,'strict-manifest + orbit-reader continuation injection')
p=p.replace('P13_V5','P13_V7').replace('v5 marker anchor','v7 marker anchor').replace('v5 transport anchor','v7 transport anchor').replace('v5 inherited stale SHA','v7 inherited stale SHA').replace('v5 correction','v7 correction')
Path(sys.argv[2]).write_text(p)
print('PASS_P13_V7_WRAPPER_PRETRUTH_SCHEMA_CONTINUATION_TRANSFORM')
PY

bash -n "$OUT"
grep -F 'LAUNCH_P13_MATCHED_TECHNICAL_RECOVERY_V7' "$OUT"
grep -F '23891b5af09b271416e00aa9edbdc7be32dcfbef79af893308541a6574ef8090  pretruth/strict/hdbscan_2023.json' "$OUT"
grep -F 'PASS_P13_V7_ORBIT_READER_TOTAL_COUNT_GUARD_ONLY_CORRECTED' "$OUT"
grep -F "require(len(header)>max(EXPECTED_SHARED_INDICES.values())" "$OUT"
chmod +x "$OUT"
exec "$OUT"
