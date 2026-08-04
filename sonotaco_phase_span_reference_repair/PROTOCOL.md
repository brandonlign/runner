# SonotaCo phase-span selector reference-stream repair audit

Status: source-only; frozen before any meteor archive, label, score, p-value, fold, or endpoint is accessed.

PR #125 is invalid because its reference calibration stream used seed prefix `mondrian-span-selector-reference` instead of the protocol-required exact PR #112 prefix `mondrian-multiview-hires-reference`.

The only authorized repair is the literal one-occurrence substitution:

- old: `mondrian-span-selector-reference`
- new: `mondrian-multiview-hires-reference`

No other source byte, threshold, calibration size, selector rule, pseudo-fold, seed, window, parser, comparator, gate, or endpoint may change.

The audit shall decode the repaired source, require SHA-256 `1fc071aeb742b70cadbf19be9bac719e79d57ca7a74ab0ce1cb960a827df4f2a`, compile and AST-parse it, reconstruct the invalid source by reversing that one substitution, and require the reconstructed SHA-256 to equal the exact PR #124 source hash `aab855db949bd520aa142a51a140c6e181918be0428bdee082b427fd1240a569`.

A pass authorizes only a separately frozen rerun of the unchanged PR #125 selector on SonotaCo 2025. SonotaCo 2024 and GhostStream remain untouched.
