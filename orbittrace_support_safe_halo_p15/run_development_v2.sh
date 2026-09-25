#!/usr/bin/env bash
set -euo pipefail

: "${GH_TOKEN:?GH_TOKEN required}"
: "${GITHUB_REPOSITORY:?GITHUB_REPOSITORY required}"

P15_SHA='22d34131e873825ca60aefbba0b92088f19f57f589fe629bfbd3b7041d160b4b'
P12_ARTIFACT=9035003746
P12_ARTIFACT_DIGEST='4b13435ede6f95bf33c016642cc20f932bf45db58e10a5576f316234c29d8cd7'
P13_ARTIFACT=9035081147
P13_ARTIFACT_DIGEST='efd9c047fb195800d88da3409fb3765e265becb6d0483367e46b8f232658956a'

progress(){ printf '\n===== %s =====\n' "$*"; }

progress 'RECONSTRUCT EXACT P12 PARENT + PINNED P15 CHILD'
mkdir -p input/{v3,v6,v8,dsh} output /tmp/p15-canonical/{p12,p13}
python orbittrace_crossyear_two_view_membership_p2/apply_protocol_compliance_patch.py orbittrace_crossyear_two_view_membership_p2/run_development.py /tmp/p2a.py
python orbittrace_crossyear_two_view_membership_p2/apply_protocol_precision_patch_v2.py /tmp/p2a.py /tmp/p2.py
echo 'f19500f6b0dfe481d845af57f3b4d7ec35e678e2191388b7ff4611f8fb2c4eeb  /tmp/p2.py' | sha256sum -c -
python orbittrace_crossfit_seed_floor_membership_p3/apply_p3_patch_v2.py /tmp/p2.py /tmp/p3.py
echo 'f6c4c5a76b8b3f35d434aed4f1fb15035be05c40d0e0531c343ff620f3ba8185  /tmp/p3.py' | sha256sum -c -
python orbittrace_dual_view_seed_envelope_p4/apply_p4_patch.py /tmp/p3.py /tmp/p4.py
echo '290c4f1b6401eaab6f182760eaeaa2f91cc994854febf465f58f7cacc5d73b2a  /tmp/p4.py' | sha256sum -c -
python orbittrace_joint_seed_support_p5/apply_p5_patch.py /tmp/p4.py /tmp/p5.py
echo 'b48b3e6a45a7a371eb8e73c70ee217a33a96c596c61b51ebb7dc9c7b60100456  /tmp/p5.py' | sha256sum -c -
python orbittrace_same_model_crossfit_p6/apply_p6_patch.py /tmp/p5.py /tmp/p6.py
echo 'd32648136b58e2f777912d6403d9de3cbd091a8c23e16aedcda0b146f09f38c2  /tmp/p6.py' | sha256sum -c -
python orbittrace_finite_sample_robust_floor_p7/apply_p7_patch.py /tmp/p6.py /tmp/p7.py
echo '89cf23c9d58692aedfaf12a9c2b7de4a08d641e6326794d82872f2e18608df54  /tmp/p7.py' | sha256sum -c -
python orbittrace_full_finite_sample_order_stat_p8/apply_p8_patch.py /tmp/p7.py /tmp/p8.py
echo 'd3bdcdaf18639e36cc02f5106b3a3c816f5e51eb19543f425717ba1c48a26470  /tmp/p8.py' | sha256sum -c -
python orbittrace_bidirectional_reliability_p9/apply_p9_patch.py /tmp/p8.py /tmp/p9.py
echo '58330c61cf4039f07e80a9746d00eb7281b4e28e674a131d6333e6378695ae31  /tmp/p9.py' | sha256sum -c -
python orbittrace_floor_consistent_geometry_p10/apply_p10_patch.py /tmp/p9.py /tmp/p10.py
echo '638b4f41e51955436557a99f1142c3d3cea91e12a66e2f74925c6bfb79d5e50d  /tmp/p10.py' | sha256sum -c -
python orbittrace_density_contrast_p11/apply_p11_patch.py /tmp/p10.py /tmp/p11.py
echo '914913d0462ea6793af3836cef945f14a03cca205ac0755ed6cdadb63b8752f9  /tmp/p11.py' | sha256sum -c -
python orbittrace_drift_conditioned_p12/apply_p12_patch.py /tmp/p11.py /tmp/p12_parent.py
echo '78e93b5af19a441bc58b00428d2b356218b33f7a4a891a640dd59cb5d4599c32  /tmp/p12_parent.py' | sha256sum -c -
python orbittrace_support_safe_halo_p15/apply_support_safe_halo_p15.py /tmp/p12_parent.py /tmp/run_p12.py
echo "$P15_SHA  /tmp/run_p12.py" | sha256sum -c -
python -m py_compile /tmp/run_p12.py orbittrace_support_safe_halo_p15/adjudicate_development_v2.py

