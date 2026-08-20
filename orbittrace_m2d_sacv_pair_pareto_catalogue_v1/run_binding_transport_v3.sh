#!/usr/bin/env bash
set -euo pipefail
# Transport-only ordering repair: the frozen Pareto equivalence self-test imports
# the reconstructed runtime, which imports NumPy. Install the exact already-pinned
# NumPy version before delegating to the unchanged v2 binding runner.
python -m pip install --disable-pip-version-check 'numpy==2.1.3' >/dev/null
exec bash orbittrace_m2d_sacv_pair_pareto_catalogue_v1/run_binding_transport_v2.sh
