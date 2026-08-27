#!/usr/bin/env bash
set -euo pipefail

: "${GH_TOKEN:?GH_TOKEN required}"
: "${BASE_SHA:?BASE_SHA required}"
: "${HEAD_SHA:?HEAD_SHA required}"

REPO="${GITHUB_REPOSITORY:-brandonlign/runner}"
SCI_FREEZE='fe86ca3a97a909bcd772eae665770b92718ca51f'
ACTIVATION_HEAD='92e09337190aa46a100f59336f6b92fa855e2088'
P13_ARTIFACT=9035081147
P13_DEV_RUN=31303078223
P12_TRANSPORT_SHA='f511a012693b7db05495985e32793177c9844196bf82e6f7fe868070ffed34ae'

progress(){ printf '\n===== %s =====\n' "$*"; }

progress 'TECHNICAL CHILD / SCIENTIFIC ACTIVATION GUARDS'
git fetch --no-tags origin "$BASE_SHA" "$HEAD_SHA" "$SCI_FREEZE" "$ACTIVATION_HEAD"
mapfile -t launcher_files < <(git diff --name-only "$BASE_SHA" "$HEAD_SHA")
test "${#launcher_files[@]}" -eq 1
test "${launcher_files[0]}" = 'orbittrace_core_halo_p13_literature/LAUNCH_V3.md'
launch_marker="$(git show "$HEAD_SHA":orbittrace_core_halo_p13_literature/LAUNCH_V3.md)"
test "$(printf '%s\n' "$launch_marker" | sed -n '1p')" = 'LAUNCH_P13_MATCHED_TECHNICAL_RECOVERY_V3'
test "$(printf '%s\n' "$launch_marker" | sed -n '2p')" = '674'
test "$(printf '%s\n' "$launch_marker" | sed -n '3p')" = '31305824131'
test "$(printf '%s\n' "$launch_marker" | wc -l)" -eq 3
cp orbittrace_core_halo_p13_literature/prepare_pretruth_panel_input_v2.py /tmp/prepare_p13_panel_v2.py
python -m py_compile /tmp/prepare_p13_panel_v2.py

gh api "repos/$REPO/pulls/674" > /tmp/activation.json
python - <<'PY'
import json
p=json.load(open('/tmp/activation.json'))
assert p['state']=='open'
assert p['base']['ref']=='agent/orbittrace-p13-matched-literature-freeze'
assert p['base']['sha']=='fe86ca3a97a909bcd772eae665770b92718ca51f'
assert p['head']['ref']=='agent/orbittrace-p13-matched-literature-run-v1'
assert p['head']['sha']=='92e09337190aa46a100f59336f6b92fa855e2088'
print('PASS_P13_V3_AUTHORITATIVE_ACTIVATION_PR_674')
PY
mapfile -t scientific_files < <(git diff --name-only "$SCI_FREEZE" "$ACTIVATION_HEAD")
test "${#scientific_files[@]}" -eq 1
test "${scientific_files[0]}" = 'orbittrace_core_halo_p13_literature/RUN.md'
scientific_marker="$(git show "$ACTIVATION_HEAD":orbittrace_core_halo_p13_literature/RUN.md)"
test "$(printf '%s\n' "$scientific_marker" | sed -n '1p')" = 'EXECUTE_P13_MATCHED_AFTER_AUTHORITATIVE_P13_DEVELOPMENT_PASS'
test "$(printf '%s\n' "$scientific_marker" | sed -n '2p')" = "$P13_DEV_RUN"
test "$(printf '%s\n' "$scientific_marker" | sed -n '3p')" = "$P13_ARTIFACT"
test "$(printf '%s\n' "$scientific_marker" | wc -l)" -eq 3

git checkout --detach "$SCI_FREEZE"
test ! -e orbittrace_core_halo_p13_literature/RUN.md
echo PASS_P13_V3_DETACHED_TO_SCIENTIFIC_FREEZE

