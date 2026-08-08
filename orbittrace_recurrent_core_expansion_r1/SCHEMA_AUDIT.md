# OrbitTrace recurrent-core expansion R1 — GMN schema-only audit

This is a pre-method, schema-only audit for a new research program that is **not** a v8 successor or retune.

Purpose: determine whether the exact GMN monthly transport already used by the frozen target-excluded v8 development exposes orbital-element columns suitable for an independently pre-existing Southworth–Hawkins physical-coherence guard.

Rules:

- inspect only the raw **2022-01** monthly transport used by the existing GMN API;
- do not invoke the trajectory dataframe parser;
- do not parse, convert, persist, print, summarize, or inspect any meteor-event row value;
- search the raw text only for header/schema lines containing the already-known geometry header tokens;
- emit only sanitized header/schema strings, byte count, SHA-256, and package version metadata;
- do not access shower-label values;
- do not access any OrbitTrace coordinate, member, identity, prior family/rank, target-region event, Stage A output, or Stage B output;
- do not execute v8, the blind catalogue, or any target-containing workflow.

No scientific method choice may depend on a meteor value from this audit. A pass only establishes which source columns exist.