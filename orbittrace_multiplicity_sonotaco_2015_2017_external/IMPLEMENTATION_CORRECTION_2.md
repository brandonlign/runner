# Implementation-only correction 2 — parser transport hash source

Status: recorded before any SonotaCo 2015 or 2017 archive access.

The second execution attempt stopped in the prerequisite guard before the scientific validation step. No SonotaCo 2015 or 2017 archive was requested.

The prerequisite workflow contained stale manually copied parser SHA-256 literals. The immutable parser-transport artifact from Actions run `31199214174`, artifact `9002098911`, is the authoritative source for the transported parser bytes and records:

- 2015 parser SHA-256: `3d3d5439ec3e4db50ae79e4ea1ef7df02768be949ee24c5e68b01357b63a3d18`
- 2017 parser SHA-256: `ee81d66b318ed2fa473ddfcee4c1cea0ef8ba08cba33da47103fd7c53ee625dc`

The retry guard must verify each downloaded parser against the `source_sha256` stored inside that immutable transport artifact rather than against separately copied literals.

This correction changes no scientific source, protocol, detector geometry, proposal generation, ranking definition, endpoint, pass gate, parser logic, label handling, blindness rule, or target-access rule. `PROTOCOL.md` and `run_external_validation.py` remain unchanged.
