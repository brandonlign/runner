#!/usr/bin/env bash
set -euo pipefail
# Transport-only diagnostic/binding wrapper. Install the exact dependency set
# required by the label-free self-test, then execute the unchanged v2 runner
# with shell tracing so any remaining plumbing failure is identified exactly.
python -m pip install --disable-pip-version-check \
  'numpy==2.1.3' 'scipy==1.14.1' 'scikit-learn==1.7.1' \
  'hdbscan==0.8.43' 'gudhi==3.12.0' >/dev/null
exec bash -x orbittrace_m2d_sacv_pair_pareto_catalogue_v1/run_binding_transport_v2.sh
