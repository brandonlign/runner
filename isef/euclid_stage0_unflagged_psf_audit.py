#!/usr/bin/env python3
"""PSF audit of every unflagged >20% Stage-0 aperture excursion.

This closes the gap left by Euclid FLG maps: large measurements with no local
INVALID/HOT/COSMIC/CR_REGION/SAT flag are checked against a same-dither PSF
morphology envelope derived independently from ordinary star x epoch controls.
Development field only; survivors are not discoveries.
"""
import json
from pathlib import Path
import numpy as np
import euclid_routed_feasibility as b
import euclid_stage0_psf_validation as pv

RES=Path('results/euclid_routed_feasibility.json'); NPZ=Path('results/euclid_routed_stamps.npz')
FLAGS=Path('results/euclid_stage0_flag_population.json'); CTRL=Path('results/euclid_stage0_psf_controls.json'); OUT=Path('results/euclid_stage0_unflagged_psf_audit.json')

def main():
    base=json.loads(RES.read_text()); cube=np.load(NPZ)['stamps']; f=json.loads(FLAGS.read_text()); c=json.loads(CTRL.read_text())
    grid=min(c['morphology_grids'],key=lambda g:abs(float(g['control_quantile'])-0.95)); lim={'shape_residual_max':float(grid['shape_residual_max']),'shape_correlation_min':float(grid['shape_correlation_min']),'brightest_positive_pixel_fraction_max':float(grid['brightest_positive_pixel_fraction_max'])}
    ra0=float(base['target']['ra']);de0=float(base['target']['dec']);routes={int(g):int(v['k']) for g,v in base['routes'].items()};hs=b.epoch_headers(routes);orig=[]
    for q in hs:
        x,y=b.pix(q,ra0,de0);orig.append((int(round(float(x)))-b.HALF,int(round(float(y)))-b.HALF))
    rows=[]
    events=[e for e in f['events'] if e['abs_excursion']>0.20 and e.get('artifact_flag_in_5x5') is False]
    for e0 in events:
        ra=float(e0['ra']);de=float(e0['dec']);e=int(e0['epoch']);g=e%4;peers=[q for q in range(g,16,4) if q!=e];cuts={}
        for p in [e]+peers:
            px,py=hs[p].w.world_to_pixel_values(ra,de);x=float(px)-orig[p][0];y=float(py)-orig[p][1];z=pv.aligned_cutout(cube[p],x,y);z,_=pv.bgsub(z);cuts[p]=z
        ref=np.nanmedian(np.stack([cuts[p] for p in peers]),axis=0);event=cuts[e];scale,off,nres,corr,_,_=pv.fit_scale(event,ref);dt=pv.diff_template(event,ref)
        bp=float(dt['positive_difference_brightest_pixel_fraction']);passm=bool(np.isfinite(nres) and np.isfinite(corr) and np.isfinite(bp) and nres<=lim['shape_residual_max'] and corr>=lim['shape_correlation_min'] and bp<=lim['brightest_positive_pixel_fraction_max'])
        rows.append({**e0,'same_dither_peers':peers,'event_to_reference_scale':scale,'shape_residual':nres,'shape_correlation':corr,'difference_template_correlation':dt['difference_template_correlation'],'difference_template_residual':dt['difference_template_residual_fraction'],'brightest_positive_pixel_fraction':bp,'passes_empirical_95pct_morphology':passm})
    # group repeated excursions from the same source; true variability may recur, while a consistently unstable/blended source is a source-quality problem.
    grouped={}
    for r in rows:
        key=f"{r['ra']:.10f},{r['dec']:.10f}";grouped.setdefault(key,[]).append(r)
    groups=[]
    for k,v in grouped.items():groups.append({'key':k,'events':len(v),'morphology_passes':sum(x['passes_empirical_95pct_morphology'] for x in v),'epochs':[x['epoch'] for x in v],'max_excursion':max(x['abs_excursion'] for x in v),'rows':v})
    groups.sort(key=lambda x:x['max_excursion'],reverse=True)
    out={'success':True,'note':'all unflagged >20% Stage-0 aperture excursions audited against independently derived 95% empirical PSF morphology envelope; development-field survivors require further validation','morphology_limits':lim,'unflagged_gt20_events':len(rows),'events_passing_morphology':sum(r['passes_empirical_95pct_morphology'] for r in rows),'unique_sources':len(groups),'source_groups':groups}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
