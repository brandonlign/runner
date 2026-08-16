# OrbitTrace topomodal orbit availability v1 — binding result

## Verdict

**PASS_TOPOMODAL_ORBIT_AVAILABILITY_V1**

The exact #1284 sparse-universe orbit audit passed the preregistered 100% completeness requirement. Orbital Fréchet ordering v1 is therefore activated without opening shower truth.

## Binding provenance

- GitHub Actions run: `31978330061`
- Job: `95241090228`
- Artifact: `9271674614`
- Artifact ZIP SHA-256: `8fb72afd22785f7cba8217e83b2bb536f735f0ebcb5b0b1b6f258f891a9052bb`
- Exact #1284 sparse-universe manifest SHA-256: `3ed5c33216d7d1cf2cbc703da088b3a86132e50532fb996cfe475d7f6052d7f8`
- Audited event-ID→orbit mapping SHA-256: `a99fdc71beb8ea78b957c0951191c66bf8c04e6ce04773952ac0c43695619f44`

## Completeness

All required elements (`e`, `q`, `i`, `peri`, `node`) were usable for every event in every frozen sparse panel:

- d128/b0: 5567 / 5567
- d128/b1: 5840 / 5840
- d128/b2: 5857 / 5857
- d128/b3: 5816 / 5816
- d1024/b0: 677 / 677
- d1024/b1: 739 / 739
- d1024/b2: 736 / 736
- d1024/b3: 766 / 766

Union-by-year completeness was also 100%:

- 2022: 9963 / 9963
- 2023: 13117 / 13117

## Firewall / scientific role

- Only exact event IDs already present in the immutable #1284 sparse manifest were eligible for orbital parsing.
- The same 24 monthly source files were required byte-for-byte by their prior manifest SHA-256 values.
- IAU shower number/code and hidden shower truth were not parsed.
- No candidate ranking or Southworth–Hawkins dissimilarity was computed in this stage.
- Solar longitude 20°–55° remained excluded.
- No OrbitTrace target information or target-region orbit was accessed/emitted.
- SonotaCo, ASFN/EFN event-level data, AMOS, MAARSY, and DMS were not accessed scientifically.

## Consequence

The frozen orbital Fréchet successor is authorized exactly as preregistered. No availability-driven change to orbital elements, dissimilarity, center statistic, hierarchy membership, rank key, support, or truth gates is permitted.
