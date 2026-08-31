#!/usr/bin/env python3
"""Frozen all-anchor constant-curvature path ranking on the external Oyashio field.

Implements the score contract in the scientific freeze notes. Candidate source
anchors are generated without the truth track using the exact STScI VEGAMAG
broad pre-morphology selection. All path maxima are computed and anchor-ranked
before the public Oyashio track is consulted for the post-generation recovery
check.

Allowed pixels: GO-16890 UGC9050-DW1 combined F814W + F555W only.
No MATLAS Table-A.1 target and no sealed final-null field may be queried/opened.
"""
from __future__ import annotations
import csv, json, math, time
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter, binary_dilation, map_coordinates
from scipy.spatial import cKDTree
import sep
import oyashio_broad_anchor_count_pilot as base
import oyashio_broad_anchor_exactzp as ezp

OUT=Path('results/oyashio_anchored_path_ranking');OUT.mkdir(parents=True,exist_ok=True)
DIST_MPC=35.2
PC_PER_PX=0.242406840554768*DIST_MPC
PSF_SIGMA_PX=(0.10/0.05)/2.354820045
WIDTHS_PC=np.array([40.,60.,90.,135.,200.])
LENGTHS_PC=np.array([500.,1000.,2000.,4000.])
TURNS_DEG=np.array([-120.,-90.,-60.,-30.,0.,30.,60.,90.,120.])
ORIENT_DEG=np.arange(0.,360.,5.)
STEP_PX=2.0
ANCHOR_EXCLUDE_PC=100.0
MIN_VALID=0.90
BRIGHT_SIGMA=12.0
BRIGHT_DILATE_PX=6
EDGE_PX=64
DOG_RATIO=3.0
BATCH_ANCHORS=16
PASS_ENDPOINT_PC=150.0
PASS_COVERAGE=0.70
PASS_MEDIAN_SIGMA=1.0
PASS_RANK_MAX=3


def robust_sigma(x):
    x=np.asarray(x,float);x=x[np.isfinite(x)]
    if not len(x):return 1.0
    m=float(np.median(x));mad=float(np.median(np.abs(x-m)));s=1.4826*mad
    if not np.isfinite(s) or s<=0:s=float(np.std(x))
    return max(s,1e-12)


def source_anchors():
    rows={f:base.q(f) for f in base.FILTERS};paths={f:base.dl(rows[f]) for f in base.FILTERS}
    a814,w814,m814=base.load(paths['F814W']);a555,w555,m555=base.load(paths['F555W'])
    r814,finite,sig=base.prep_detection(a814)
    objs=sep.extract(np.ascontiguousarray(r814,dtype=np.float32),base.DETECT_SIGMA*sig,minarea=base.MINAREA,mask=~finite)
    x=np.asarray(objs['x'],float);y=np.asarray(objs['y'],float)
    f814,_,_=sep.sum_circle(np.ascontiguousarray(r814,dtype=np.float32),x,y,base.APER_R_PX,mask=~finite)
    sky=w814.pixel_to_world(x,y);x5,y5=w555.world_to_pixel(sky)
    r555,finite5,_=base.prep_detection(a555);f555=np.full(len(x),np.nan,float)
    inside=(x5>=base.APER_R_PX)&(x5<a555.shape[1]-base.APER_R_PX)&(y5>=base.APER_R_PX)&(y5<a555.shape[0]-base.APER_R_PX)
    if np.any(inside):
        v,_,_=sep.sum_circle(np.ascontiguousarray(r555,dtype=np.float32),x5[inside],y5[inside],base.APER_R_PX,mask=~finite5);f555[inside]=v
    zp814,d814=ezp.vega_zp('F814W',m814['date_obs']);zp555,d555=ezp.vega_zp('F555W',m555['date_obs'])
    mi=base.mag_from_flux(f814,zp814);mv=base.mag_from_flux(f555,zp555);color=mv-mi
    broad=np.isfinite(color)&np.isfinite(mi)&(color>base.BROAD_COLOR[0])&(color<base.BROAD_COLOR[1])&(mi>base.BROAD_I[0])&(mi<base.BROAD_I[1])
    ii=np.where(broad)[0]
    anchors=[]
    for k,j in enumerate(ii):
        anchors.append({'anchor_index':k,'source_index':int(j),'x_px':float(x[j]),'y_px':float(y[j]),'i_vega':float(mi[j]),'v_minus_i':float(color[j]),
                        'a_px':float(objs['a'][j]),'b_px':float(objs['b'][j])})
    meta={'source_n':int(len(objs)),'broad_anchor_n':int(len(anchors)),'zero_points':{'F814W':zp814,'F555W':zp555},
          'zero_point_dates':{'F814W':d814,'F555W':d555},'f814_filename':rows['F814W']['filename'],'f555_filename':rows['F555W']['filename']}
    # F555W is no longer needed after anchors are fixed; retain F814W for score.
    paths['F555W'].unlink(missing_ok=True)
    return anchors,a814,paths['F814W'],meta