progress 'AUTHORITATIVE P13 DEVELOPMENT PREREQUISITE'
curl -L --fail --retry 3 -H "Authorization: Bearer $GH_TOKEN" -H 'Accept: application/vnd.github+json' "https://api.github.com/repos/$REPO/actions/artifacts/$P13_ARTIFACT" -o /tmp/p13-meta.json
curl -L --fail --retry 3 -H "Authorization: Bearer $GH_TOKEN" -H 'Accept: application/vnd.github+json' "https://api.github.com/repos/$REPO/actions/artifacts/$P13_ARTIFACT/zip" -o /tmp/p13-dev.zip
echo 'efd9c047fb195800d88da3409fb3765e265becb6d0483367e46b8f232658956a  /tmp/p13-dev.zip' | sha256sum -c -
rm -rf /tmp/p13-dev && mkdir -p /tmp/p13-dev && unzip -q /tmp/p13-dev.zip -d /tmp/p13-dev
python - <<'PY'
import json
m=json.load(open('/tmp/p13-meta.json')); r=json.load(open('/tmp/p13-dev/dual_output_core_halo_p13_development.json'))
assert m['id']==9035081147 and m['name']=='orbittrace-dual-output-core-halo-p13-development' and m['workflow_run']['id']==31303078223
assert m['digest']=='sha256:efd9c047fb195800d88da3409fb3765e265becb6d0483367e46b8f232658956a' and not m['expired']
assert r['verdict']=='PASS_DUAL_OUTPUT_CORE_HALO_P13_DEVELOPMENT'
assert r['configuration']['p13_primary_discovery_metrics_use_core_only'] is True
assert r['configuration']['p13_membership_metrics_use_halo_only'] is True
assert r['configuration']['p13_detector_recomputed'] is False
assert r['core_discovery']=={'qualified_matches':95,'recovered_at_100':58,'recovered_at_500':95,'mrr':0.045531138942766655,'top100_dominant_precision':0.6884631112636006}
assert r['core_pretruth_sha256']=='12e6635085c77c8c705fe225e67811c659e98bf7cd1047649ec2b8d593261b3c'
assert r['halo_pretruth_sha256']=='f158ebfa3a9a3c8006a7c81cbf0b47f7307aa7f2537e8046621b08037230cca3'
assert r['no_new_truth_query'] is True and r['target_information_access'] is False
assert all(r['gates'].values()) and all(r['inherited_p12_non_scientific_gates'].values())
print('PASS_P13_V3_AUTHORITATIVE_DEVELOPMENT')
PY

progress 'INSTALL + EXACT METHOD RECONSTRUCTION'
python -m pip install --upgrade pip -r exact-lit/ghoststream_fixed4_application/requirements.txt
python -m pip install --no-deps gmn-python-api==0.0.13
mkdir -p input/{v3,dsh,source,evaluator,parser,mapping,archives} input/competitors/{hdbscan2023,hdbscan2025,sugar2023,sugar2025} pretruth/{strict,hdbscan,sugar,checkpoints} output
python orbittrace_crossyear_two_view_membership_p2/apply_protocol_compliance_patch.py orbittrace_crossyear_two_view_membership_p2/run_development.py /tmp/p2a.py
python orbittrace_crossyear_two_view_membership_p2/apply_protocol_precision_patch_v2.py /tmp/p2a.py /tmp/p2.py
python orbittrace_crossfit_seed_floor_membership_p3/apply_p3_patch_v2.py /tmp/p2.py /tmp/p3.py
python orbittrace_dual_view_seed_envelope_p4/apply_p4_patch.py /tmp/p3.py /tmp/p4.py
python orbittrace_joint_seed_support_p5/apply_p5_patch.py /tmp/p4.py /tmp/p5.py
python orbittrace_same_model_crossfit_p6/apply_p6_patch.py /tmp/p5.py /tmp/p6.py
python orbittrace_finite_sample_robust_floor_p7/apply_p7_patch.py /tmp/p6.py /tmp/p7.py
python orbittrace_full_finite_sample_order_stat_p8/apply_p8_patch.py /tmp/p7.py /tmp/p8.py
python orbittrace_bidirectional_reliability_p9/apply_p9_patch.py /tmp/p8.py /tmp/p9.py
python orbittrace_floor_consistent_geometry_p10/apply_p10_patch.py /tmp/p9.py /tmp/p10.py
python orbittrace_density_contrast_p11/apply_p11_patch.py /tmp/p10.py /tmp/p11.py
echo '914913d0462ea6793af3836cef945f14a03cca205ac0755ed6cdadb63b8752f9  /tmp/p11.py' | sha256sum -c -
python orbittrace_drift_conditioned_p12/apply_p12_patch.py /tmp/p11.py /tmp/p12.py
echo '78e93b5af19a441bc58b00428d2b356218b33f7a4a891a640dd59cb5d4599c32  /tmp/p12.py' | sha256sum -c -
python orbittrace_core_halo_p13_literature/apply_p12_matched_transport_patch_v2.py /tmp/p12.py /tmp/p12_panel.py
echo "$P12_TRANSPORT_SHA  /tmp/p12_panel.py" | sha256sum -c -

