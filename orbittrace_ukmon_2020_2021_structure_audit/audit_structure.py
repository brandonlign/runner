#!/usr/bin/env python3
"""Frozen pre-scientific UKMON 2020/2021 structure audit, transport-corrected.

The only correction after the first structure failure is reuse of the pre-existing
UKMON daily->four-period transport fallback. Scientific values and opaque identifiers
are never read, converted, logged, persisted, compared, or used.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import requests

DATES=("20200814","20210814")
BASE="https://api.ukmeteors.co.uk/matches?reqtyp=summary&reqval={}"
PERIODS=("0-6","6-12","12-18","18-24")
REQUIRED=("orbname","_sol","_ra_t","_dc_t","_vg","_q","_e","_incl","_peri","_node")


def request_top_level_list(url:str)->list[dict[str,Any]]|None:
    """Copy the prior frozen UKMON external transport acceptance rule."""
    for attempt in range(3):
        try:
            response=requests.get(
                url,
                timeout=120,
                headers={"User-Agent":"OrbitTrace-UKMON-2020-2021-structure-transport/1.0"},
            )
            if response.status_code==200:
                try:
                    payload=response.json()
                except Exception:
                    payload=None
                if isinstance(payload,list) and all(isinstance(row,dict) for row in payload):
                    return payload
        except Exception:
            pass
        if attempt<2:
            time.sleep(1.0*(attempt+1))
    return None


def audit_date(date:str)->dict[str,Any]:
    daily_url=BASE.format(date)
    rows=request_top_level_list(daily_url)
    fallback_used=False
    period_success=None
    if rows is None:
        fallback_used=True
        rows=[]
        period_success=[]
        for period in PERIODS:
            part=request_top_level_list(daily_url+f"&period={period}")
            ok=part is not None
            period_success.append(ok)
            if not ok:
                raise RuntimeError(f"fixed UKMON period transport failed for {date} period {period}")
            rows.extend(part)

    n=len(rows)
    presence={key:(sum(key in row for row in rows)/n if n else 0.0) for key in REQUIRED}
    gates={
        "transport_rule_succeeded":True,
        "rows_at_least_5":n>=5,
        "all_required_keys_present_95pct":all(v>=0.95 for v in presence.values()),
    }
    return {
        "date":f"{date[:4]}-{date[4:6]}-{date[6:]}",
        "daily_url":daily_url,
        "fallback_used":fallback_used,
        "fixed_periods":list(PERIODS) if fallback_used else [],
        "period_success":period_success,
        "rows_at_least_5":n>=5,
        "required_key_presence_fraction":presence,
        "gates":gates,
        "exact_row_count_withheld":True,
        "scientific_field_values_inspected":False,
        "orbname_values_inspected":False,
        "source_label_values_inspected":False,
        "raw_payload_persisted":False,
    }


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--freshness-json",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)

    fresh=json.loads(a.freshness_json.read_text())
    assert fresh["verdict"]=="PASS_UKMON_2020_2021_ZERO_DATA_FRESHNESS_ADJUDICATION"
    assert fresh["raw_audit_verdict_preserved"]=="FAIL_UKMON_2020_2021_REPO_SCIENTIFIC_FRESHNESS_AUDIT"
    assert fresh["raw_hit_count"]==1 and fresh["additional_hits_forgiven"]==0
    assert fresh["meteor_api_contacted"] is False
    assert fresh["scientific_value_access_this_adjudication"] is False
    assert fresh["target_information_access"] is False

    results=[audit_date(d) for d in DATES]
    passed=all(all(x["gates"].values()) for x in results)
    verdict="PASS_UKMON_2020_2021_STRUCTURE_TRANSPORT_CORRECTION" if passed else "FAIL_UKMON_2020_2021_STRUCTURE_TRANSPORT_CORRECTION"
    result={
        "verdict":verdict,
        "prior_structure_run":31225678351,
        "prior_structure_failure":"daily_non_list_dict_before_scientific_value_access",
        "transport_correction_source_blob":"fd554e1b25731439cff02711558ed2c009665004",
        "transport_rule":"daily_then_fixed_periods_0-6_6-12_12-18_18-24_on_nonlist_or_failure",
        "dates":["2020-08-14","2021-08-14"],
        "results":results,
        "scientific_field_values_inspected":False,
        "orbname_values_inspected":False,
        "source_label_values_inspected":False,
        "raw_payload_persisted":False,
        "method_evaluation_performed":False,
        "orbittrace_target_information_access":False,
        "claim_boundary":"Transport-only correction using a pre-existing frozen UKMON fallback. The already-fixed 2022 scientific field mapping is unchanged. No UKMON 2020/2021 scientific or identifier value was inspected; a pass authorizes freezing the scientific protocol only.",
    }
    (a.output/"ukmon_2020_2021_structure_transport_correction.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
    if verdict.startswith("FAIL_"):
        raise SystemExit(1)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
