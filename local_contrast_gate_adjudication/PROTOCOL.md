# Local-contrast recurrence gate-only adjudication

Status: frozen before re-reading the preserved result artifact. This stage performs no simulation, injection, calibration, threshold estimation, detector scoring, or parameter change.

## Integrity issue

The prospectively committed development protocol and PR description required both null-family FWER estimates to be at most **0.20** in the 20-trial reduced screen. The generated candidate source instead encoded gate labels and comparisons at **0.15**. Workflow `30877969736` then observed shared-structure FWER exactly **0.20** and emitted `KILL_LOCAL_CONTRAST_RECURRENCE` solely under the inconsistent 0.15 implementation gate.

The original run, source, artifact, metrics, and source-emitted verdict remain immutable. This adjudication does not relabel that implementation as correct; it determines the continuation decision required by the pre-run written protocol.

## Pinned evidence

- workflow run: `30877969736`;
- artifact: `local-contrast-recurrence-development`, ID `8880244804`;
- artifact ZIP digest: `sha256:1885babf888fb8f85a913b7b61b1bcc9f47f08ff3b29eda42ecf9d2badc5c1da`;
- `DEVELOPMENT_PROTOCOL.md` SHA-256: `1cbc95994afbe7121282f3e0ef98ec87323571d239695031c560130b71f1b96d`;
- `results/stage0_result.json` SHA-256: `6eae2e4d5d9afa5778efda2cb134806a3d0fb4e9fcd2dc455f885c01a13e7c91`;
- original derived source SHA-256 recorded by the artifact: `b7589d8d140a37596f19d4993be1e2fdd99a18b8eaa087a02e3c4ce585000071`.

## Frozen adjudication rules

Read only the exact pinned JSON and recompute the six written protocol gates:

1. ideal-null local-contrast FWER at most 0.20;
2. shared-structure-null local-contrast FWER at most 0.20;
3. weak one-year-artifact detection at most 0.20;
4. weak recurrent power is no more than 0.05 below the strongest valid comparator;
5. weak recurrence-margin gain over the strongest valid comparator at least 0.05;
6. strong recurrent power is no more than 0.05 below the strongest valid comparator.

The numerical tolerance is fixed at `1e-12`, matching the original generated source. No metric may be recomputed from catalogs, rounded, replaced, or omitted.

## Decision boundary

- If every written-protocol gate passes, the adjudication verdict is `AUTHORIZE_LOCAL_CONTRAST_FULL_STAGE0_FROM_PROTOCOL`.
- Otherwise the verdict is `KILL_LOCAL_CONTRAST_FROM_PROTOCOL`.

A pass authorizes only a separately frozen, larger, independently seeded Stage-0 benchmark. It does not validate the detector, authorize real-shower testing, access confirmation data, or permit GhostStream application.

No filter width, recurrence order, threshold family, trial count, injection design, comparator, null family, FWER ceiling, or power gate may change.