git fetch --no-tags --depth=1 origin d8258581af143308495bd97bedcc142abbbd951a
git show FETCH_HEAD:orbittrace_multi_anchor_energy_v3/multi_anchor_energy_v3.py > input/v3/multi_anchor_energy_v3.py
(cd exact-lit && python orbittrace_wavelet_catalogue_v3/audit_development_source.py)
echo 'ef3e69317af59fdac7a030edc77f742fc4772473d7f16b719b5d804cd4117f51  /tmp/run_wavelet_catalogue_v3_development.py' | sha256sum -c -
test "$(git -C exact-lit rev-parse HEAD)" = 'ffe8351b9ee8df4418fb4926fab782d66180e276'
test -f exact-lit/orbittrace_literature_matched_v8/run_exact_row_benchmark.py
test -f exact-lit/orbittrace_literature_matched_v8/sonotaco_2025_native_adapter_wrapper.py
printf 'PIN exact-row commit=%s blob=%s\n' "$(git -C exact-lit rev-parse HEAD)" "$(git -C exact-lit hash-object orbittrace_literature_matched_v8/run_exact_row_benchmark.py)"

git fetch --no-tags --depth=1 origin agent/orbittrace-literature-comparison-2023-replication
git show FETCH_HEAD:orbittrace_literature_comparison/literature_comparators.py > input/dsh/literature_comparators.py
echo '85cd11afbdebc4a0315ebf1daf42d10d4993d7ab088dd05301e3234b18340a5a  input/dsh/literature_comparators.py' | sha256sum -c -
git fetch --no-tags --depth=1 origin d8e58697812bbc93cbd204eb5ebbd6c98d0f3c0d
git show FETCH_HEAD:orbittrace_crossyear_two_view_membership_p2_literature/prepare_strict_id_manifest.py > input/source/prepare_strict_id_manifest.py
git show FETCH_HEAD:orbittrace_crossyear_two_view_membership_p2_literature/read_exact_orbits.py > input/source/read_exact_orbits.py
printf 'PIN strict-manifest commit=d8e58697812bbc93cbd204eb5ebbd6c98d0f3c0d blob=%s\n' "$(git hash-object input/source/prepare_strict_id_manifest.py)"
printf 'PIN orbit-reader commit=d8e58697812bbc93cbd204eb5ebbd6c98d0f3c0d blob=%s\n' "$(git hash-object input/source/read_exact_orbits.py)"
python -m py_compile /tmp/prepare_p13_panel_v2.py /tmp/p12_panel.py input/source/prepare_strict_id_manifest.py input/source/read_exact_orbits.py
grep -F 'runtime=exact.v8.mult.load_frozen_runtime()' /tmp/prepare_p13_panel_v2.py
grep -F 'v8_panel=exact.run_v8_panel(a.panel,scan,support,runtime,base)' /tmp/prepare_p13_panel_v2.py
echo PASS_P13_V3_EXACT_RUNTIME_IDENTITIES

