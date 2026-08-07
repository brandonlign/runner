# Multiplicity v5 pre-data implementation correction

## Status of the first execution

Workflow run `31194941606` failed before the first holdout catalogue call. The preregistration/source guards and frozen factorization guard passed, then `run_holdout.py` stopped immediately after loading the support module because it asserted that the runtime-presented support years were the raw support-source years.

No 2020 or 2021 GMN monthly file was fetched or parsed. The first holdout data access in the implementation is the later call to `support.parse_catalogue(base)`, which was never reached.

## Source-only diagnosis

Exact source-only audit run `31195349735` verified:

- frozen raw fixed4 support source SHA-256: `fa18a19c08c6824c66606cbd92095dc3605cbcc30f17a468c9e525e7c6ff4a62`;
- frozen catalogue-v3 runtime SHA-256: `ef3e69317af59fdac7a030edc77f742fc4772473d7f16b719b5d804cd4117f51`;
- raw fixed4 `YEARS = (2022, 2023, 2024, 2025)`;
- raw fixed4 `CORPUS = "gmn-known-shower-wrapper-development-2022-2025-excluding-sol20-55"`;
- raw fixed4 `RANKING_VARIANTS = ("persistence", "mean_year_strength", "sqrt_support_strength", "min_year_strength", "size_penalized_strength")`;
- the catalogue-v3 runtime loader executes the exact raw support source and then overwrites `YEARS`, `MONTH_KEYS`, `CORPUS`, and `RANKING_VARIANTS` with catalogue-v3 wrapper values.

The source audit accessed no meteor catalogue or OrbitTrace target information.

## Allowed correction

The retry will change no scientific method, ranking definition, threshold, calibration count, family rule, holdout year, target exclusion, or pass gate.

Before the first catalogue call it will:

1. verify the runtime-presented wrapper values exactly;
2. restore the audited raw fixed4 `CORPUS` and raw fixed4 `RANKING_VARIANTS`;
3. substitute only the preregistered temporal globals `YEARS = (2020, 2021)` and the exact 24 monthly keys;
4. verify all restored/substituted globals;
5. then proceed to the same first catalogue call.

This is an implementation-only correction required to make the loaded module equal the preregistered exact frozen fixed4 proposal generator, apart from the already-preregistered 2020–2021 temporal substitution.
