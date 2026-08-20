#!/usr/bin/env bash
set -euo pipefail
# Transport-only ordering repair: the frozen label-free self-test imports the
# reconstructed runtime before v2 reaches its normal dependency-install step.
# Preinstall the exact versions already specified by the frozen workflow.
python -m pip install --disable-pip-version-check \
  'numpy==2.1.3' 'scipy==1.14.1' 'scikit-learn==1.7.1' \
  'hdbscan==0.8.43' 'gudhi==3.12.0' >/dev/null
exec bash orbittrace_m2d_sacv_pair_pareto_catalogue_v1/run_binding_transport_v2.sh