progress 'ASSIGNMENT FILES — ID-ONLY PRETRUTH ACCESS'
gh run download 31226945294 --repo "$REPO" --name orbittrace-hdbscan-2023-blind-safe-benchmark --dir input/competitors/hdbscan2023
gh run download 31071589912 --repo "$REPO" --name orbittrace-sonotaco-2025-hdbscan-catalogue --dir input/competitors/hdbscan2025
gh run download 31076789635 --repo "$REPO" --name orbittrace-sonotaco-2023-sugar-uncertainty-transfer --dir input/competitors/sugar2023
gh run download 31075178517 --repo "$REPO" --name orbittrace-sonotaco-2025-sugar-uncertainty-catalogue --dir input/competitors/sugar2025
cp "$(find input/competitors/hdbscan2023 -type f -name full_catalogue_assignments.jsonl.gz -print -quit)" input/hdbscan_2023.jsonl.gz
cp "$(find input/competitors/hdbscan2025 -type f -name full_catalogue_assignments.jsonl.gz -print -quit)" input/hdbscan_2025.jsonl.gz
cp "$(find input/competitors/sugar2023 -type f -name sugar_uncertainty_assignments.json.gz -print -quit)" input/sugar_2023.json.gz
cp "$(find input/competitors/sugar2025 -type f -name sugar_uncertainty_assignments.json.gz -print -quit)" input/sugar_2025.json.gz
echo '35f629b1dff4d04cdc13aa8224171ec1ab8e06b52836900d66ff978b5c235761  input/hdbscan_2023.jsonl.gz' | sha256sum -c -
echo '8e7580c52e41e6996d6e46f289a7b916565a4efc512c5549ee83f249d0e81ee3  input/hdbscan_2025.jsonl.gz' | sha256sum -c -
echo '2b9e86572f10af447071cb10c56f643c1ad8babfe0d9aa667994ba3639834389  input/sugar_2023.json.gz' | sha256sum -c -
echo '77844d700bb14bb9952307fad13eb66cbc62e6a1555e5edd9c8aa0d26968b06e  input/sugar_2025.json.gz' | sha256sum -c -
python input/source/prepare_strict_id_manifest.py --hdbscan-2023 input/hdbscan_2023.jsonl.gz --hdbscan-2025 input/hdbscan_2025.jsonl.gz --sugar-2023 input/sugar_2023.json.gz --sugar-2025 input/sugar_2025.json.gz --output pretruth/strict_manifest.json
python orbittrace_core_halo_p13_literature/split_strict_manifest.py --input pretruth/strict_manifest.json --output-dir pretruth/strict
echo PASS_P13_V3_ASSIGNMENT_IDS_FROZEN_CLUSTER_VALUES_UNREAD

progress 'EXACT RAW BENCHMARK ARCHIVES'
curl -L --fail --retry 3 'https://www.astro.sk/iaumdcDB/public/data/SNMv3/023a.zip' -o input/archives/023a.zip
curl -L --fail --retry 3 'https://www.astro.sk/iaumdcDB/public/data/SNMv3/025a.zip' -o input/archives/025a.zip
echo '9f44696f99164801ff405dab90f68df3666b0d6734fed464a95e7ed0d6f5f430  input/archives/023a.zip' | sha256sum -c -
echo 'f4eb716a4b900658fcc658a633d918eca28946f59da75935f1fd5f6bc539bf52  input/archives/025a.zip' | sha256sum -c -

progress 'FREEZE P13 CORE + EXACT P12 HALO FOR BOTH COMPARATOR UNIVERSES'
export PYTHONPATH="exact-lit:input/v3:exact-lit/orbittrace_wavelet_catalogue_v3:."
for PANEL in hdbscan sugar; do
  mkdir -p "pretruth/$PANEL/halo"
  python /tmp/prepare_p13_panel_v2.py \
    --panel "$PANEL" \
    --archive-2023 input/archives/023a.zip --archive-2025 input/archives/025a.zip \
    --manifest-2023 "pretruth/strict/${PANEL}_2023.json" --manifest-2025 "pretruth/strict/${PANEL}_2025.json" \
    --exact-row-runner exact-lit/orbittrace_literature_matched_v8/run_exact_row_benchmark.py \
    --orbit-reader input/source/read_exact_orbits.py \
    --support-source-parts exact-lit/orbittrace_fixed4_support_wrapper_development/source_parts \
    --candidate-payload exact-lit/sonotaco_fixed4_final_development/candidate.py.gz.b64 \
    --baseline-payload exact-lit/real_shower_meta_stage0/run_baseline_ceiling.py.gz.b64 \
    --scorer-parts exact-lit/mondrian_clique_development/source_parts_v2 \
    --output "pretruth/$PANEL"
  python -u /tmp/p12_panel.py \
    --base-runner /tmp/run_wavelet_catalogue_v3_development.py \
    --support-source-parts exact-lit/orbittrace_fixed4_support_wrapper_development/source_parts \
    --candidate-payload exact-lit/sonotaco_fixed4_final_development/candidate.py.gz.b64 \
    --baseline-payload exact-lit/real_shower_meta_stage0/run_baseline_ceiling.py.gz.b64 \
    --scorer-parts exact-lit/mondrian_clique_development/source_parts_v2 \
    --v6-structural-families-json-gz /dev/null --v8-result-json /dev/null --v8-runner /dev/null \
    --dsh-comparator input/dsh/literature_comparators.py \
    --panel-input "pretruth/$PANEL/p13_${PANEL}_core_panel_input.json.gz" \
    --output "pretruth/$PANEL/halo"
  python orbittrace_core_halo_p13_literature/finalize_pretruth_checkpoint.py \
    --panel "$PANEL" \
    --core-input "pretruth/$PANEL/p13_${PANEL}_core_panel_input.json.gz" \
    --halo-pretruth "pretruth/$PANEL/halo/p13_${PANEL}_p12_halo_pretruth.pkl" \
    --output "pretruth/checkpoints/${PANEL}.pkl"
