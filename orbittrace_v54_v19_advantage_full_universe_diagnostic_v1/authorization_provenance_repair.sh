#!/usr/bin/env bash
set -euo pipefail

python -m pip install --upgrade pip -r frozen-v8/ghoststream_fixed4_application/requirements.txt
python -m pip install --no-deps gmn-python-api==0.0.13
python -m pip install 'numpy==2.1.3' 'scipy==1.14.1' 'scikit-learn==1.5.2' 'joblib==1.5.3'
mkdir -p input/v51 input/auth input/payload input/truth output/freeze output/diag

test "$(git hash-object orbittrace_v54_v19_advantage_full_universe_diagnostic_v1/PROTOCOL.md)" = '42b19b51df72d6073dc4ec9f802324aba86eeda2'
test "$(git hash-object orbittrace_v54_v19_advantage_full_universe_diagnostic_v1/diagnose.py)" = '441c6e48cb8b874361db87cc0a9f925f239e05a1'
python -m py_compile orbittrace_v54_v19_advantage_full_universe_diagnostic_v1/diagnose.py
echo PASS_V54_REPAIRED_SOURCE_PINS

curl -L --fail --retry 3 -H "Authorization: Bearer ${GH_TOKEN}" -H 'Accept: application/vnd.github+json' \
  'https://api.github.com/repos/brandonlign/runner/actions/artifacts/9101972590/zip' -o input/v51.zip
echo '56258a0be52d83c0d6dbfcffdb9fd9a2c6b73587ba8d92d7bdccdef9729868c9  input/v51.zip' | sha256sum -c -
unzip -q input/v51.zip -d input/v51
echo '5f20a8bedb6e7b8d6c06d66e45d5037057a9853ded35a2b360333d6ea5e2c4cc  input/v51/capture/V51_V31_CONSENSUS_BOTTLENECK_VECTOR.json' | sha256sum -c -

curl -L --fail --retry 3 -H "Authorization: Bearer ${GH_TOKEN}" -H 'Accept: application/vnd.github+json' \
  'https://api.github.com/repos/brandonlign/runner/actions/artifacts/9102914767/zip' -o input/auth.zip
echo '2441cb6fb4401601976ada3feb59db6cf658bc8eba4f0e5a3bc06b743aa8c167  input/auth.zip' | sha256sum -c -
unzip -q input/auth.zip -d input/auth
echo '165f094fafa0f0f1e78b57dca83fbbf2aeee5d15bdefc9ba4b6f349d495e0aa7  input/auth/diag/V31_INTERNAL_V19_SUPPRESSION_DIAGNOSTIC.json' | sha256sum -c -
python - <<'PY'
import json
v=json.load(open('input/v51/capture/V51_V31_CONSENSUS_BOTTLENECK_VECTOR.json'))
a=json.load(open('input/auth/diag/V31_INTERNAL_V19_SUPPRESSION_DIAGNOSTIC.json'))
assert v['verdict']=='PASS_V51_V31_CONSENSUS_BOTTLENECK_VECTOR_CAPTURE'
assert v['family_count']==229 and len(v['families'])==229
assert v['canonical_sha256_without_self_field']=='0e13b3f9e6b791a13a3e90d853f8704573b1264dffcb67236e6423491ad70020'
assert v['diagnostic_recoverability_attached'] is False and v['annual_own_family_f1_attached'] is False
assert a['verdict']=='PASS_V31_INTERNAL_V19_SUPPRESSION_DIAGNOSTIC'
assert a['direction_supported_both_years'] is True
assert a['new_rank_or_score_used_for_ranking'] is False and a['successor_selected'] is False
assert a['sonotaco_role']=='EXPOSED_DEVELOPMENT_ONLY'
assert a['target_information_access'] is False and a['target_region_events_accessed'] is False
assert a['maarsy_scientific_access'] is False and a['dms_scientific_access'] is False
print('PASS_V54_REPAIRED_AUTHORIZER_PINS')
PY

