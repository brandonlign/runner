#!/usr/bin/env bash
set -euo pipefail

SRC='orbittrace_core_halo_p13_literature/run_p13_matched_launcher_v3.sh'
OUT='/tmp/run_p13_matched_launcher_v5_inner.sh'
NOTE='orbittrace_core_halo_p13_literature/HDBSCAN_2025_ASSIGNMENT_SHA_CORRECTION.md'

test -f "$SRC" -a -f "$NOTE"
test "$(git hash-object "$SRC")" = '1fb46484a51bb7d7edd60c865dcf5341550277a1'
grep -F '8e7580c52e41e6994d6e46f289a7b916565a4efc512c5549ee83f249d0e81ee3' "$NOTE"
grep -F '8955917326' "$NOTE"
grep -F '82e95052eb75349031341ea600aebf8f74d6842f03c0e47edf7cdea6de471a89' "$NOTE"

python - "$SRC" "$OUT" <<'PY'
from pathlib import Path
import sys
src=Path(sys.argv[1]).read_text()

old_marker="""test \"${launcher_files[0]}\" = 'orbittrace_core_halo_p13_literature/LAUNCH_V3.md'\nlaunch_marker=\"$(git show \"$HEAD_SHA\":orbittrace_core_halo_p13_literature/LAUNCH_V3.md)\"\ntest \"$(printf '%s\\n' \"$launch_marker\" | sed -n '1p')\" = 'LAUNCH_P13_MATCHED_TECHNICAL_RECOVERY_V3'\ntest \"$(printf '%s\\n' \"$launch_marker\" | sed -n '2p')\" = '674'\ntest \"$(printf '%s\\n' \"$launch_marker\" | sed -n '3p')\" = '31305824131'\n"""
new_marker="""test \"${launcher_files[0]}\" = 'orbittrace_core_halo_p13_literature/LAUNCH_V5.md'\nlaunch_marker=\"$(git show \"$HEAD_SHA\":orbittrace_core_halo_p13_literature/LAUNCH_V5.md)\"\ntest \"$(printf '%s\\n' \"$launch_marker\" | sed -n '1p')\" = 'LAUNCH_P13_MATCHED_TECHNICAL_RECOVERY_V5'\ntest \"$(printf '%s\\n' \"$launch_marker\" | sed -n '2p')\" = '674'\ntest \"$(printf '%s\\n' \"$launch_marker\" | sed -n '3p')\" = '31323275459'\n"""
if src.count(old_marker)!=1: raise SystemExit(f'v5 marker anchor count={src.count(old_marker)}')
src=src.replace(old_marker,new_marker,1)