done

progress 'HARD TWO-PANEL PRETRUTH BARRIER'
python - <<'PY'
import hashlib,pickle
from pathlib import Path
expected={'hdbscan':{'2023':26460,'2025':19658},'sugar':{'2023':30414,'2025':23200}}
for panel in ('hdbscan','sugar'):
    p=Path(f'pretruth/checkpoints/{panel}.pkl'); raw=p.read_bytes(); side=p.with_suffix(p.suffix+'.sha256')
    assert side.read_text().strip()==hashlib.sha256(raw).hexdigest()
    c=pickle.loads(raw)
    assert c['classification']=='P3 matched-literature pretruth panel checkpoint'
    assert c['panel']==panel and c['years']==[2023,2025] and c['blind_exclusion']==[20.0,55.0]
    assert c['competitor_cluster_values_accessed'] is False and c['known_shower_truth_accessed'] is False
    assert c['parameter_search'] is False and c['p13_primary_core_only'] is True and c['p13_halo_secondary_only'] is True
    assert c['p3_diagnostics']['primary_candidate_is_core_only'] is True and c['p3_diagnostics']['halo_can_affect_primary_evaluation'] is False
    assert c['p13_transport_source_sha256']=='f511a012693b7db05495985e32793177c9844196bf82e6f7fe868070ffed34ae'
    assert c['exact_event_rows']==expected[panel]
    assert len(c['p13_core_pretruth_sha256'])==64 and len(c['p13_halo_membership_pretruth_sha256'])==64
print('PASS_P13_V3_BOTH_CHECKPOINTS_FROZEN_BEFORE_TRUTH_OR_CLUSTER_VALUES')
PY

progress 'POSTFREEZE TRUTH PARSERS + EVALUATOR SOURCE'
gh run download 30920687116 --repo "$REPO" --name sonotaco-2023-confirmation-source-repair-v2 --dir input/parser
cp "$(find input/parser -type f -name run_sonotaco_2023_fixed4_confirmation.py -print -quit)" input/parser_2023.py
echo 'bc2636005cc25da33e8accb6bdb70beea6ab900862cd1e6342a481395ac8f3e6  input/parser_2023.py' | sha256sum -c -
gh run download 30855193522 --repo "$REPO" --name real-shower-meta-data-audit --dir input/mapping
cp "$(find input/mapping -type f -name audit.json -print -quit)" input/mapping_audit.json
echo 'f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778  input/mapping_audit.json' | sha256sum -c -
git fetch --no-tags --depth=1 origin b1fa693471be78d1634632de942b6f95222c8a92
git show FETCH_HEAD:orbittrace_crossfit_seed_floor_membership_p3_literature/evaluate_frozen.py > input/evaluator/evaluate_frozen.py
git show FETCH_HEAD:orbittrace_crossfit_seed_floor_membership_p3_literature/evaluate_frozen_blindsafe.py > input/evaluator/evaluate_frozen_blindsafe.py
python -m py_compile input/parser_2023.py input/evaluator/evaluate_frozen.py input/evaluator/evaluate_frozen_blindsafe.py exact-lit/orbittrace_literature_matched_v8/sonotaco_2025_native_adapter_wrapper.py
echo PASS_P13_V3_POSTFREEZE_EVALUATOR_STAGED

