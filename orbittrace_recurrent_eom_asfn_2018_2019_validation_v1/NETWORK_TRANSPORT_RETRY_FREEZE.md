# ASFN 2018/2019 validation — NASA network transport retry freeze

## Status

Frozen after technical no-result run `31850281138` and before any subsequent ASFN archive-acquisition attempt.

Run `31850281138` transferred zero archive bytes and never invoked the scientific runner. This freeze changes **only network transport tolerance** for obtaining the same already-pinned archive.

## Scientific bytes remain fixed

- scientific protocol Git blob: `0d90b3db461ff65da3780d507506e4618a2cbf52`;
- scientific runner Git blob: `8f5699326758dd11cc46f9a209049a8ed61dee3a`;
- recurrent-EOM source Git blob: `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`;
- hash-header wrapper Git blob: `0e5fce5b04959ec45c42bb22ed477e48bdc31bde`;
- header-repair audit result SHA-256: `212a52b402187d0bc20c85dc50ba9d0b6b52cbe5126398d9ca7b6b87ffa49ff2`;
- prior retry execution freeze Git blob: `11bf96de9598a5dc6108d8c7d830041c4caf063b`.

## Frozen acquisition identity

Use only:

`https://fireballs.ndc.nasa.gov/public_data/nasfn_2013-2019.zip`

Required downloaded archive SHA-256:

`c091b0f3f87f10badbe5fa38e6c45ba818af99f1c27c2fd6a23be286074c89a4`

No mirror, cached copy, alternate host, alternate NASA release, reconstructed archive, year-specific substitute, or content-level equivalence is authorized.

## Frozen transport behavior

Exactly one workflow acquisition step may use curl with:

- HTTPS URL exactly as above;
- connection timeout 45 seconds;
- total timeout 180 seconds per attempt;
- up to 3 total attempts;
- 5-second delay between failed attempts;
- retry on connection/timeouts/other transport errors;
- output to a fresh local `ASFN_2013_2019.zip` path;
- mandatory exact SHA-256 check immediately after successful transfer.

A failed attempt must remove any partial archive before the next attempt. If all three attempts fail, the run is another technical no-result. If any completed transfer has a SHA different from the frozen identity, fail closed and do **not** retry from another source or inspect its contents.

## Scientific execution

Only after exact archive SHA verification may the already-frozen header-repaired execution run. The first technically valid scientific endpoint remains binding.

No method, parser semantics, year, blind interval, HDBSCAN parameter, recurrence rule, rank, label boundary, evaluator, or gate may change.

## Firewall

This transport repair authorizes no protected target, MAARSY, or DMS access and no ASFN scientific inspection outside the already-frozen validation runner.
