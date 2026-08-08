#!/usr/bin/env bash
set -euo pipefail

cd frozen-v6
python orbittrace_wavelet_catalogue_v3/audit_development_source.py
echo 'ef3e69317af59fdac7a030edc77f742fc4772473d7f16b719b5d804cd4117f51  /tmp/run_wavelet_catalogue_v3_development.py' | sha256sum -c -
cat orbittrace_v3_catalogue_v6/exact_parts/part*.b64 | tr -d '\n\r' | base64 --decode | gzip --decompress > /tmp/v6.frozen.py
echo 'a139802f328e0721a6b48b9b41e098660d03e0e218cec49f1d6251981a2828c9  /tmp/v6.frozen.py' | sha256sum -c -
cd ..
PYTHONPATH=execution python - <<'PY'
from pathlib import Path
from orbittrace_v6_checkpointed_fallback.common import apply_exact_two_line_repair
d=apply_exact_two_line_repair(Path('/tmp/v6.frozen.py'),Path('/tmp/v6.repaired.py'))
assert d=='257aab9d0f4d710a1b62af6088cfb9c0939062018d44dbacd074b4e7898eaa24',d
print('PASS_SHARD0_RESCUE_EXACT_RUNTIME',d)
PY