progress 'OPEN TRUTH + COMPETITOR CLUSTER VALUES EXACTLY ONCE'
python -u input/evaluator/evaluate_frozen_blindsafe.py \
  --hdbscan-pretruth pretruth/checkpoints/hdbscan.pkl \
  --sugar-pretruth pretruth/checkpoints/sugar.pkl \
  --exact-row-runner exact-lit/orbittrace_literature_matched_v8/run_exact_row_benchmark.py \
  --base-runner /tmp/run_wavelet_catalogue_v3_development.py \
  --support-source-parts exact-lit/orbittrace_fixed4_support_wrapper_development/source_parts \
  --candidate-payload exact-lit/sonotaco_fixed4_final_development/candidate.py.gz.b64 \
  --baseline-payload exact-lit/real_shower_meta_stage0/run_baseline_ceiling.py.gz.b64 \
  --scorer-parts exact-lit/mondrian_clique_development/source_parts_v2 \
  --parser-2023 input/parser_2023.py \
  --parser-2025 exact-lit/orbittrace_literature_matched_v8/sonotaco_2025_native_adapter_wrapper.py \
  --mapping-audit input/mapping_audit.json \
  --archive-2023 input/archives/023a.zip --archive-2025 input/archives/025a.zip \
  --hdbscan-2023 input/hdbscan_2023.jsonl.gz --hdbscan-2025 input/hdbscan_2025.jsonl.gz \
  --sugar-2023 input/sugar_2023.json.gz --sugar-2025 input/sugar_2025.json.gz \
  --output output/p3_evaluator_result.json
python orbittrace_core_halo_p13_literature/finalize_p3_evaluator_result.py \
  --p3-result output/p3_evaluator_result.json \
  --hdbscan-checkpoint pretruth/checkpoints/hdbscan.pkl \
  --sugar-checkpoint pretruth/checkpoints/sugar.pkl \
  --output output/p13_matched_literature_result.json

progress 'FINAL FROZEN MATCHED GATE'
python - <<'PY'
import json
r=json.load(open('output/p13_matched_literature_result.json'))
assert r['verdict'] in {'PASS_P13_MATCHED_SPARSE_SUPERIORITY_BOTH_COMPARATORS_BOTH_YEARS','FAIL_P13_MATCHED_SPARSE_SUPERIORITY_NO_GO'}
assert r['years']==[2023,2025] and r['blind_exclusion']==[20.0,55.0]
assert r['target_access_authorized'] is False
assert r['primary_discovery_output']=='immutable P13 recurrent core only'
assert r['secondary_characterization_output']=='exact transported P12 halo; cannot affect superiority'
assert r['sparse_superiority_required_against_both_comparators_in_both_years'] is True
assert r['pairwise_only_no_cross_denominator_comparison'] is True and r['broad_only_does_not_authorize_external'] is True
if r['verdict'].startswith('PASS_'):
    assert r['classification']=='SPARSE_STREAM_SUPERIORITY' and r['external_validation_authorized'] is True
    assert all(r['panels'][p]['sparse_pairwise_pass'] and all(r['panels'][p]['year_sparse_pass'].values()) for p in ('hdbscan','sugar'))
else:
    assert r['classification']=='NO_LITERATURE_SUPERIORITY' and r['external_validation_authorized'] is False
print('ORBITTRACE_P13_MATCHED_FINAL_BEGIN')
print(json.dumps(r,indent=2,sort_keys=True))
print('ORBITTRACE_P13_MATCHED_FINAL_END')
PY

python --version > output/python_version.txt
python -m pip freeze > output/environment.txt
sha256sum /tmp/prepare_p13_panel_v2.py /tmp/p12_panel.py orbittrace_core_halo_p13_literature/MATCHED_FREEZE.json orbittrace_core_halo_p13_literature/P12_MATCHED_TRANSPORT_SOURCE_SHA256 orbittrace_core_halo_p13_literature/*.py > output/source_sha256.txt 2>/dev/null || true
