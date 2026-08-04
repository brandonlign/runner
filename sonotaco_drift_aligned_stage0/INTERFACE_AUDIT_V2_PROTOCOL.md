# SonotaCo drift-aligned inherited-interface audit v2

Status: frozen after parser v1 completed every source check but failed while serializing a Python `set` into its JSON report.

The sole permitted change is report normalization: values returned by `ast.literal_eval` that are not native JSON types are converted deterministically (`set`/`frozenset` to sorted lists, bytes to hexadecimal, complex numbers to real/imaginary objects, and ellipsis to a string). No source hash, AST inspection, required interface, gate, or scientific boundary changes.

The audit decodes only the exact inherited baseline, Mondrian scorer, and SonotaCo adapter sources. It may compile and AST-parse those sources, but it may not request a meteor archive, mapping artifact, event row, label, score, fold result, or endpoint. SonotaCo 2024 and GhostStream remain untouched.
