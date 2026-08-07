# OrbitTrace sparse-support multiplicity — SonotaCo 2017/2019 locked score/label holdout

## Status

Preregistered **before any SonotaCo 2017 or 2019 shower-label access or multiplicity/v3/Brown/fixed4 scientific-score computation for this holdout**.

This is not a raw-data-pristine holdout. Both annual archives have prior transport/input exposure. Actions run `31202654482`, artifact `9003434595`, froze the boundary that neither year has had its shower labels or detector-ranking endpoints exposed for this test:

- 2017: archive bytes were transported in the failed 2015/2017 chain, but the 2015 parser raised first, before the 2017 parser was invoked or any hidden-panel/scoring/ranking stage was reached.
- 2019: the prior CMOR multiyear input audit read only solar longitude, speed, speed uncertainty, and convergence angle; it explicitly read no shower labels and computed no wavelet coefficient/candidate endpoint.

Any result must therefore be described as a **prospectively locked scientific-score/label external holdout**, never as a pristine first-access dataset.

## Frozen scientific method

No methodology development is permitted on this panel.

1. Years are exactly **2017 and 2019**.
2. Solar longitude **20°–55° inclusive is excluded before shower-label access**.
3. Proposal generation is the exact frozen target-free fixed4 sparse-support scanner and family linker used by multiplicity v5:
   - calibration negatives per bin: 128
   - shortlist: 64; exact audit shortlist: 128
   - minimum anchor count: 2
   - maximum retained quartets per bin: 512
   - minimum component events: 4
   - minimum component quartets: 2
   - minimum family years: 2
   - family-link radius: 1.5
4. One deterministic 128-event local episode is constructed for each family/year exactly as in frozen multiplicity v5.
5. The exact frozen multi-anchor v3 and independent Brown comparator are computed.
6. Primary score is the already-frozen scale-free multiplicity term:

   `M = (v3 / Brown)^2`

7. Primary family ordering is unchanged from v5: worst-year multiplicity descending, then two-year geometric mean descending, then stable family id.
8. Comparators are unchanged fixed4 persistence and Brown ranking; v3 is reported descriptively but is not substituted for the primary rank.
9. No multiplicity p-value, RRF, threshold search, weight search, family-link search, endpoint search, or year-specific tuning is allowed.

## Frozen endpoint

Development had 197 recurrent families and used top 100. To preserve that selection fraction rather than repeat the underpowered literal-top-100 problem, the endpoint is:

`K = ceil(100 * N / 197)`

where `N` is the number of recurrent families in the 2017/2019 panel.

No alternate K may be reported as a pass endpoint.

## Frozen power requirements

The scientific outcome is **INCONCLUSIVE** rather than pass/fail unless all are true:

- `K >= 30`
- `N - K >= 30`
- at least 30 eligible/qualified known-shower matches under the unchanged evaluation rule

The unchanged known-shower qualification rule is overlap >=4 and family precision >=0.50.

## Frozen pass gates

If powered, all three are required:

1. multiplicity recovered known showers at K >= Brown recovery at K + 1;
2. multiplicity recovery at K >= `ceil(0.90 * fixed4 recovery at K)`;
3. multiplicity top-K dominant-family precision >= 0.50.

Failure of any required gate is a scientific failure. No post-result relaxation or replacement endpoint is permitted.

## Frozen parser/integrity requirements

The exact SonotaCo parser integrity gates inherited from the validated transported parser remain unchanged, including:

- exact annual member/header structure;
- zero malformed selected rows;
- blind interval removed before label access;
- native shower-token syntax fraction >=0.90;
- mapped nonbackground fraction >=0.90;
- at least 30 supported native codes (>=20 events each);
- at least 10,000 sporadic events after ESV removal;
- at least 30 distinct mapped labeled showers.

A parser/integrity failure yields no scientific ranking result and **must not be repaired by relaxing these gates**.

Frozen parser sources:

- 2017 parser SHA-256: `ee81d66b318ed2fa473ddfcee4c1cea0ef8ba08cba33da47103fd7c53ee625dc`
- 2019 source-only transported parser SHA-256: `301a711e4de43566ba434f2d4a94fc38a85714a33dcee45e26cb19340101ea43`

The 2019 parser was produced in Actions run `31203088669`, artifact `9003602054`, by year-identifier-only transport from the frozen 2017 parser, with no catalogue/label/score access and all parser gates unchanged.

## Frozen archive identity

The evaluation must use the exact already-exposed raw archive identities:

- SonotaCo 2017 archive SHA-256: `1db43348806a44490fde8936529541754411b16825f2caea240378cda11c77cf`
- SonotaCo 2019 archive SHA-256: `d49c37f5a9f7f089973d7029b840283f26ca9d915c137152a6f4368bbf5aabb4`
- SonotaCo 2019 annual member SHA-256 from the prior input-only audit: `8d80ec18108c04ace4f1a2f3daeaa05ab1e7d879022c2db8b80185d28f5aa11f`

An archive hash mismatch is an integrity failure before scientific interpretation.

## Claim boundary

OrbitTrace target coordinates, members, activity interval contents, identity, and excluded-region records remain inaccessible throughout this holdout.

A powered scientific pass would establish that the frozen multiplicity ranking transfers to an external survey/year pair whose **scientific labels and ranking endpoints were unseen at preregistration time**. It would not retroactively make the raw archives pristine, and this distinction must be preserved in any paper claim.

Even a pass does **not** itself reveal OrbitTrace. It authorizes freezing a separate final target-free discovery-application protocol before the 20°–55° target region is opened.
