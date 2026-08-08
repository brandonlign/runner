#!/usr/bin/env bash
set -euo pipefail
: "${GH_TOKEN:?GH_TOKEN required}"

rm -rf input output_manifest
mkdir -p input/{archives,hdbscan2023,hdbscan2025,sugar2023,sugar2025} output_manifest

gh run download 31226945294 --repo "$GITHUB_REPOSITORY" --name orbittrace-hdbscan-2023-blind-safe-benchmark --dir input/hdbscan2023
gh run download 31071589912 --repo "$GITHUB_REPOSITORY" --name orbittrace-sonotaco-2025-hdbscan-catalogue --dir input/hdbscan2025
gh run download 31076789635 --repo "$GITHUB_REPOSITORY" --name orbittrace-sonotaco-2023-sugar-uncertainty-transfer --dir input/sugar2023
gh run download 31075178517 --repo "$GITHUB_REPOSITORY" --name orbittrace-sonotaco-2025-sugar-uncertainty-catalogue --dir input/sugar2025

echo '35f629b1dff4d04cdc13aa8224171ec1ab8e06b52836900d66ff978b5c235761  input/hdbscan2023/full_catalogue_assignments.jsonl.gz' | sha256sum -c -
echo '8e7580c52e41e6994d6e46f289a7b916565a4efc512c5549ee83f249d0e81ee3  input/hdbscan2025/full_catalogue_assignments.jsonl.gz' | sha256sum -c -
echo '2b9e86572f10af447071cb10c56f643c1ad8babfe0d9aa667994ba3639834389  input/sugar2023/sugar_uncertainty_assignments.json.gz' | sha256sum -c -
echo '77844d700bb14bb9952307fad13eb66cbc62e6a1555e5edd9c8aa0d26968b06e  input/sugar2025/sugar_uncertainty_assignments.json.gz' | sha256sum -c -

curl --fail --location --retry 3 --output input/archives/023a.zip https://www.astro.sk/iaumdcDB/public/data/SNMv3/023a.zip
curl --fail --location --retry 3 --output input/archives/025a.zip https://www.astro.sk/iaumdcDB/public/data/SNMv3/025a.zip
echo '9f44696f99164801ff405dab90f68df3666b0d6734fed464a95e7ed0d6f5f430  input/archives/023a.zip' | sha256sum -c -
echo 'f4eb716a4b900658fcc658a633d918eca28946f59da75935f1fd5f6bc539bf52  input/archives/025a.zip' | sha256sum -c -

python orbittrace_v6_literature_adapter/prepare_id_manifest.py \
  --exact-row-runner runtime/run_exact_row_blind_safe.py \
  --archive-2023 input/archives/023a.zip \
  --archive-2025 input/archives/025a.zip \
  --hdbscan-2023 input/hdbscan2023/full_catalogue_assignments.jsonl.gz \
  --hdbscan-2025 input/hdbscan2025/full_catalogue_assignments.jsonl.gz \
  --sugar-2023 input/sugar2023/sugar_uncertainty_assignments.json.gz \
  --sugar-2025 input/sugar2025/sugar_uncertainty_assignments.json.gz \
  --output output_manifest/id_manifest.json

test -f output_manifest/id_manifest.json
test -f output_manifest/id_manifest.json.sha256
echo PASS_OPTIMIZED_MATCHED_ID_MANIFEST