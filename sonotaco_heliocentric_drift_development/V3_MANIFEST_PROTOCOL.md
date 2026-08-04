# SonotaCo heliocentric drift development v3 manifest repair

Status: frozen after PR #119 stopped before source decoding.

The sole permitted v3 change is to replace the expected outer payload-file SHA-256 with the authoritative hash emitted by PR #119's provenance artifact:

`3d860c665ffeddf68422fdaace31db3a442e03edff828b35db37c9e1b7f064b1`.

The decoded source must still match SHA-256 `10e87a4ada2eaceb5a8852642f786ce3e8e3978ac490844104c346532e41508c` and compile. No source byte, transformation equation, Earth speed, phase span, velocity scale, neighbor pool, quartet search, archive, seed, calibration, comparator, threshold, gate, blind interval, or endpoint changes.

SonotaCo 2024 and GhostStream remain untouched.
