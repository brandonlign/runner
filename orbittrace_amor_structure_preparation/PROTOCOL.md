# OrbitTrace AMOR 1990–1999 structure-only preparation — frozen before archive access

## Status and boundary

The full-history audit already established that the IAU MDC AMOR 1990–1999 pool is scientifically untouched in this repository. This preparation freezes how AMOR structural compatibility and a future two-year panel would be determined **before any AMOR archive is downloaded**.

This branch does not authorize archive access. A structure-only Actions run may be triggered only if a successor discovery method has first passed its own frozen development gate.

## Allowed information in a future structure-only run

A future structure audit may:

- retrieve the official IAU MDC radio-data index page and resolve the ten links whose visible labels are `AMOR 1990 - ZIP archive` through `AMOR 1999 - ZIP archive`;
- download those ten ZIP containers;
- record ZIP byte size and SHA-256;
- test ZIP CRC and safe member paths;
- record member names, member byte sizes, and file extensions;
- read explicit documentation/header/schema metadata when structurally identifiable as metadata;
- for reduced single-line meteor files, process records only as opaque physical lines to count nonempty rows, byte lengths, and whitespace-token counts;
- for workbook files, inspect workbook/sheet structure and an explicit header row only, without reading subsequent cell values.

It may not decode, retain, compare, print, classify, threshold, or score any meteor-record token value. In particular it may not read AMOR solar longitude, radiant, speed, orbit, shower label, or target-region value.

## Frozen compatibility requirements

The official IAU MDC radio documentation defines the reduced single-line interface and the relevant scientific fields independently of AMOR values. A structurally valid AMOR year must expose a deterministic documented interface sufficient to obtain, after a later scientific protocol is separately frozen:

- unique meteor identity;
- date or solar longitude sufficient to compute/use solar longitude;
- geocentric radiant RA/DEC;
- geocentric speed Vg;
- q, e, i, argument of perihelion, and longitude of ascending node for post-ranking orbital validation.

No shower label is required.

A structure audit must fail closed if the archive contents cannot be mapped to that documented interface without inspecting scientific meteor values.

## Predeclared future panel-selection rule

If multiple annual AMOR archives are structurally valid, the future external-validation panel is selected using **structure metadata only**:

1. retain years with the same validated parser/schema interface and at least 10,000 opaque meteor records;
2. rank those years by opaque record count descending;
3. choose the two highest-count years; break an exact count tie by earlier calendar year.

This rule is frozen before AMOR archive access. It deliberately selects for statistical power using only catalogue size, not any shower, detector, orbital, or target statistic.

If fewer than two years satisfy the structural requirements, AMOR is an integrity/power no-go and no AMOR scientific-value access follows.

## Scientific firewall

The structure artifact may contain only transport/schema/opaque-count metadata and its selected year pair. It must not contain meteor values. A separate external-validation protocol must then freeze the parser, density normalization, target exclusion, family architecture, rankings, power floors, and scientific gates before the first AMOR meteor value is decoded.

No OrbitTrace target information may be accessed at any stage of this preparation.
