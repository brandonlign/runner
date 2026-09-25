#!/usr/bin/env python3
from __future__ import annotations

import csv
import io

from orbittrace_final_sonotaco_normalizer_v1 import normalizer
from orbittrace_final_sonotaco_truth_v1 import truth_boundary as tb


def mapping_audit():
    return {
        "profiles": [
            {"eligible": True, "iau": 7, "complex_key": "PER_COMPLEX", "codes": {"PER": 1}},
            {"eligible": True, "iau": 4, "complex_key": "GEM_COMPLEX", "codes": {"GEM": 1}},
            {"eligible": False, "iau": 99, "complex_key": "NOPE", "codes": {"BAD": 1}},
        ]
    }


def annual_csv():
    header=list(normalizer.EXPECTED_EFFECTIVE_HEADER)+[""]
    idx={x:i for i,x in enumerate(normalizer.EXPECTED_EFFECTIVE_HEADER)}
    def row(sol, shower):
        v=["0"]*normalizer.EFFECTIVE_HEADER_WIDTH
        v[idx["soldeg"]]=str(sol); v[idx["shower"]]=shower
        return v
    b=io.StringIO(newline=""); w=csv.writer(b); w.writerow(header)
    w.writerow(row(10,"PER_JA"))          # physical row 2 mapped
    w.writerow(row(60,""))                # row 3 native background
    w.writerow(row(70,"SPO_JA"))          # row 4 native background
    w.writerow(row(80,"XYZ_JA"))          # row 5 valid syntax, unmapped
    w.writerow(row(90,"BROKEN"))          # row 6 invalid syntax
    w.writerow(row(100,"GEM_JA"))         # row 7 mapped
    return b.getvalue().encode()


def freeze(ids, comparator="Sugar"):
    return {
        "year": 2013,
        "comparator": comparator,
        "pretruth_outputs_frozen": True,
        "truth_accessed_before_freeze": False,
        "target_information_access": False,
        "target_region_access": False,
        "pairwise_event_ids_sha256": tb.canonical_ids_sha256(ids),
        "orbittrace_primary_output_sha256": "1"*64,
        "comparator_primary_output_sha256": "2"*64,
        "orbittrace_source_manifest_sha256": "3"*64,
        "comparator_source_manifest_sha256": "4"*64,
    }


def test_mapping_and_reference_background():
    ids=[f"SNT2013:{i}" for i in range(2,8)]
    truth,audit=tb.parse_truth_after_freeze(
        annual_csv(), year=2013, comparator="Sugar", requested_event_ids=ids,
        mapping_audit=mapping_audit(), mapping_audit_sha256=tb.MAPPING_AUDIT_SHA256,
        pretruth_freeze=freeze(ids),
    )
    assert truth["SNT2013:2"]=="PER_COMPLEX"
    assert truth["SNT2013:7"]=="GEM_COMPLEX"
    for i in (3,4,5,6): assert truth[f"SNT2013:{i}"]=="SPORADIC"
    assert audit["status_counts"]=={
        "invalid_native_syntax_reference_background":1,
        "mapped_known_shower":2,
        "native_background":2,
        "unmapped_native_code_reference_background":1,
    }
    assert audit["truth_accessed_before_freeze"] is False
    assert audit["detector_rerun_or_mutation_after_truth"] is False


def test_truth_before_freeze_fails_closed():
    ids=["SNT2013:2"]
    f=freeze(ids); f["pretruth_outputs_frozen"]=False
    try:
        tb.parse_truth_after_freeze(annual_csv(),year=2013,comparator="Sugar",requested_event_ids=ids,
            mapping_audit=mapping_audit(),mapping_audit_sha256=tb.MAPPING_AUDIT_SHA256,pretruth_freeze=f)
    except RuntimeError as exc: assert "not frozen" in str(exc)
    else: raise AssertionError("truth opened without frozen outputs")


def test_event_universe_hash_fails_closed():
    ids=["SNT2013:2"]
    f=freeze(ids); f["pairwise_event_ids_sha256"]="0"*64
    try:
        tb.parse_truth_after_freeze(annual_csv(),year=2013,comparator="Sugar",requested_event_ids=ids,
            mapping_audit=mapping_audit(),mapping_audit_sha256=tb.MAPPING_AUDIT_SHA256,pretruth_freeze=f)
    except RuntimeError as exc: assert "event-ID freeze hash mismatch" in str(exc)
    else: raise AssertionError("mismatched event universe accepted")


def test_target_interval_requested_row_fails_closed():
    # Construct a requested row inside the sealed interval. The truth parser must reject it even if
    # a malformed caller tried to smuggle such an ID into an otherwise frozen-looking manifest.
    header=list(normalizer.EXPECTED_EFFECTIVE_HEADER)+[""]
    idx={x:i for i,x in enumerate(normalizer.EXPECTED_EFFECTIVE_HEADER)}
    v=["0"]*normalizer.EFFECTIVE_HEADER_WIDTH; v[idx["soldeg"]]="30"; v[idx["shower"]]="PER_JA"
    b=io.StringIO(newline=""); w=csv.writer(b); w.writerow(header); w.writerow(v)
    ids=["SNT2013:2"]
    try:
        tb.parse_truth_after_freeze(b.getvalue().encode(),year=2013,comparator="Sugar",requested_event_ids=ids,
            mapping_audit=mapping_audit(),mapping_audit_sha256=tb.MAPPING_AUDIT_SHA256,pretruth_freeze=freeze(ids))
    except RuntimeError as exc: assert "excluded target interval" in str(exc)
    else: raise AssertionError("target-interval truth row accepted")


def test_mapping_identity_fails_closed():
    ids=["SNT2013:2"]
    try:
        tb.parse_truth_after_freeze(annual_csv(),year=2013,comparator="Sugar",requested_event_ids=ids,
            mapping_audit=mapping_audit(),mapping_audit_sha256="0"*64,pretruth_freeze=freeze(ids))
    except RuntimeError as exc: assert "mapping audit SHA mismatch" in str(exc)
    else: raise AssertionError("wrong mapping audit accepted")


if __name__=="__main__":
    test_mapping_and_reference_background(); test_truth_before_freeze_fails_closed(); test_event_universe_hash_fails_closed(); test_target_interval_requested_row_fails_closed(); test_mapping_identity_fails_closed()
    print("PASS_FINAL_SONOTACO_POSTOUTPUT_TRUTH_BOUNDARY_SYNTHETIC_TESTS")