progress 'PIN EXACT DEVELOPMENT INPUTS'
python orbittrace_wavelet_catalogue_v3/audit_development_source.py
echo 'ef3e69317af59fdac7a030edc77f742fc4772473d7f16b719b5d804cd4117f51  /tmp/run_wavelet_catalogue_v3_development.py' | sha256sum -c -
test "$(git -C exact-v8 rev-parse HEAD)" = 'c9d6c44704013ba0c9430100e98a29a56b453304'
test "$(git -C exact-v8 hash-object orbittrace_pooled_year_centroid_v8/run_development.py)" = 'f248df78e1258b132b41aecca6a985a5eb782654'

git fetch --no-tags --depth=1 origin d8258581af143308495bd97bedcc142abbbd951a
git show FETCH_HEAD:orbittrace_multi_anchor_energy_v3/multi_anchor_energy_v3.py > input/v3/multi_anchor_energy_v3.py
test "$(git hash-object input/v3/multi_anchor_energy_v3.py)" = '2ba4835db23f8f623cdd28d0a4e6113b7954ecb2'
cp exact-v8/orbittrace_wavelet_catalogue_v3/wavelet_episode_comparator.py input/v3/wavelet_episode_comparator.py
test "$(git hash-object input/v3/wavelet_episode_comparator.py)" = '493fcc7f2d2cc75ee35acf17e142e7ce7c1e03e8'

curl -L --fail --retry 3 -H "Authorization: Bearer $GH_TOKEN" -H 'Accept: application/vnd.github+json' \
  "https://api.github.com/repos/$GITHUB_REPOSITORY/actions/artifacts/9005846925/zip" -o input/v6.zip
echo '3c636b05cbfc88c6d6b2b8289b309412174b0025c305ae2f2532678927b2232b  input/v6.zip' | sha256sum -c -
unzip -q input/v6.zip -d input/v6
echo 'f76b8448f299ccf078fc5978c0890b9a084f131080db8d2136b5e6dba77edc7b  input/v6/label_free_sparse_support_v6_families.json.gz' | sha256sum -c -

curl -L --fail --retry 3 -H "Authorization: Bearer $GH_TOKEN" -H 'Accept: application/vnd.github+json' \
  "https://api.github.com/repos/$GITHUB_REPOSITORY/actions/artifacts/9009728299/zip" -o input/v8.zip
echo '88d2d607e05d027015c338f7e23b64a6195e55ae24f1b2ac745f5e9bc6df599e  input/v8.zip' | sha256sum -c -
unzip -q input/v8.zip -d input/v8
echo 'fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b  input/v8/pooled_year_centroid_v8_development.json' | sha256sum -c -

git fetch --no-tags --depth=1 origin agent/orbittrace-literature-comparison-2023-replication
git show FETCH_HEAD:orbittrace_literature_comparison/literature_comparators.py > input/dsh/literature_comparators.py
echo '85cd11afbdebc4a0315ebf1daf42d10d4993d7ab088dd05301e3234b18340a5a  input/dsh/literature_comparators.py' | sha256sum -c -
python -m py_compile input/dsh/literature_comparators.py
echo PASS_P15_V2_EXACT_DEVELOPMENT_INPUT_IDENTITIES

