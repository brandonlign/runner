#!/usr/bin/env python3
from __future__ import annotations

import argparse,csv,gzip,hashlib,io,json,zipfile
from collections import Counter
from pathlib import Path

PRE_GZ='b1beb3dac03579b2ca2a0f85a2e65213e3a4826dfe0d8f038856f6b227319765'
PRE_INNER='75dec41919072681a423d3c37d4565ca5ee19dccf86900b3b39ef5d30153ca0b'
CAN_SHA='716b70313465d5df4bfb092a85a81680e6f618606b71e25470c63c480b6449f5'
EXPECTED_ALL={2019:1,2020:4,2021:1,2022:10,2023:8,2024:14,2025:34,2026:29}
EXPECTED_CAN={2022:10,2023:8,2024:14,2025:34,2026:29}
NESTED='GhostStream_Expert_Review_Bundle.zip'
MEMBER='reconstruction/exact_downstream/primary/april_candidate_members.csv'

def req(x,m):
    if not x: raise RuntimeError(m)
def sha(b): return hashlib.sha256(b).hexdigest()

def canonical(path:Path):
    outer=path.read_bytes(); req(sha(outer)==CAN_SHA,'canonical ZIP SHA changed')
    with zipfile.ZipFile(io.BytesIO(outer)) as oz:
        hits=[n for n in oz.namelist() if Path(n).name==NESTED]; req(len(hits)==1,f'nested count {hits}'); nested=oz.read(hits[0])
    with zipfile.ZipFile(io.BytesIO(nested)) as nz:
        req(MEMBER in nz.namelist(),'canonical CSV missing'); text=nz.read(MEMBER).decode('utf-8-sig')
    rows=list(csv.DictReader(io.StringIO(text))); req(rows,'empty canonical CSV')
    parsed=[(str(r['unique_trajectory_identifier']).strip(),int(r['year'])) for r in rows]
    req(dict(sorted(Counter(y for _,y in parsed).items()))==EXPECTED_ALL,'historical counts changed')
    c=[(eid,y) for eid,y in parsed if y in EXPECTED_CAN]
    req(dict(sorted(Counter(y for _,y in c).items()))==EXPECTED_CAN and len(c)==95,'canonical counts changed')
    return c

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--pretruth',type=Path,required=True); ap.add_argument('--canonical-zip',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    gz=a.pretruth.read_bytes(); req(sha(gz)==PRE_GZ,'replay pretruth gzip changed'); raw=gzip.decompress(gz); req(sha(raw)==PRE_INNER,'replay pretruth inner changed'); pre=json.loads(raw)
    req(pre['schema']=='ORBITTRACE_M2D_BLIND_REDISCOVERY_V1_PRETRUTH','schema'); req(pre['scientific_role']=='TARGET_FREE_COMPLETE_M2D_RANKING_BEFORE_ORBITTRACE_REVEAL','role'); req(pre['verdict']=='BLIND_M2D_SCAN_FROZEN_AWAITING_SEPARATE_REVEAL','not frozen')
    req(pre['candidate_count']==8884==len(pre['candidates']),'candidate count'); req(pre['orbittrace_target_information_access'] is False and pre['orbittrace_canonical_members_access'] is False and pre['prior_orbittrace_reveal_access'] is False,'firewall'); req(pre['post_result_parameter_search'] is False and pre['post_promotion_parameter_search'] is False,'post-result search')
    can=canonical(a.canonical_zip); by={y:{eid for eid,yy in can if yy==y} for y in (2022,2023)}
    ev=[]
    for c in pre['candidates']:
        ids=set(map(str,c['event_ids'])); o22=sorted(ids&by[2022]); o23=sorted(ids&by[2023]); ov=len(o22)+len(o23)
        ev.append({'rank':int(c['rank']),'family_hash':str(c['family_hash']),'member_count':int(c['member_count']),'m2d':float(c['internal_2d_mass']),'modal_contrast':float(c['modal_contrast']),'overlap_2022':o22,'overlap_2023':o23,'overlap_total':ov,'precision':ov/len(ids) if ids else 0.0,'recall':ov/18.0,'gate':len(o22)>=4 and len(o23)>=4 and ov>=8})
    passing=sorted((x for x in ev if x['gate']),key=lambda x:x['rank']); req(passing,'no gate-passing family'); chosen=passing[0]
    baseline={'rank':84,'member_count':1814,'precision':18/1814,'overlap_total':18}
    checks={'preserves_all_18_exact_ids':chosen['overlap_total']==18 and len(chosen['overlap_2022'])==10 and len(chosen['overlap_2023'])==8,'remains_within_partial_rank_band':chosen['rank']<=100,'family_strictly_smaller_than_1814':chosen['member_count']<1814}
    verdict='IMPROVED_SUPPORT_PRUNED_ORBITTRACE_EXTRACTION' if all(checks.values()) else 'NO_CLEAN_SUPPORT_PRUNED_ORBITTRACE_EXTRACTION_IMPROVEMENT'
    result={'schema':'ORBITTRACE_M2D_SUPPORT_PRUNED_REPLAY_REVEAL_REPAIR','verdict':verdict,'scientific_scan_reexecuted':False,'reveal_repair_only':True,'pretruth_gzip_sha256':PRE_GZ,'pretruth_inner_sha256':PRE_INNER,'canonical_zip_sha256':CAN_SHA,'candidate_count':8884,'chosen_family':chosen,'baseline_pr1378':baseline,'checks':checks,'member_reduction':1814-chosen['member_count'],'member_reduction_fraction':(1814-chosen['member_count'])/1814,'precision_multiplier':chosen['precision']/baseline['precision'],'interpretation_boundary':'Post-promotion, post-reveal apples-to-apples characterization only; not a new pristine blind discovery claim and not used to tune support-pruned v1.'}
    (a.output/'SUPPORT_PRUNED_REPLAY_REVEAL_REPAIR.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    lines=['# Support-pruned M2D OrbitTrace replay — reveal-only repair','',f"Verdict: **`{verdict}`**",'',f"- rank: **{chosen['rank']}** (PR #1378: **84**)",f"- exact overlap: **{chosen['overlap_total']}/18** (2022 **{len(chosen['overlap_2022'])}/10**, 2023 **{len(chosen['overlap_2023'])}/8**)",f"- family members: **{chosen['member_count']}** (PR #1378: **1,814**; reduction **{result['member_reduction']}**, {100*result['member_reduction_fraction']:.1f}%)",f"- precision: **{chosen['precision']:.6f}** (PR #1378: **{baseline['precision']:.6f}**; {result['precision_multiplier']:.3f}x)",f"- M2D: `{chosen['m2d']:.17g}`",f"- family hash: `{chosen['family_hash']}`",'',result['interpretation_boundary']]
    (a.output/'SUPPORT_PRUNED_REPLAY_REVEAL_REPAIR.md').write_text('\n'.join(lines)+'\n'); print('\n'.join(lines))
if __name__=='__main__': main()
