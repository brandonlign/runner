# Execute frozen MAARSY RCS Stage 0F

Execution-only trigger for PR #435. The workflow may request only compressed bytes 0–1,048,575, materialize at most 65,536 uncompressed bytes, parse tar headers only, and stop at the first non-empty member. No member payload or scientific value may be read.