def stream_preprocess(a):
    finite=np.isfinite(a);zero=(a==0)&finite
    if zero.mean()>0.005:finite &= ~zero
    med=float(np.median(a[finite]));fill=np.where(finite,a,med).astype(np.float32)
    resid=(fill-gaussian_filter(fill,base.BROAD_SIGMA_PX,mode='nearest')).astype(np.float32)
    sig=robust_sigma(resid[finite]);norm=(resid/sig).astype(np.float32)
    bright=gaussian_filter(norm,1.0,mode='nearest')>BRIGHT_SIGMA
    yy,xx=np.mgrid[-BRIGHT_DILATE_PX:BRIGHT_DILATE_PX+1,-BRIGHT_DILATE_PX:BRIGHT_DILATE_PX+1]
    st=(xx*xx+yy*yy)<=BRIGHT_DILATE_PX**2
    bright=binary_dilation(bright,structure=st)
    valid=finite&~bright
    e=EDGE_PX;valid[:e,:]=False;valid[-e:,:]=False;valid[:,:e]=False;valid[:,-e:]=False
    return norm,valid,{'native_resid_sigma':sig,'finite_fraction':float(finite.mean()),'bright_mask_fraction':float(bright.mean()),'analysis_valid_fraction':float(valid.mean())}


def response_maps(norm,valid):
    maps=[];meta=[]
    for W in WIDTHS_PC:
        si=(W/2.0)/PC_PER_PX;so=math.sqrt(si*si+PSF_SIGMA_PX*PSF_SIGMA_PX)
        narrow=gaussian_filter(norm,so,mode='nearest');wide=gaussian_filter(norm,DOG_RATIO*so,mode='nearest')
        r=(narrow-wide).astype(np.float32);rs=robust_sigma(r[valid]);r=(r/rs).astype(np.float32);r[~valid]=0
        maps.append(r);meta.append({'width_pc':float(W),'intrinsic_sigma_px':float(si),'observed_sigma_px':float(so),'dog_robust_sigma_before_standardization':float(rs)})
        del narrow,wide
    return maps,meta


def geometry_xy(ax,ay,phi,s,turn_rad,Lpx):
    # ax,ay shape (B,1,1); phi shape (1,O,1); s shape (1,1,N)
    if abs(turn_rad)<1e-12:
        x=ax+s*np.cos(phi);y=ay+s*np.sin(phi)
    else:
        k=turn_rad/Lpx
        x=ax+(np.sin(phi+k*s)-np.sin(phi))/k
        y=ay-(np.cos(phi+k*s)-np.cos(phi))/k
    return x,y