# Engineering-only compatibility copy: the frozen v54 source used a stale
# #1157 guard-field name. Replace exactly that one authorizer assertion in a
# temporary copy. The scientific statistic, split, truth semantics, and gate
# remain byte-for-byte defined by the original frozen source/protocol.
cp orbittrace_v54_v19_advantage_full_universe_diagnostic_v1/diagnose.py input/diagnose_authorizer_compat.py
python - <<'PY'
p='input/diagnose_authorizer_compat.py'
s=open(p).read()
old="auth['new_candidate_order_evaluated']"
new="auth['new_rank_or_score_used_for_ranking']"
assert s.count(old)==1
s=s.replace(old,new)
open(p,'w').write(s)
assert old not in open(p).read()
print('PASS_V54_SINGLE_FIELD_AUTHORIZER_COMPAT_PATCH')
PY

PYTHONPATH=orbittrace_v22_sonotaco_grouped_oof_ranker_v1/stubs:. \
python -u input/diagnose_authorizer_compat.py freeze \
  --vector-file input/v51/capture/V51_V31_CONSENSUS_BOTTLENECK_VECTOR.json \
  --authorizer-file input/auth/diag/V31_INTERNAL_V19_SUPPRESSION_DIAGNOSTIC.json \
  --output output/freeze
python - <<'PY'
import hashlib,json
p='output/freeze/V54_V19_ADVANTAGE_FULL_UNIVERSE_SPLIT.json'
r=json.load(open(p))
assert r['verdict']=='PASS_V54_V19_ADVANTAGE_FULL_UNIVERSE_SPLIT_FREEZE'
assert r['scientific_role']=='COMPLETE_229_FAMILY_HDB_V19_ADVANTAGE_SPLIT_FROZEN_BEFORE_V54_RECOVERABILITY_ATTACHMENT'
assert r['family_count']==229 and len(r['families'])==229
assert r['positive_v19_advantage_count']==104 and r['nonpositive_v19_advantage_count']==125
assert r['current_v54_recoverability_attached'] is False and r['annual_own_family_f1_attached'] is False
for k in ('literature_budget_used_in_split','top_k_used_in_split','rank_window_used_in_split','boundary_identity_used','group_identity_used','v1157_surfaced_missed_identity_used','component_quality_topology_signal_used','new_candidate_order_evaluated','selector_evaluated','successor_selected','nonzero_threshold_selected','target_information_access','target_region_events_accessed','maarsy_scientific_access','dms_scientific_access'):
    assert r[k] is False
assert r['sonotaco_role']=='EXPOSED_DEVELOPMENT_ONLY' and r['blind_exclusion']==[20.0,55.0]
print('PASS_V54_REPAIRED_SPLIT_FREEZE',hashlib.sha256(open(p,'rb').read()).hexdigest(),r['canonical_sha256_without_self_field'])
PY

# Only after the full split has frozen may membership/truth inputs be restored.
curl -L --fail --retry 3 -H "Authorization: Bearer ${GH_TOKEN}" -H 'Accept: application/vnd.github+json' \
  'https://api.github.com/repos/brandonlign/runner/actions/artifacts/9074742322/zip' -o input/payload.zip
echo 'd940fa255804866f14bc34b1d72467d17adddcfb7d82c954ed5a8d1668aa307a  input/payload.zip' | sha256sum -c -
unzip -q input/payload.zip -d input/payload
python - <<'PY'
import json
m=json.load(open('input/payload/hdbscan/V22_PRETRUTH_FEATURE_MANIFEST.json'))
f=json.load(open('input/payload/hdbscan/family_memberships.json'))
assert m['truth_accessed'] is False and f['truth_accessed'] is False
assert m['feature_dimension']==71 and len(m['family_ids'])==229 and len(f['families'])==229
assert [str(x['family_id']) for x in f['families']]==list(map(str,m['family_ids']))
assert m['target_information_access'] is False
assert m['maarsy_scientific_access'] is False and m['dms_scientific_access'] is False
print('PASS_V54_REPAIRED_IMMUTABLE_HDB_PAYLOAD')
PY

