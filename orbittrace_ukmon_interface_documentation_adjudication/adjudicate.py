#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path

def sha(p:Path)->str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('--dictionary-audit',required=True,type=Path); p.add_argument('--api-docs-html',required=True,type=Path); p.add_argument('--output',required=True,type=Path)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    old=json.loads(a.dictionary_audit.read_text())
    assert old['verdict']=='FAIL_UKMON_DOCUMENTATION_INTERFACE_AUDIT'
    assert old['meteor_api_contacted'] is False and old['meteor_record_access'] is False and old['reserved_2024_2025_access'] is False
    required=['solar_longitude','radiant_ra','radiant_dec','geocentric_speed','perihelion_q','eccentricity','inclination','argument_perihelion','ascending_node']
    missing=[x for x in required if not old['concept_matches'].get(x)]
    html=a.api_docs_html.read_text(errors='strict')
    docs={
      'orbname_documented':bool(re.search(r'\borbname\b',html,re.I)),
      'summary_api_documented':bool(re.search(r'reqtyp=summary',html,re.I)),
      'matches_api_documented':bool(re.search(r'reqtyp=matches',html,re.I)),
      'full_trajectory_api_documented':bool(re.search(r'getpickle',html,re.I)),
    }
    verdict='PASS_UKMON_DOCUMENTED_INTERFACE_ADJUDICATION' if not missing and all(docs.values()) else 'FAIL_UKMON_DOCUMENTED_INTERFACE_ADJUDICATION'
    result={
      'verdict':verdict,'prior_audit_verdict':old['verdict'],'dictionary_sha256':old['dictionary_sha256'],
      'api_docs_html_sha256':sha(a.api_docs_html),'required_scientific_concepts_missing':missing,
      'documented_field_keys':{'solar_longitude':'_sol','geocentric_ra':'_ra_t','geocentric_dec':'_dc_t','geocentric_speed':'_vg','perihelion':'_q','eccentricity':'_e','inclination':'_incl','argument_perihelion':'_peri','node':'_node','trajectory_id':'orbname'},
      'api_documentation_guards':docs,'meteor_api_contacted':False,'meteor_record_access':False,'reserved_2024_2025_access':False,'target_information_access':False,
      'claim_boundary':'Documentation-only adjudication combining the already-audited UKMON data dictionary with the public API documentation page. No matches, summary, or trajectory data endpoint was called.'
    }
    (a.output/'ukmon_documented_interface_adjudication.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True))
    if verdict.startswith('FAIL_'): raise SystemExit(1)
    return 0
if __name__=='__main__': raise SystemExit(main())
