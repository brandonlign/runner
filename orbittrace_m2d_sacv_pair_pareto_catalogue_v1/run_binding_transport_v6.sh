#!/usr/bin/env bash
set -euo pipefail
# Transport-only artifact provenance repair. The frozen scientific code expects
# SACV-v1 pretruth SHA 77528f..., which is artifact run 32324386269. The legacy
# sibling workflow hardcoded a later nonmatching technical attempt 32325172601.
# Intercept only that one gh download and redirect it to the exact frozen oracle.
gh() {
  if [ "$#" -ge 3 ] && [ "$1" = run ] && [ "$2" = download ] && [ "$3" = 32325172601 ]; then
    shift 3
    command gh run download 32324386269 "$@"
  else
    command gh "$@"
  fi
}
export -f gh
# Preinstall the exact versions already pinned by the frozen workflow so the
# label-free Pareto self-audit can import its reconstructed runtime.
python -m pip install --disable-pip-version-check \
  'numpy==2.1.3' 'scipy==1.14.1' 'scikit-learn==1.7.1' \
  'hdbscan==0.8.43' 'gudhi==3.12.0' >/dev/null
exec bash -x orbittrace_m2d_sacv_pair_pareto_catalogue_v1/run_binding_transport_v2.sh