def scan(anchors,maps,valid,response_meta):
    A=len(anchors);best=np.full(A,-np.inf,np.float32)
    best_len=np.full(A,np.nan);best_turn=np.full(A,np.nan);best_ori=np.full(A,np.nan);best_w=np.full(A,-1,int);best_vfrac=np.zeros(A,float)
    va=valid.astype(np.float32);oris=np.deg2rad(ORIENT_DEG)[None,:,None]
    excl=ANCHOR_EXCLUDE_PC/PC_PER_PX
    for Lpc in LENGTHS_PC:
        Lpx=Lpc/PC_PER_PX
        if Lpx<=excl+STEP_PX:continue
        s=np.arange(excl,Lpx+1e-6,STEP_PX,dtype=np.float32)[None,None,:]
        for td in TURNS_DEG:
            tr=math.radians(float(td))
            for a0 in range(0,A,BATCH_ANCHORS):
                a1=min(A,a0+BATCH_ANCHORS);sub=anchors[a0:a1]
                ax=np.array([z['x_px'] for z in sub],dtype=np.float32)[:,None,None]
                ay=np.array([z['y_px'] for z in sub],dtype=np.float32)[:,None,None]
                x,y=geometry_xy(ax,ay,oris,s,tr,Lpx)
                shp=x.shape;xf=x.ravel();yf=y.ravel()
                vm=(map_coordinates(va,[yf,xf],order=0,mode='constant',cval=0.0).reshape(shp)>0.5)
                counts=vm.sum(axis=2);vfrac=counts/shp[2];ok=vfrac>=MIN_VALID
                if not np.any(ok):continue
                # Geometry max over widths, constant width per path.
                gbest=np.full((a1-a0,len(ORIENT_DEG)),-np.inf,np.float32);gwi=np.full(gbest.shape,-1,np.int16)
                nominal_scored=max(Lpx-excl,STEP_PX)
                for wi,(r,rm) in enumerate(zip(maps,response_meta)):
                    vals=map_coordinates(r,[yf,xf],order=1,mode='constant',cval=0.0).reshape(shp)
                    sm=(vals*vm).sum(axis=2);mean=np.divide(sm,counts,out=np.full_like(sm,np.nan,dtype=float),where=counts>0)
                    factor=math.sqrt(nominal_scored/(2.0*rm['observed_sigma_px']))
                    sc=(mean*factor).astype(np.float32);sc[~ok]=-np.inf
                    upd=sc>gbest;gbest[upd]=sc[upd];gwi[upd]=wi
                # Reduce orientations for this length/turn, then update per-anchor max.
                oi=np.argmax(gbest,axis=1);loc=gbest[np.arange(a1-a0),oi]
                for jj,val in enumerate(loc):
                    ai=a0+jj
                    if val>best[ai]:
                        best[ai]=val;best_len[ai]=Lpc;best_turn[ai]=td;best_ori[ai]=ORIENT_DEG[int(oi[jj])]
                        best_w[ai]=int(gwi[jj,int(oi[jj])]);best_vfrac[ai]=float(vfrac[jj,int(oi[jj])])
                del x,y,xf,yf,vm,counts,vfrac,gbest,gwi
    out=[]
    for i,z in enumerate(anchors):
        q=dict(z);wi=int(best_w[i]);q.update({'anchor_max_score':float(best[i]),'best_length_pc':float(best_len[i]),'best_turn_deg':float(best_turn[i]),
            'best_orientation_deg':float(best_ori[i]),'best_width_pc':float(WIDTHS_PC[wi]) if wi>=0 else None,
            'best_observed_sigma_px':float(response_meta[wi]['observed_sigma_px']) if wi>=0 else None,'best_valid_fraction':float(best_vfrac[i])})
        out.append(q)
    order=sorted(range(A),key=lambda i:(-out[i]['anchor_max_score'],out[i]['anchor_index']))
    for rank,i in enumerate(order,1):out[i]['rank']=rank
    return out


def best_path_points(z,include_core=True):
    Lpx=z['best_length_pc']/PC_PER_PX;start=0.0 if include_core else ANCHOR_EXCLUDE_PC/PC_PER_PX
    s=np.arange(start,Lpx+1e-6,STEP_PX,dtype=float)
    phi=math.radians(z['best_orientation_deg']);tr=math.radians(z['best_turn_deg'])
    if abs(tr)<1e-12:
        x=z['x_px']+s*np.cos(phi);y=z['y_px']+s*np.sin(phi)
    else:
        k=tr/Lpx;x=z['x_px']+(np.sin(phi+k*s)-math.sin(phi))/k;y=z['y_px']-(np.cos(phi+k*s)-math.cos(phi))/k
    return np.c_[x,y]