progress 'EXECUTE FROZEN TARGET-EXCLUDED P15 DEVELOPMENT'
export PYTHONPATH='exact-v8:input/v3:orbittrace_wavelet_catalogue_v3:.'
python -u orbittrace_drift_conditioned_p12/run_header_compatible.py \
  --base-runner /tmp/run_wavelet_catalogue_v3_development.py \
  --support-source-parts orbittrace_fixed4_support_wrapper_development/source_parts \
  --candidate-payload sonotaco_fixed4_final_development/candidate.py.gz.b64 \
  --baseline-payload real_shower_meta_stage0/run_baseline_ceiling.py.gz.b64 \
  --scorer-parts mondrian_clique_development/source_parts_v2 \
  --v6-structural-families-json-gz input/v6/label_free_sparse_support_v6_families.json.gz \
  --v8-result-json input/v8/pooled_year_centroid_v8_development.json \
  --v8-runner exact-v8/orbittrace_pooled_year_centroid_v8/run_development.py \
  --dsh-comparator input/dsh/literature_comparators.py \
  --output output

test -f output/drift_conditioned_two_view_membership_p12_development.json

progress 'PIN CANONICAL P12 + P13 DEVELOPMENT ARTIFACTS'
for pair in "$P12_ARTIFACT:$P12_ARTIFACT_DIGEST:p12" "$P13_ARTIFACT:$P13_ARTIFACT_DIGEST:p13"; do
  IFS=: read -r aid digest tag <<< "$pair"
  curl -L --fail --retry 3 -H "Authorization: Bearer $GH_TOKEN" -H 'Accept: application/vnd.github+json' \
    "https://api.github.com/repos/$GITHUB_REPOSITORY/actions/artifacts/$aid" -o "/tmp/p15-canonical/$tag-meta.json"
  curl -L --fail --retry 3 -H "Authorization: Bearer $GH_TOKEN" -H 'Accept: application/vnd.github+json' \
    "https://api.github.com/repos/$GITHUB_REPOSITORY/actions/artifacts/$aid/zip" -o "/tmp/p15-canonical/$tag.zip"
  echo "$digest  /tmp/p15-canonical/$tag.zip" | sha256sum -c -
  unzip -q "/tmp/p15-canonical/$tag.zip" -d "/tmp/p15-canonical/$tag"
done
python - <<'PY'
import json
from pathlib import Path
checks=(
 ('p12',9035003746,'orbittrace-drift-conditioned-two-view-membership-p12-development',31302353678,'sha256:4b13435ede6f95bf33c016642cc20f932bf45db58e10a5576f316234c29d8cd7'),
 ('p13',9035081147,'orbittrace-dual-output-core-halo-p13-development',31303078223,'sha256:efd9c047fb195800d88da3409fb3765e265becb6d0483367e46b8f232658956a'),
)
for tag,aid,name,run,digest in checks:
    m=json.loads(Path(f'/tmp/p15-canonical/{tag}-meta.json').read_text())
    assert m['id']==aid and m['name']==name and m['workflow_run']['id']==run
    assert m['digest']==digest and not m['expired']
print('PASS_P15_CANONICAL_P12_P13_ARTIFACT_METADATA')
PY

test -f /tmp/p15-canonical/p12/drift_conditioned_two_view_membership_p12_development.json
test -f /tmp/p15-canonical/p13/dual_output_core_halo_p13_development.json

progress 'ARTIFACT-EXACT P15 DEVELOPMENT ADJUDICATION'
python orbittrace_support_safe_halo_p15/adjudicate_development_v2.py \
  --p15-result output/drift_conditioned_two_view_membership_p12_development.json \
  --canonical-p12 /tmp/p15-canonical/p12/drift_conditioned_two_view_membership_p12_development.json \
  --canonical-p13 /tmp/p15-canonical/p13/dual_output_core_halo_p13_development.json \
  --output output/support_safe_secondary_halo_p15_development.json

grep -F '"verdict": "PASS_SUPPORT_SAFE_SECONDARY_HALO_P15_DEVELOPMENT"' output/support_safe_secondary_halo_p15_development.json
echo PASS_P15_V2_DEVELOPMENT_COMPATIBILITY_AND_CANONICAL_IDENTITY
