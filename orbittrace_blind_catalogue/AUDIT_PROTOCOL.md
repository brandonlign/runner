# OrbitTrace fixed-4° blind-catalogue source audit

## Purpose

Prepare a post-freeze blind deployment of the exact fixed-4° coverage-normalized Mondrian anchored four-clique detector without changing the detector, calibration rule, score, scale, thresholds, or any prior result.

This audit is source-only. It decodes and inventories the exact frozen detector, baseline, scorer, SonotaCo adapter, and prior targeted-application program already preserved in the repository. It does not download a meteor catalogue, retrieve the canonical OrbitTrace artifact, expose OrbitTrace members, or compute any scientific endpoint.

## Isolation

- Branch: `agent/orbittrace-fixed4-blind-catalogue-audit`.
- No file under `orbittrace_literature_comparison/` or any literature-comparison workflow is modified.
- The blind deployment will use separate workflow, artifact, directory, and concurrency names.
- Literature comparison and blind deployment may run concurrently without cancellation or output collision.

## Frozen method

The primary detector is the exact source with SHA-256:

`747b2b1471f3ba193d68a39dd82ad3ac8506be63b651d45f84ffabb8d1acd301`

The solar-longitude scale remains exactly 4 degrees per distance unit. Existing source components are decoded only to determine their interfaces and to reuse them byte-for-byte.

## Claim boundary

A successful later blind deployment may establish that the frozen detector independently rediscovered OrbitTrace in a catalogue-scale scan. It cannot rewrite the historical chronology: HDBSCAN first exposed the candidate during exploration. The final paper may nevertheless organize the scientific pipeline around the frozen detector as the principal reproducible detection method, with HDBSCAN as an independent corroborating path, provided the blind scan surfaces OrbitTrace without target information.