def truth_evaluate(scored):
    raw,dense=base.truth_dense();results=[]
    for z in scored:
        path=best_path_points(z,True);ptree=cKDTree(path);d,_=ptree.query(dense)
        ep=min(float(np.linalg.norm(np.array([z['x_px'],z['y_px']])-raw[0])),float(np.linalg.norm(np.array([z['x_px'],z['y_px']])-raw[-1])))
        so=float(z['best_observed_sigma_px']) if z['best_observed_sigma_px'] is not None else np.inf
        cov=float(np.mean(d<=2*so));med=float(np.median(d));sep_pc=ep*PC_PER_PX
        assoc=bool(sep_pc<=PASS_ENDPOINT_PC and cov>=PASS_COVERAGE and med<=PASS_MEDIAN_SIGMA*so)
        results.append({'anchor_index':z['anchor_index'],'rank':z['rank'],'anchor_max_score':z['anchor_max_score'],'endpoint_distance_px':ep,'endpoint_distance_pc':sep_pc,
                        'truth_coverage_within_2sigma':cov,'truth_median_distance_px':med,'selected_sigma_px':so,'truth_associated_geometry':assoc,
                        'passes_ranked_positive_gate':bool(assoc and z['rank']<=PASS_RANK_MAX)})
    assoc=[z for z in results if z['truth_associated_geometry']];assoc.sort(key=lambda q:q['rank'])
    passes=[z for z in assoc if z['passes_ranked_positive_gate']]
    return {'pass':bool(passes),'pass_rule':{'endpoint_pc_max':PASS_ENDPOINT_PC,'coverage_min':PASS_COVERAGE,'median_distance_sigma_max':PASS_MEDIAN_SIGMA,'anchor_rank_max':PASS_RANK_MAX},
            'best_truth_associated':assoc[0] if assoc else None,'truth_associated_n':len(assoc),'passing_n':len(passes),
            'top_truth_associated':assoc[:20]}


def main():
    t=time.time();anchors,a814,f814_path,srcmeta=source_anchors();t1=time.time()
    norm,valid,prep=stream_preprocess(a814);del a814
    maps,rmeta=response_maps(norm,valid);del norm;t2=time.time()
    scored=scan(anchors,maps,valid,rmeta);t3=time.time()
    # Truth is first read here, after all anchor maxima and ranks exist.
    truth=truth_evaluate(scored);t4=time.time()
    top=sorted(scored,key=lambda z:z['rank'])[:20]
    rep={'role':'external deep-positive whole-field all-anchor path-ranking gate','matlas_target_science_values_opened':False,'final_null_science_values_opened':False,
         'information_barrier':'Only GO-16890 UGC9050-DW1 combined F814W+F555W opened; truth read after all anchor maxima/ranks',
         'source_anchor':srcmeta,'stream_preprocess':prep,'response_maps':rmeta,
         'frozen_family':{'widths_pc':WIDTHS_PC.tolist(),'lengths_pc':LENGTHS_PC.tolist(),'turns_deg':TURNS_DEG.tolist(),'orientation_deg':ORIENT_DEG.tolist(),
                          'sample_step_px':STEP_PX,'anchor_exclusion_pc':ANCHOR_EXCLUDE_PC,'dog_ratio':DOG_RATIO,'min_valid_fraction':MIN_VALID,
                          'multiplicity_unit':'one maximum per broad source anchor'},
         'anchor_n':len(scored),'field_max_score':float(max(z['anchor_max_score'] for z in scored)),'top_anchors':top,'truth_evaluation':truth,
         'timing_s':{'anchor_generation':t1-t,'response_maps':t2-t1,'path_scan':t3-t2,'posthoc_truth':t4-t3,'total':t4-t}}
    (OUT/'report.json').write_text(json.dumps(rep,indent=2,sort_keys=True)+'\n')
    with (OUT/'anchor_scores.csv').open('w',newline='') as f:
        cols=['rank','anchor_index','source_index','x_px','y_px','i_vega','v_minus_i','a_px','b_px','anchor_max_score','best_length_pc','best_turn_deg','best_orientation_deg','best_width_pc','best_observed_sigma_px','best_valid_fraction']
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader();
        for z in sorted(scored,key=lambda q:q['rank']):w.writerow({k:z.get(k) for k in cols})
    f814_path.unlink(missing_ok=True)
    print(json.dumps({'anchor_n':len(scored),'field_max_score':rep['field_max_score'],'top5':[{'rank':z['rank'],'xy':[z['x_px'],z['y_px']],'score':z['anchor_max_score'],'L':z['best_length_pc'],'turn':z['best_turn_deg'],'ori':z['best_orientation_deg'],'W':z['best_width_pc']} for z in top[:5]],
                      'truth_evaluation':truth,'timing_s':rep['timing_s']},indent=2))
    raise SystemExit(0 if truth['pass'] else 3)

if __name__=='__main__':main()
