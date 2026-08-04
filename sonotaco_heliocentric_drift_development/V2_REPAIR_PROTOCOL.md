# SonotaCo heliocentric drift development v2 repair

Status: frozen after PR #117 stopped before scoring.

PR #117 verified every source and input hash, then failed only because its synthetic three-event physics self-test passed a `(3, 3)` velocity array to a validator hardcoded for production `(128, 3)` episodes.

The sole permitted v2 change is:

- replace the hardcoded `(128, 3)` output assertion with a general `N × 3` assertion requiring `N` to equal the input event count.

Production episodes remain exactly 128 events through the unchanged inherited episode builder. No transformation equation, Earth speed, coordinate convention, phase span, velocity scale, neighbor pool, quartet search, archive, seed, calibration count, comparator, threshold, gate, blind interval, or endpoint changes.

SonotaCo 2024 and GhostStream remain untouched.

Frozen v2 source SHA-256: `10e87a4ada2eaceb5a8852642f786ce3e8e3978ac490844104c346532e41508c`.