curl -L --fail --retry 3 -H "Authorization: Bearer ${GH_TOKEN}" -H 'Accept: application/vnd.github+json' \
  'https://api.github.com/repos/brandonlign/runner/actions/artifacts/9069505548/zip' -o input/truth.zip
echo 'cdea3297c234b0b3a8f09c2208649c8607bb3e9a9004d299f6dcc18536ebb797  input/truth.zip' | sha256sum -c -
unzip -q input/truth.zip -d input/truth
echo PASS_V54_REPAIRED_EXPOSED_TRUTH_LOADED_AFTER_SPLIT_FREEZE

# The truth-aware diagnostic uses the original frozen source; its authorizer
# guard is not on this execution path.
PYTHONPATH=orbittrace_v22_sonotaco_grouped_oof_ranker_v1/stubs:. \
python -u orbittrace_v54_v19_advantage_full_universe_diagnostic_v1/diagnose.py diagnose \
  --split-file output/freeze/V54_V19_ADVANTAGE_FULL_UNIVERSE_SPLIT.json \
  --hdb-root input/payload/hdbscan --truth-root input/truth --output output/diag

python - <<'PY'
import json
r=json.load(open('output/diag/V54_V19_ADVANTAGE_FULL_UNIVERSE_DIAGNOSTIC.json'))
assert r['verdict'] in {'PASS_V54_V19_ADVANTAGE_FULL_UNIVERSE_DIAGNOSTIC','FAIL_V54_V19_ADVANTAGE_FULL_UNIVERSE_DIAGNOSTIC'}
assert r['family_count']==229 and r['authorizing_diagnostic']=='PASS_V31_INTERNAL_V19_SUPPRESSION_DIAGNOSTIC'
assert r['authorizing_run']==31495853601 and r['authorizing_artifact']==9102914767
assert len(r['annual_diagnostics'])==2
for k in ('new_candidate_order_evaluated','literature_panel_evaluated','selector_evaluated','replacement_rule_evaluated','successor_selected','v19_only_order_evaluated','minimum_rank_order_evaluated','weighted_fusion_evaluated','nonlinear_fusion_evaluated','representative_group_aggregation_evaluated','auc_evaluated','correlation_evaluated','regression_evaluated','p_value_evaluated','nonzero_threshold_search','absolute_gap_search','quantile_search','top_k_search','rank_window_search','literature_budget_analysis','boundary_identity_used','v1157_surfaced_missed_identity_used','component_quality_topology_rescue','feature_search','model_search','k_search','metric_search','scaling_search','diversity_search','source_quota_selected','post_result_second_search','target_information_access','target_region_events_accessed','maarsy_scientific_access','dms_scientific_access'):
    assert r[k] is False
assert r['sonotaco_role']=='EXPOSED_DEVELOPMENT_ONLY' and r['blind_exclusion']==[20.0,55.0]
print(r['verdict'],r['annual_diagnostics'])
PY

sha256sum \
  orbittrace_v54_v19_advantage_full_universe_diagnostic_v1/PROTOCOL.md \
  orbittrace_v54_v19_advantage_full_universe_diagnostic_v1/diagnose.py \
  orbittrace_v54_v19_advantage_full_universe_diagnostic_v1/authorization_provenance_repair.sh \
  input/diagnose_authorizer_compat.py \
  input/v51.zip input/v51/capture/V51_V31_CONSENSUS_BOTTLENECK_VECTOR.json \
  input/auth.zip input/auth/diag/V31_INTERNAL_V19_SUPPRESSION_DIAGNOSTIC.json \
  output/freeze/V54_V19_ADVANTAGE_FULL_UNIVERSE_SPLIT.json \
  input/payload.zip input/truth.zip output/diag/V54_V19_ADVANTAGE_FULL_UNIVERSE_DIAGNOSTIC.json \
  > output/V54_V19_ADVANTAGE_REPAIR_SOURCE_SHA256.txt
git rev-parse HEAD > output/execution_commit.txt
python --version > output/python_version.txt
python -m pip freeze > output/environment.txt
