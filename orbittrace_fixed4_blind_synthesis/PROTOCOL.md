# OrbitTrace fixed-4° blind catalogue synthesis

Status: frozen artifact-only synthesis; no detector or catalogue rerun is authorized.

Execution authorization: verify the two exact final artifacts and apply only the fixed synthesis rule below.

## Purpose

Synthesize the two independently frozen catalogue wrappers applied to the same immutable fixed-4° coverage-normalized Mondrian anchored four-clique core.

This stage is artifact-only. It does not rerun a detector, parse a meteor catalogue, access an unfrozen family list, change a threshold, merge families, rerank candidates, or create a third wrapper.

## Frozen evidence

### Broad ranked-quartet recurrence wrapper

- branch / PR: `agent/orbittrace-fixed4-blind-catalogue-audit`, PR #164;
- complete 2019–2025 plus January–July 2026 GMN sporadic corpus;
- final artifact ID `8957230278`;
- artifact ZIP SHA-256 `2ee3d5c9edf299c0f9ea69b2d6254d7918e0aa659f8cc2c659bb99ff2dfc0d17`;
- frozen verdict `NO_BLIND_ORBITTRACE_RECOVERY`.

### Calibrated component-family wrapper

- branches / PRs: `agent/orbittrace-fixed4-blind-catalogue-scan` and `agent/orbittrace-fixed4-blind-catalogue-reveal`, PRs #168 and #175;
- January 2022–July 2026 GMN sporadic corpus;
- final reveal artifact ID `8958194010`;
- artifact ZIP SHA-256 `74c95a3fd59650126a2a298fc1bab5cc055caa91bff2feae6c9256521fdc00aa`;
- frozen verdict `PARTIAL_BLIND_ORBITTRACE_RECOVERY`.

The calibrated wrapper's final source was committed at `2026-08-06T05:40:18Z`, before the broader wrapper's result was recorded, so it was not created in response to the negative outcome.

## Fixed synthesis rule

- If both wrappers yield full blind rediscovery, classify `ROBUST_FULL_BLIND_REDISCOVERY`.
- If both yield at least partial recovery and neither is negative, classify `CONSISTENT_BLIND_RECOVERY`.
- If one is positive or partial and another is negative, classify `BLIND_RECOVERY_WRAPPER_SENSITIVE`.
- If both are negative, classify `NO_BLIND_RECOVERY_ACROSS_WRAPPERS`.

No wrapper is selected as authoritative after seeing the outcomes. Corpus size, event availability, family definition, thresholding, and retention differences are reported as possible sources of sensitivity but are not used to invalidate either frozen result.

## Claim boundary

`BLIND_RECOVERY_WRAPPER_SENSITIVE` does not support presenting the novel detector as the primary blind discovery method. It supports only the narrower statements that:

1. the frozen detector independently recognized OrbitTrace in targeted testing;
2. one preregistered calibrated catalogue wrapper partially recovered it at blind rank 59;
3. a second, broader preregistered recurrence wrapper produced no exact recovery;
4. catalogue-scale recovery therefore depends materially on the generic wrapper.

The historically accurate project structure remains exploratory HDBSCAN candidate discovery, independent frozen detector recognition and mixed blind-deployment evidence, followed by observational validation.
