#!/usr/bin/env python3
"""Aggregate exact per-file shards of the frozen PUNCH long spatial gate."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import punch_kh_real_background_wave_gate as wg
import punch_kh_long_oriented_spatial_gate as ls

OUT=Path('results/punch_kh_long_spatial_sharded_gate');OUT.mkdir(parents=True,exist_ok=True)

def main():
    files=sorted(Path('shards').glob('**/shard.json'))
    if len(files)!=3:raise RuntimeError(f'expected exactly 3 shard.json files, found {len(files)}: {files}')
    reports=[json.loads(p.read_text()) for p in files]
    idx=sorted(r['file_index'] for r in reports)
    if idx!=[0,1,2]:raise RuntimeError(f'expected shard indices 0,1,2; got {idx}')
    trials=[]
    for r in sorted(reports,key=lambda x:x['file_index']):
        if len(r['trials'])!=48:raise RuntimeError(f"incomplete shard {r['file_index']}")
        trials.extend(r['trials'])
    if len(trials)!=144:raise RuntimeError(f'expected 144 trials, got {len(trials)}')
    pos=[r for r in trials if r['kind']=='growth'];null=[r for r in trials if r['kind']!='growth']
    summary={'positive_n':len(pos),'positive_pass_n':sum(r.get('positive_pass',False) for r in pos),'positive_pass_fraction':float(np.mean([r.get('positive_pass',False) for r in pos])) if pos else 0.,'null_n':len(null),'null_false_kh_n':sum(r['kh_call'] for r in null),'p90_of_trial_p90_error_px':float(np.quantile([r['p90_abs_error_px'] for r in trials],.90)),'minimum_valid_fraction':float(min(r['valid_fraction'] for r in trials)),'minimum_eligible_frame_fraction':float(min(r['eligible_frame_fraction'] for r in trials)),'by_wavelength':{str(int(w)):{'n':sum(r['kind']=='growth' and r['wavelength_true']==w for r in trials),'pass_fraction':float(np.mean([r.get('positive_pass',False) for r in pos if r['wavelength_true']==w]))} for w in ls.WAVES}}
    center_ok=summary['p90_of_trial_p90_error_px']<=wg.CENTERLINE_P90_OF_P90_MAX and summary['minimum_valid_fraction']>=wg.CENTERLINE_MIN_VALID and summary['minimum_eligible_frame_fraction']>=wg.CENTERLINE_MIN_ELIGIBLE
    wave_ok=summary['positive_pass_fraction']>=wg.POS_PASS_FRACTION_MIN and summary['null_false_kh_n']<=wg.NULL_FALSE_KH_MAX
    summary.update({'centerline_gate':'PASS' if center_ok else 'FAIL','wave_gate':'PASS' if wave_ok else 'FAIL','gate':'PASS' if center_ok and wave_ok else 'FAIL'})
    serial_fields={k:{'center':[float(x) for x in v['center']],'u':[float(x) for x in v['u']]} for k,v in ls.FIELDS.items()}
    report={'information_barrier':'same three frozen 2025-09-21 non-R3 CTM files as canonical spatial gate; zero R3 pixels','execution_change_only':'three file blocks executed concurrently; exact canonical trial() and gate equations reused','roi':[ls.NY,ls.NX],'base_azimuth_deg':ls.BASE_AZ_DEG,'fields':serial_fields,'wavelengths':ls.WAVES,'peak_sigma':ls.PEAK,'shards':[{'file_index':r['file_index'],'file':r['file']} for r in sorted(reports,key=lambda x:x['file_index'])],'trials':trials,'summary':summary}
    (OUT/'summary.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps(summary,indent=2,sort_keys=True))
    return 0 if center_ok and wave_ok else 3

if __name__=='__main__':raise SystemExit(main())
