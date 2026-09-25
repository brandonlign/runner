#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
from pathlib import Path

P = Path(__file__).with_name('adjudicate_v1.py')
spec = importlib.util.spec_from_file_location('adj', P)
assert spec and spec.loader
adj = importlib.util.module_from_spec(spec); spec.loader.exec_module(adj)


def feas(verdict: str):
    x={'verdict':verdict}
    if verdict==adj.PASS_846:
        x.update({'robustness':{'passing_grid_variants':3},'selected':{'policy':{'model':'ET_d4_l10','threshold':0.5,'cap_ratio':1.0}}})
    return x

assert adj.decide(None,None,None)[0]=='NOT_READY_846'
assert adj.decide(feas(adj.FAIL_846),None,None)[:2]==('FINAL_GMN_METHOD_M0','M0')
assert adj.decide(feas(adj.PASS_846),None,None)[0]=='NOT_READY_850'
assert adj.decide(feas(adj.PASS_846),{'verdict':adj.FAIL_850},None)[:2]==('FINAL_GMN_METHOD_M0','M0')
assert adj.decide(feas(adj.PASS_846),{'verdict':adj.PASS_850},None)[0]=='NOT_READY_852'
assert adj.decide(feas(adj.PASS_846),{'verdict':adj.PASS_850},{'verdict':adj.FAIL_852})[:2]==('FINAL_GMN_METHOD_M0','M0')
assert adj.decide(feas(adj.PASS_846),{'verdict':adj.PASS_850},{'verdict':adj.PASS_852})[:2]==('FINAL_GMN_METHOD_M2','M2')
print('PASS_FINAL_GMN_ADJUDICATOR_V1_SYNTHETIC_STATES')