old_transport="""gh run download 31226945294 --repo \"$REPO\" --name orbittrace-hdbscan-2023-blind-safe-benchmark --dir input/competitors/hdbscan2023\ngh run download 31071589912 --repo \"$REPO\" --name orbittrace-sonotaco-2025-hdbscan-catalogue --dir input/competitors/hdbscan2025\ngh run download 31076789635 --repo \"$REPO\" --name orbittrace-sonotaco-2023-sugar-uncertainty-transfer --dir input/competitors/sugar2023\ngh run download 31075178517 --repo \"$REPO\" --name orbittrace-sonotaco-2025-sugar-uncertainty-catalogue --dir input/competitors/sugar2025\ncp \"$(find input/competitors/hdbscan2023 -type f -name full_catalogue_assignments.jsonl.gz -print -quit)\" input/hdbscan_2023.jsonl.gz\ncp \"$(find input/competitors/hdbscan2025 -type f -name full_catalogue_assignments.jsonl.gz -print -quit)\" input/hdbscan_2025.jsonl.gz\ncp \"$(find input/competitors/sugar2023 -type f -name sugar_uncertainty_assignments.json.gz -print -quit)\" input/sugar_2023.json.gz\ncp \"$(find input/competitors/sugar2025 -type f -name sugar_uncertainty_assignments.json.gz -print -quit)\" input/sugar_2025.json.gz\n"""
new_transport="""fetch_exact_assignment_artifact(){\n  local artifact_id=\"$1\" zip_sha=\"$2\" member=\"$3\" member_sha=\"$4\" output=\"$5\" tag=\"$6\"\n  local zip=\"/tmp/${tag}.zip\" dir=\"/tmp/${tag}\"\n  rm -rf \"$dir\" \"$zip\"; mkdir -p \"$dir\"\n  curl -L --fail --retry 3 -H \"Authorization: Bearer $GH_TOKEN\" -H 'Accept: application/vnd.github+json' \\\n    \"https://api.github.com/repos/$REPO/actions/artifacts/$artifact_id/zip\" -o \"$zip\"\n  echo \"$zip_sha  $zip\" | sha256sum -c -\n  unzip -q \"$zip\" -d \"$dir\"\n  mapfile -t hits < <(find \"$dir\" -type f -name \"$member\" -print | sort)\n  test \"${#hits[@]}\" -eq 1\n  cp \"${hits[0]}\" \"$output\"\n  echo \"$member_sha  $output\" | sha256sum -c -\n}\nfetch_exact_assignment_artifact 9012424187 2a953a237d32abfed8cfef110689623ec47e9acc9ed15eddee23a39d358d1bd4 full_catalogue_assignments.jsonl.gz 35f629b1dff4d04cdc13aa8224171ec1ab8e06b52836900d66ff978b5c235761 input/hdbscan_2023.jsonl.gz hdbscan2023\nfetch_exact_assignment_artifact 8955917326 82e95052eb75349031341ea600aebf8f74d6842f03c0e47edf7cdea6de471a89 full_catalogue_assignments.jsonl.gz 8e7580c52e41e6994d6e46f289a7b916565a4efc512c5549ee83f249d0e81ee3 input/hdbscan_2025.jsonl.gz hdbscan2025\nfetch_exact_assignment_artifact 8957940764 ea77c5111a7be51ff2bb45b16df934f7c808c695d08ac12003025de971df4fdf sugar_uncertainty_assignments.json.gz 2b9e86572f10af447071cb10c56f643c1ad8babfe0d9aa667994ba3639834389 input/sugar_2023.json.gz sugar2023\nfetch_exact_assignment_artifact 8957263372 9df4a48f4808180d534086e560e68ae56486f60171510207acd7bd6fedeebbc9 sugar_uncertainty_assignments.json.gz 77844d700bb14bb9952307fad13eb66cbc62e6a1555e5edd9c8aa0d26968b06e input/sugar_2025.json.gz sugar2025\n"""
if src.count(old_transport)!=1: raise SystemExit(f'v5 transport anchor count={src.count(old_transport)}')
src=src.replace(old_transport,new_transport,1)

stale='8e7580c52e41e6996d6e46f289a7b916565a4efc512c5549ee83f249d0e81ee3'
correct='8e7580c52e41e6994d6e46f289a7b916565a4efc512c5549ee83f249d0e81ee3'
if src.count(stale)!=1: raise SystemExit(f'v5 inherited stale SHA count={src.count(stale)}')
src=src.replace(stale,correct,1)
if stale in src: raise SystemExit('stale HDBSCAN-2025 SHA survived v5 correction')
Path(sys.argv[2]).write_text(src)
print('PASS_P13_V5_EXACT_TRANSPORT_PLUS_SINGLE_PRETRUTH_SHA_CORRECTION')
PY

chmod +x "$OUT"
grep -F "LAUNCH_P13_MATCHED_TECHNICAL_RECOVERY_V5" "$OUT"
grep -F "8e7580c52e41e6994d6e46f289a7b916565a4efc512c5549ee83f249d0e81ee3  input/hdbscan_2025.jsonl.gz" "$OUT"
if grep -Fq '8e7580c52e41e6996d6e46f289a7b916565a4efc512c5549ee83f249d0e81ee3' "$OUT"; then
  echo 'stale HDBSCAN-2025 SHA survived generated v5 launcher' >&2
  exit 1
fi
exec "$OUT"
