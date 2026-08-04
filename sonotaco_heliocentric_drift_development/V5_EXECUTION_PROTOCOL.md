# SonotaCo heliocentric drift development v5 execution

Status: frozen after the source-only recovery in PR #123 and before any v5 score is computed.

## Authorization and exact repair

PR #123 recovered the exact verified v1 source and the current v2 payload. The v2 source differs from v1 only by generalizing the heliocentric-velocity output validator from the hardcoded `(128, 3)` shape to a two-dimensional `N × 3` shape with `N = len(episode.vg)`. It compiles and has frozen source SHA-256 `10e87a4ada2eaceb5a8852642f786ce3e8e3978ac490844104c346532e41508c`.

The authoritative committed v2 payload file SHA-256 is `34e23118534eca95864d1bee123707316e896bba5169e76d3d5c777bf2d7cb5a`. PRs #119 and #121 produced no scientific result because their transport manifests were wrong or stale.

## Frozen execution

This workflow changes only the outer payload-file SHA-256 used before decoding. It then executes the exact v2 source under the original heliocentric-drift protocol, with unchanged:

- SonotaCo 2025 archive and hash;
- GMN-MDC mapping audit and hash;
- 20°–55° inclusive removal before labels, reservoirs, windows, scores, folds, or endpoints;
- parser, native labels, quality filters, 128-event episodes, ±10° neighborhoods, anchored 10° Mondrian bins, seeds, calibration streams, test negatives, folds, alpha levels, comparators, thresholds, and gates;
- heliocentric transformation, circular-Earth velocity, 10° phase-span gate, 2 km/s velocity scale, six-neighbor quartet search, and candidate definition.

No source byte, scientific setting, endpoint, or pass threshold may change after this execution begins.

## Decision rule

The exact source and all inherited inputs must verify before scoring. The candidate passes only if every gate already encoded in frozen source SHA-256 `10e87a4ada2eaceb5a8852642f786ce3e8e3978ac490844104c346532e41508c` passes. Any failed gate kills this exact heliocentric formulation and its negative result must be preserved.

SonotaCo 2024 and GhostStream remain untouched. A full pass authorizes only the next separately frozen robustness step specified by the candidate protocol.
