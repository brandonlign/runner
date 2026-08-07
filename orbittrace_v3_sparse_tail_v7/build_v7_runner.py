#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p=argparse.ArgumentParser(); p.add_argument('--base',required=True,type=Path); p.add_argument('--output',required=True,type=Path); return p.parse_args()

def rep(s,o,n,label):
    c=s.count(o)
    if c!=1: raise RuntimeError(f'{label}: expected one target, found {c}')
    return s.replace(o,n)

def main():
    a=parse_args(); s=a.base.read_text()
    s=rep(s,'import multi_anchor_energy_v3 as v3\n','import multi_anchor_energy_v3 as v3\nimport v3_sparse_tail_v7 as v7\n','import')
    s=rep(s,'    "orbittrace_multi_anchor_wavelet_energy_v3",\n)\n','    "orbittrace_multi_anchor_wavelet_energy_v3",\n)\nBASE_METHODS = METHODS\nMETHODS = BASE_METHODS + (v7.METHOD_ID,)\n','registry')
    s=rep(s,'    if set(scores) != set(METHODS) or not all(np.isfinite(value) for value in scores.values()):\n','    if set(scores) != set(BASE_METHODS) or not all(np.isfinite(value) for value in scores.values()):\n','score audit')
    s=rep(s,'    calibration: dict[str, dict[int, np.ndarray]] = {method: {} for method in METHODS}\n    for method in METHODS:\n','    calibration: dict[str, dict[int, np.ndarray]] = {method: {} for method in BASE_METHODS}\n    for method in BASE_METHODS:\n','calibration registry')
    s=rep(s,'            calibration[method][bin_index] = values\n\n    for row in negative_rows:\n','            calibration[method][bin_index] = values\n\n    v7_null = {\n        bin_index: v7.calibration_statistics(\n            calibration[v7.PRIMARY][bin_index], calibration[v7.SPARSE][bin_index]\n        ) for bin_index in supported_bins\n    }\n\n    for row in negative_rows:\n','null construction')
    old='''        row["p"] = {
            method: literature.conservative_rank_pvalue(row["scores"][method], calibration[method][row["bin"]])
            for method in METHODS
        }
'''
    new='''        row["p"] = {
            method: literature.conservative_rank_pvalue(row["scores"][method], calibration[method][row["bin"]])
            for method in BASE_METHODS
        }
        stat = v7.target_statistic(
            row["scores"][v7.PRIMARY], row["scores"][v7.SPARSE],
            calibration[v7.PRIMARY][row["bin"]], calibration[v7.SPARSE][row["bin"]]
        )
        row["scores"][v7.METHOD_ID] = stat
        row["p"][v7.METHOD_ID] = v7.final_pvalue(stat, v7_null[row["bin"]])
'''
    if s.count(old)!=2: raise RuntimeError(f'p blocks={s.count(old)}')
    s=s.replace(old,new,2)
    g2025='''        "multi_anchor_energy_v3_rules_frozen": (
            v3.METHOD_ID == "orbittrace_multi_anchor_wavelet_energy_v3"
            and v3.ANGULAR_PROBE_DEG == wavelet.ANGULAR_PROBE_DEG == 4.0
            and v3.SPEED_PROBE_FRACTION == wavelet.SPEED_PROBE_FRACTION == 0.10
            and v3.TRUNCATION_RADIUS == wavelet.TRUNCATION_RADIUS == 4.0
            and v3.KERNEL_DIMENSION == wavelet.KERNEL_DIMENSION == 3.0
            and v3.TOP_ANCHORS == 4
            and all(v3.self_test().values())
        ),
'''
    g2023='''        "wavelet_parameters_unchanged": (
            wavelet.ANGULAR_PROBE_DEG == 4.0
            and wavelet.SPEED_PROBE_FRACTION == 0.10
            and wavelet.TRUNCATION_RADIUS == 4.0
            and wavelet.KERNEL_DIMENSION == 3.0
            and all(wavelet.self_test().values())
        ),
'''
    if g2025 in s: s=rep(s,g2025,g2025+'        "v7_sparse_tail_rule_frozen": all(v7.self_test().values()),\n','2025 gate')
    elif g2023 in s: s=rep(s,g2023,g2023+'        "v7_sparse_tail_rule_frozen": all(v7.self_test().values()),\n','2023 gate')
    else: raise RuntimeError('gate marker missing')
    markers=('        "orbittrace_multi_anchor_wavelet_energy_v3": "new OrbitTrace method development",\n','        "orbittrace_multi_anchor_wavelet_energy_v3": "frozen OrbitTrace v3 transfer",\n')
    for m in markers:
        if m in s:
            s=rep(s,m,m+'        "orbittrace_v3_primary_fixed4_margin_025_v7": "fully calibrated OrbitTrace v7 sparse-tail method",\n','classification'); break
    else: raise RuntimeError('classification marker missing')
    compile(s,str(a.output),'exec'); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(s)
    print('PASS_BUILD_V7_RUNNER',hashlib.sha256(s.encode()).hexdigest())
if __name__=='__main__': main()
