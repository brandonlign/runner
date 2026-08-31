#!/usr/bin/env python3
"""Locked entry point for frozen Oyashio all-anchor path ranking.

Only patches a defensive post-hoc truth-evaluation edge case: anchors for which
no geometry reaches the frozen 90% valid-fraction requirement are skipped by
truth matching instead of trying to build a path from NaN geometry. Candidate
generation, scores, ranks and all frozen scientific constants are unchanged.
"""
from __future__ import annotations
import math
import numpy as np
from scipy.spatial import cKDTree
import oyashio_anchored_path_ranking as p


def truth_evaluate_safe(scored):
    raw,dense=p.base.truth_dense();results=[];invalid_n=0
    for z in scored:
        if (not np.isfinite(z['anchor_max_score']) or z['best_observed_sigma_px'] is None or
            not np.isfinite(z['best_length_pc']) or not np.isfinite(z['best_orientation_deg']) or not np.isfinite(z['best_turn_deg'])):
            invalid_n+=1
            continue
        path=p.best_path_points(z,True);ptree=cKDTree(path);d,_=ptree.query(dense)
        ep=min(float(np.linalg.norm(np.array([z['x_px'],z['y_px']])-raw[0])),
               float(np.linalg.norm(np.array([z['x_px'],z['y_px']])-raw[-1])))
        so=float(z['best_observed_sigma_px']);cov=float(np.mean(d<=2*so));med=float(np.median(d));sep_pc=ep*p.PC_PER_PX
        assoc=bool(sep_pc<=p.PASS_ENDPOINT_PC and cov>=p.PASS_COVERAGE and med<=p.PASS_MEDIAN_SIGMA*so)
        results.append({'anchor_index':z['anchor_index'],'rank':z['rank'],'anchor_max_score':z['anchor_max_score'],
                        'endpoint_distance_px':ep,'endpoint_distance_pc':sep_pc,'truth_coverage_within_2sigma':cov,
                        'truth_median_distance_px':med,'selected_sigma_px':so,'truth_associated_geometry':assoc,
                        'passes_ranked_positive_gate':bool(assoc and z['rank']<=p.PASS_RANK_MAX)})
    assoc=[z for z in results if z['truth_associated_geometry']];assoc.sort(key=lambda q:q['rank'])
    passes=[z for z in assoc if z['passes_ranked_positive_gate']]
    return {'pass':bool(passes),'pass_rule':{'endpoint_pc_max':p.PASS_ENDPOINT_PC,'coverage_min':p.PASS_COVERAGE,
            'median_distance_sigma_max':p.PASS_MEDIAN_SIGMA,'anchor_rank_max':p.PASS_RANK_MAX},
            'best_truth_associated':assoc[0] if assoc else None,'truth_associated_n':len(assoc),'passing_n':len(passes),
            'anchors_without_valid_geometry_n':invalid_n,'top_truth_associated':assoc[:20]}

p.truth_evaluate=truth_evaluate_safe
if __name__=='__main__':
    p.main()
