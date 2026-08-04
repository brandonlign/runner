# SonotaCo 2023 replacement-confirmation feasibility audit

Status: frozen before any SonotaCo 2023 meteor row, label, score, p-value, fold, support count, or endpoint is opened or computed.

## Why this audit exists

PR #136 passed the complete standalone SonotaCo 2025 final-development standard and froze the final method as the exact fixed-4° coverage-normalized Mondrian anchored four-clique detector.

PR #134 prematurely opened SonotaCo 2024 before that required 2025 benchmark had passed. SonotaCo 2024 is therefore irreversibly consumed and cannot serve as the reserved one-shot confirmation panel.

A replacement panel may be considered only if the method, source, thresholds, calibration, seeds, gates, and interpretation remain frozen. The replacement year is selected without seeing any scientific content:

- choose SonotaCo 2023 because it is the most recent annual SonotaCo panel earlier than 2024;
- repository code search, PR search, and commit search performed before this branch found no prior reference to `023a.zip` or `SonotaCo 2023`;
- do not inspect 2022 or any earlier panel unless this exact 2023 feasibility audit fails for availability or structural incompatibility.

## Permitted actions

This audit may only:

1. fetch all runner Git refs and search every pre-existing branch tree and commit message for prior references to `023a.zip`, its exact URL, or `SonotaCo 2023`;
2. download the fixed official archive URL `https://www.astro.sk/iaumdcDB/public/data/SNMv3/023a.zip`;
3. record HTTP provenance, byte length, and SHA-256;
4. read the ZIP central directory and record member names, compressed/uncompressed sizes, CRC values, and timestamps;
5. verify that the archive is structurally a ZIP and contains at least one plausible tabular member.

The audit may not open or extract a member, read a CSV header or row, count meteors, map labels, compute solar longitude, inspect shower support, execute the detector, or calculate any scientific endpoint.

## Frozen pass rule

Pass only if:

- no prior pre-existing runner branch tree or commit message contains a SonotaCo 2023 archive/data reference;
- the exact official URL downloads successfully;
- the archive is non-empty and has a stable recorded SHA-256;
- the central directory is readable;
- at least one member has a plausible `.csv`, `.txt`, or `.dat` suffix;
- no member is opened or extracted;
- the exact final model source SHA-256 remains `747b2b1471f3ba193d68a39dd82ad3ac8506be63b651d45f84ffabb8d1acd301`;
- SonotaCo 2024 is not downloaded or parsed;
- no GhostStream value is present.

A pass authorizes only a separate source-only parser/confirmation protocol audit for SonotaCo 2023. It does not authorize scoring the archive.

No result from SonotaCo 2024 may alter this audit or any future 2023 protocol.
