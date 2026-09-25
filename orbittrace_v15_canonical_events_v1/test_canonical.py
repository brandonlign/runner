#!/usr/bin/env python3
from __future__ import annotations

from orbittrace_v15_canonical_events_v1 import canonical as c


def expect_fail(fn, text: str) -> None:
    try:
        fn()
    except RuntimeError as exc:
        assert text in str(exc), (text, str(exc))
    else:
        raise AssertionError(f"expected failure containing {text!r}")


def base_event(event_id: str, year: int) -> dict:
    return {
        "id": event_id,
        "year": year,
        "sol": 100.0,
        "sun_lon": -20.0,
        "ecl_lat": 12.5,
        "vg": 30.0,
        "iau": 0,
        "complex_key": "HIDDEN",
    }


def test_gmn_and_sonotaco_exact_projection() -> None:
    gmn = base_event("GMN:1", 2022)
    son = base_event("SNT2013:2", 2013)
    # Extra non-truth transport fields are deliberately projected away; scientific geometry is exact.
    son["ra"] = 123.4
    son["qc"] = 20.0
    got_gmn = c.from_gmn(gmn, allowed_years=(2022, 2023))
    got_son = c.from_sonotaco(son)
    assert tuple(got_gmn) == c.CANONICAL_FIELDS
    assert tuple(got_son) == c.CANONICAL_FIELDS
    assert c.science_tuple(got_gmn) == (100.0, -20.0, 12.5, 30.0)
    assert c.science_tuple(got_son) == (100.0, -20.0, 12.5, 30.0)


def test_maarsy_exact_frozen_scalar_mapping() -> None:
    row = c.from_maarsy_retained_geometry(
        year=2022,
        archive_member="synthetic.h5",
        row_index_0based=7,
        native_sun_lon_deg=100.0,
        native_slon_deg=340.0,
        native_slat_deg=12.5,
        native_vels_km_s=30.0,
    )
    assert row["id"] == "MAARSY|2022|synthetic.h5|7"
    assert c.science_tuple(row) == (100.0, -20.0, 12.5, 30.0)
    # Same physical tuple reaches the detector regardless of survey representation.
    assert c.science_tuple(row) == c.science_tuple(c.from_gmn(base_event("G", 2022), allowed_years=(2022, 2023)))
    # The preserved RCS HDF5 schema is scalar; the stale vector interpretation must fail closed.
    expect_fail(lambda: c.from_maarsy_retained_geometry(
        year=2022, archive_member="synthetic.h5", row_index_0based=8,
        native_sun_lon_deg=100.0, native_slon_deg=340.0, native_slat_deg=12.5,
        native_vels_km_s=(18.0, 24.0, 0.0)), "MAARSY vels is not numeric")


def test_target_firewall_and_roles_fail_closed() -> None:
    assert c.maarsy_keep_from_solar_longitude(19.9999) is True
    assert c.maarsy_keep_from_solar_longitude(20.0) is False
    assert c.maarsy_keep_from_solar_longitude(55.0) is False
    assert c.maarsy_keep_from_solar_longitude(55.0001) is True
    expect_fail(lambda: c.from_maarsy_retained_geometry(
        year=2022, archive_member="x", row_index_0based=0,
        native_sun_lon_deg=20.0, native_slon_deg=0.0, native_slat_deg=0.0,
        native_vels_km_s=30.0), "blinded MAARSY row")
    expect_fail(lambda: c.maarsy_event_id(2020, "x", 0), "outside fixed 2021-support/2022-scored")
    expect_fail(lambda: c.from_sonotaco(base_event("x", 2015)), "outside caller-frozen years")


def test_truth_and_schema_fail_closed() -> None:
    row = base_event("x", 2022)
    row["shower"] = "SECRET"
    expect_fail(lambda: c.from_gmn(row, allowed_years=(2022, 2023)), "truth-bearing key")
    row = base_event("x", 2022)
    row["iau"] = 7
    expect_fail(lambda: c.from_gmn(row, allowed_years=(2022, 2023)), "nonzero IAU")
    row = base_event("x", 2022)
    del row["vg"]
    expect_fail(lambda: c.from_gmn(row, allowed_years=(2022, 2023)), "field(s) missing")


def test_no_cross_survey_quality_recut() -> None:
    # Canonical contract validates units/physical finiteness only. Survey quality cuts remain upstream.
    row = base_event("x", 2022)
    row["vg"] = 4.0
    assert c.from_gmn(row, allowed_years=(2022, 2023))["vg"] == 4.0


if __name__ == "__main__":
    test_gmn_and_sonotaco_exact_projection()
    test_maarsy_exact_frozen_scalar_mapping()
    test_target_firewall_and_roles_fail_closed()
    test_truth_and_schema_fail_closed()
    test_no_cross_survey_quality_recut()
    print("PASS_ORBITTRACE_CANONICAL_EVENT_ADAPTERS_SYNTHETIC")
