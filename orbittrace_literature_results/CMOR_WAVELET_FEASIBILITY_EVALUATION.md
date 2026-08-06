# CMOR-style 3D wavelet feasibility evaluation

## Question

Can a single checksum-pinned SonotaCo year support a fair implementation of the Brown et al. (2010) CMOR 3D wavelet survey without weakening its published sample-size or temporal-linking rules?

The published survey stacked approximately three million CMOR orbits across seven years into a virtual year, divided that stack into one-degree solar-longitude bins, and required a local maximum to have at least 300 contributing radiants. Candidate maxima were linked only when separated by at most two degrees of solar longitude, and at least three linked points were required.

## Frozen support-only audit

- Workflow: `31077762735`
- Artifact: `8958194513`
- Artifact digest: `sha256:0a401dfceaa624420a2eb27d654623dbeb247d7f8737e9b31748e4fa9d53ddbf`
- Verdict: `PASS_CMOR_WAVELET_FEASIBILITY_AUDIT`
- Decision: `PASSES_NECESSARY_SINGLE_YEAR_SUPPORT_GATE_ONLY`

The audit was frozen before catalogue access and deliberately calculated no wavelet coefficient, local maximum, shower recovery, or comparison endpoint. It read only solar longitude, geocentric speed, speed uncertainty, and convergence angle. Shower labels and OrbitTrace values were not accessed. The existing 20°–55° blind interval was removed before counting.

## Result

After the preregistered quality and blind-interval filters, the one-year catalogue contained 23,662 retained events across 324 available one-degree bins.

| Quantity | Result |
|---|---:|
| Median one-degree-bin count | 50.5 |
| 90th percentile | 175.0 |
| 95th percentile | 237.0 |
| 99th percentile | 313.78 |
| Maximum | 806 |
| Bins with at least 300 total radiants | 5 / 324 |
| Fraction reaching 300 | 0.01543 |
| Three-point chains allowed by the published <=2° gap | 1 |
| Longest supported chain | 3 points |

The five bins reaching the necessary 300-event floor were 125°, 126°, 127°, 141°, and 262° solar longitude. Only 125°–127° formed a valid three-point chain.

## Interpretation

This is not enough to justify a global one-year wavelet survey. The 300-radiant rule applies to events contributing near one specific radiant-speed test point, not to the total population anywhere in the one-degree time bin. Therefore even the single supported chain only passes a necessary condition; it does not establish that any coefficient location would retain 300 local contributors.

The one-year result does, however, justify continuing to the closest published design: a preregistered seven-year SonotaCo virtual-year stack. That next stage must first checksum every annual archive and quantify year-by-year and solar-longitude exposure. No coefficient may be calculated until the stack and exposure treatment are frozen.

The following shortcuts remain prohibited:

- lowering the 300-radiant floor;
- shortening the three-point chain;
- enlarging the one-degree time bins after seeing the result;
- evaluating only known shower coordinates;
- calling a reduced wavelet kernel a faithful Brown et al. reproduction;
- treating failure of SonotaCo support as evidence that the CMOR method performs poorly or that fixed4 wins.

## Current comparator status

The wavelet method is neither beaten nor fully implemented. The one-year route is rejected as globally unsupported, while the seven-year virtual-year input and exposure audit is authorized. HDBSCAN and the full uncertainty-aware Sugar pipeline remain the completed catalogue comparators; fixed4 remains evaluated on the separate sparse-episode task.
