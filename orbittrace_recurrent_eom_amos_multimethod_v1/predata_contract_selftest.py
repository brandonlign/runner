from __future__ import annotations

import json
from pathlib import Path

from orbittrace_recurrent_eom_amos_multimethod_v1.predata_contract import (
    RECURRENT_KEYS,
    SUPPLEMENT_KEYS,
    catalogue_hdbscan_eligible,
    pairwise_universe,
    parse_supplement,
    recurrent_projection,
    sugar_eligible,
)


def supplement_row(eid: str, *, ra=0.1, dec=0.1, vg=1.0, qc=20.0, q=0.5, e=0.8):
    return {
        "event_id": eid,
        "ra_sd_deg": ra,
        "dec_sd_deg": dec,
        "vg_sd_km_s": vg,
        "convergence_angle_deg": qc,
        "q_au": q,
        "e": e,
    }


def base(eid: str, year: int, vg: float = 30.0):
    return {
        "id": eid,
        "year": year,
        "sol": 100.0,
        "sun_lon": -20.0,
        "ecl_lat": 5.0,
        "vg": vg,
    }


def must_fail(fn, needle: str) -> None:
    try:
        fn()
    except Exception as exc:
        if needle not in str(exc):
            raise AssertionError(f"wrong failure: {exc}") from exc
    else:
        raise AssertionError(f"expected failure containing {needle!r}")


def main() -> None:
    allow = {"A", "B", "C", "D", "E", "F", "G"}
    rows = [
        supplement_row("A"),                              # both comparators
        supplement_row("B", qc=15.0),                   # HDB yes; Sugar strict >15 no
        supplement_row("C", qc=14.999),                 # neither
        supplement_row("D", vg=4.0),                    # Sugar yes for base vg=30; HDB no (>10%)
        supplement_row("E", ra="", q=0.7, e=0.7),       # HDB yes; Sugar missing RA uncertainty
        supplement_row("F", q=1.2),                     # Sugar yes; HDB q invalid
        supplement_row("G", e=1.01),                    # Sugar yes; HDB e invalid
    ]
    sup = parse_supplement(rows, allow)
    assert list(rows[0]) == list(SUPPLEMENT_KEYS)

    bases = [base(eid, 2023 if eid < "E" else 2024) for eid in sorted(allow)]

    expected_sugar = ["A", "D", "F", "G"]
    expected_hdb = ["A", "B", "E"]
    observed_sugar = [r["id"] for r in bases if sugar_eligible(r, sup.get(r["id"]))]
    observed_hdb = [r["id"] for r in bases if catalogue_hdbscan_eligible(r, sup.get(r["id"]))]
    assert observed_sugar == expected_sugar, (observed_sugar, expected_sugar)
    assert observed_hdb == expected_hdb, (observed_hdb, expected_hdb)

    sugar_rows, sugar_ids = pairwise_universe(bases, sup, "sugar")
    hdb_rows, hdb_ids = pairwise_universe(bases, sup, "catalogue_hdbscan")
    assert sugar_ids == expected_sugar
    assert hdb_ids == expected_hdb
    assert all(tuple(r.keys()) == RECURRENT_KEYS for r in sugar_rows + hdb_rows)
    assert all(set(r).isdisjoint(set(SUPPLEMENT_KEYS[1:])) for r in sugar_rows + hdb_rows)
    assert recurrent_projection(base("A", 2023)) == base("A", 2023)

    # Blank/missing supplemental values never remove a row from the primary sample;
    # they only make it absent from the relevant pairwise universe.
    partial = parse_supplement([supplement_row("A", vg="")], allow)
    assert not sugar_eligible(base("A", 2023), partial["A"])
    assert not catalogue_hdbscan_eligible(base("A", 2023), partial["A"])

    # Fail-closed boundaries.
    must_fail(lambda: parse_supplement([supplement_row("PROTECTED_OR_UNKNOWN")], allow), "non-retained")
    must_fail(lambda: parse_supplement([supplement_row("A"), supplement_row("A")], allow), "duplicate")
    bad_extra = supplement_row("A") | {"extra": 1}
    must_fail(lambda: parse_supplement([bad_extra], allow), "header/order")
    bad_truth = supplement_row("A") | {"shower_code": "ABC"}
    must_fail(lambda: parse_supplement([bad_truth], allow), "truth-bearing")
    bad_inf = supplement_row("A", vg=float("inf"))
    must_fail(lambda: parse_supplement([bad_inf], allow), "finite or blank")
    bad_base = base("A", 2023) | {"label": "ABC"}
    must_fail(lambda: recurrent_projection(bad_base), "truth-bearing")
    must_fail(lambda: pairwise_universe([base("A", 2023)], sup, "not_a_comparator"), "unsupported")

    payload = {
        "verdict": "PASS_AMOS_MULTIMETHOD_PREDATA_CONTRACT_SELFTEST_V1",
        "synthetic_only": True,
        "amos_data_accessed": False,
        "amos_truth_accessed": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "comparator_only_fields_entered_recurrent_eom": False,
        "sugar_fixture_ids": sugar_ids,
        "catalogue_hdbscan_fixture_ids": hdb_ids,
        "recurrent_projection_keys": list(RECURRENT_KEYS),
        "supplement_keys": list(SUPPLEMENT_KEYS),
    }
    Path("amos_multimethod_predata_contract_selftest.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
