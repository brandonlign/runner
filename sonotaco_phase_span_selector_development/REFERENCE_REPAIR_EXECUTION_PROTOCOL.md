# SonotaCo phase-span selector development v2

Status: frozen after the source-only repair audit in PR #130 and before any repaired selector score is computed.

## Authorization

PR #125 was invalidated because the implementation used reference seed prefix `mondrian-span-selector-reference` instead of the exact frozen PR #112 prefix `mondrian-multiview-hires-reference`. PR #130 verified a source change containing exactly that one replacement and no other source change.

The repaired source SHA-256 is `1fc071aeb742b70cadbf19be9bac719e79d57ca7a74ab0ce1cb960a827df4f2a`.

## Unchanged scientific protocol

Execute the exact selector protocol in `sonotaco_phase_span_selector_development/PROTOCOL.md` unchanged:

- exact thresholds 2.5°, 5.0°, and 7.5°;
- exact original 128-calibration stream;
- exact PR #112 512-reference stream;
- exact separate 512-selector-calibration stream;
- exact conditional original-versus-phase3 selection rule;
- exact complex-held-out lexicographic threshold selection;
- exact deterministic pseudo-fold assignment for test negatives;
- exact parser, mapping, labels, quality rules, 128-event episodes, ±10° neighborhoods, anchored 10° bins, positive windows, folds, fixed comparators, alpha levels, endpoints, and gates;
- removal of solar longitude 20°–55° inclusive before labels, reservoirs, windows, scores, folds, or endpoints.

No candidate threshold, seed other than the repaired reference prefix, score, calibration size, test stream, fold, comparator, endpoint, or gate may change.

## Decision rule

The exact original and phase3 controls must reproduce their frozen values before the selector is interpreted. The cross-fitted selector passes only if every gate encoded in repaired source SHA-256 `1fc071aeb742b70cadbf19be9bac719e79d57ca7a74ab0ce1cb960a827df4f2a` passes. Any failed gate kills this exact selector and the negative result must be preserved.

SonotaCo 2024 and GhostStream remain untouched. A complete pass authorizes only the separately frozen next step stated by the original selector protocol; it does not authorize opening SonotaCo 2024.
