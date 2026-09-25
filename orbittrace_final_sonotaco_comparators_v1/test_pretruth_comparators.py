#!/usr/bin/env python3
from __future__ import annotations

import numpy as np

import pretruth_comparators as adapter


def records(n=12):
    return [
        {
            "id": f"E{i:03d}", "year": 2013,
            "sol": float(100+i), "sun_lon": float(-20+i), "ecl_lat": float(i%5), "vg": 30.0,
            "ra": float(120+i), "dec": 10.0, "ra_sd": 0.2, "dec_sd": 0.3, "vg_sd": 0.4,
            "q": 0.5, "e": 0.8, "qc": 20.0, "ncam": 2.0,
            "iau": 0, "complex_key": "HIDDEN",
        }
        for i in range(n)
    ]


class FakeMaster:
    def __init__(self, component_id, recurrence, members):
        self.component_id=component_id; self.recurrence=recurrence; self.members=np.asarray(members)
        self.membership_probability=np.ones(len(members),dtype=float)


class FakeMerger:
    def __init__(self, n): self.n=n; self.calls=[]
    def add_iteration(self, iteration, clusters): self.calls.append((iteration,clusters))
    def finalize(self): return [FakeMaster(3,120,[0,1,2,3,4]), FakeMaster(7,90,[5,6,7,8,9])]


class FakeSugar:
    __source_sha256__=adapter.SUGAR_CORE_SHA256
    MIN_SAMPLES=5; EPS_PERCENTILE=23.0; CLONE_ITERATIONS=1000
    MERGE_OVERLAP_FRACTION=0.5; MIN_RECURRENCE=100; STRONG_RECURRENCE=500; SEED_ROOT=20170209
    OverlapGraphMerger=FakeMerger
    seeds=[]
    @staticmethod
    def stable_seed(*parts):
        FakeSugar.seeds.append(parts)
        return 12345
    @staticmethod
    def feature_matrix_from_equatorial(sol,ra,dec,vg): return np.zeros((len(sol),6))
    @staticmethod
    def transferred_epsilon(features): return 0.1,np.ones(len(features))*0.1
    @staticmethod
    def clone_feature_matrix(sol,ra,dec,vg,ra_sd,dec_sd,vg_sd,seed): return np.zeros((len(sol),6))
    @staticmethod
    def dbscan_clusters(features,epsilon): return [np.asarray([0,1,2,3,4],dtype=np.int32)]
    @staticmethod
    def hard_assignment(event_count, masters, minimum_recurrence=100):
        labels=np.full(event_count,-1,dtype=np.int32); p=np.zeros(event_count)
        retained=[m for m in masters if m.recurrence>=minimum_recurrence]
        for label,m in enumerate(retained):
            for i in m.members: labels[int(i)]=label; p[int(i)]=1.0
        return labels,p


class FakeHDB:
    __source_sha256__=adapter.HDBSCAN_SOURCE_SHA256
    MIN_CLUSTER_SIZE=100; HDBSCAN_VERSION="0.8.44"
    @staticmethod
    def feature_matrix(rs): return np.zeros((len(rs),6))
    @staticmethod
    def run_hdbscan(features,core_dist_jobs):
        labels=np.full(len(features),-1,dtype=np.int32)
        labels[:5]=4; labels[5:10]=9
        p=np.where(labels>=0,0.8,0.0)
        return labels,p,{"cluster_count":2}


def test_sugar_truth_free_and_seed_contract():
    FakeSugar.seeds=[]
    out=adapter.run_sugar(records(),year=2013,sugar=FakeSugar)
    assert out["truth_accessed"] is False
    assert out["corpus_namespace"]=="sonotaco-final-label-free-sugar-v1"
    assert out["comparator_pair_identifier"]=="ORBITTRACE_VS_SUGAR"
    assert out["clone_iterations"]==1000
    assert len(FakeSugar.seeds)==1000
    assert FakeSugar.seeds[0]==(20170209,"sonotaco-final-label-free-sugar-v1",2013,"ORBITTRACE_VS_SUGAR",0)
    assert FakeSugar.seeds[-1]==(20170209,"sonotaco-final-label-free-sugar-v1",2013,"ORBITTRACE_VS_SUGAR",999)
    assert out["retained_family_count"]==1
    assert out["families"][0]["member_ids"]==["E000","E001","E002","E003","E004"]


def test_sugar_quality_fails_closed():
    cases=[("qc",15.0,"convergence-angle"),("vg_sd",4.0001,"speed-uncertainty"),("ra_sd",-0.1,"uncertainty")]
    for key,value,text in cases:
        rs=records(); rs[0][key]=value
        try: adapter.run_sugar(rs,year=2013,sugar=FakeSugar)
        except RuntimeError as exc: assert text in str(exc)
        else: raise AssertionError(f"invalid Sugar {key} accepted")
    rs=records(); rs[0]["ra_sd"]=0.0; rs[0]["dec_sd"]=0.0; rs[0]["vg_sd"]=0.0
    assert adapter.run_sugar(rs,year=2013,sugar=FakeSugar)["truth_accessed"] is False


def test_hdbscan_truth_free():
    out=adapter.run_hdbscan(records(),year=2013,hdbscan_runner=FakeHDB)
    assert out["truth_accessed"] is False
    assert out["retained_family_count"]==2
    assert [x["native_label"] for x in out["families"]]==[4,9]


def test_truth_key_fails_closed():
    rs=records(); rs[0]["shower"]="SECRET"
    try: adapter.run_hdbscan(rs,year=2013,hdbscan_runner=FakeHDB)
    except RuntimeError as exc: assert "truth-bearing key" in str(exc)
    else: raise AssertionError("truth-bearing input was accepted")


def test_year_mismatch_fails_closed():
    rs=records(); rs[0]["year"]=2014
    try: adapter.run_sugar(rs,year=2013,sugar=FakeSugar)
    except RuntimeError as exc: assert "mixed/wrong year" in str(exc)
    else: raise AssertionError("mixed year was accepted")


def test_source_identity_fails_closed():
    old=FakeHDB.__source_sha256__; FakeHDB.__source_sha256__="0"*64
    try:
        try: adapter.run_hdbscan(records(),year=2013,hdbscan_runner=FakeHDB)
        except RuntimeError as exc: assert "decoded-source SHA drift" in str(exc)
        else: raise AssertionError("wrong HDBSCAN source identity was accepted")
    finally: FakeHDB.__source_sha256__=old


if __name__=="__main__":
    test_sugar_truth_free_and_seed_contract(); test_sugar_quality_fails_closed(); test_hdbscan_truth_free(); test_truth_key_fails_closed(); test_year_mismatch_fails_closed(); test_source_identity_fails_closed()
    print("PASS_FINAL_PRETRUTH_COMPARATOR_ADAPTER_SYNTHETIC_TESTS")
