#!/usr/bin/env bash
set -euo pipefail

SRC='orbittrace_support_safe_rank_p14/run_matched_pretruth_v1.sh'
OUT='/tmp/run_matched_pretruth_v2_fixed.sh'
test -f "$SRC"
test "$(git hash-object "$SRC")" = 'e1c84941458dbb018f5ab8c903629965c3a4eb19'

python - "$SRC" "$OUT" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]).read_text()
open_old="replacement=r'''chmod +x \"$OUT\"\n"
open_new='replacement=r"""chmod +x "$OUT"\n'
if p.count(open_old)!=1:
    raise SystemExit(f'P14 v2 outer quote open anchor count={p.count(open_old)}')
p=p.replace(open_old,open_new,1)
close_old="exec \"$OUT\"\n'''\np=p.replace(needle,replacement,1)"
close_new='exec "$OUT"\n"""\np=p.replace(needle,replacement,1)'
if p.count(close_old)!=1:
    raise SystemExit(f'P14 v2 outer quote close anchor count={p.count(close_old)}')
p=p.replace(close_old,close_new,1)
Path(sys.argv[2]).write_text(p)
print('PASS_P14_PRETRUTH_V2_NESTED_QUOTE_FIX_ONLY')
PY

bash -n "$OUT"
grep -F 'replacement=r"""chmod +x "$OUT"' "$OUT"
grep -F "p=p[:pos]+r'''progress 'P14 HARD TWO-PANEL PRETRUTH BARRIER — STOP BEFORE TRUTH'" "$OUT"
chmod +x "$OUT"
exec "$OUT"
