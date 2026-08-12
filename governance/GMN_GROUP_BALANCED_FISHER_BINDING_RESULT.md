# Binding result — GMN group-balanced Fisher OOF v1

Run: `31568054338`
Job: `94023953039`
Execution head: `a29b8ae7b77c9d4fc8abc4d08284cf3caaff16e9`
Artifact: `9130216325`
Artifact digest: `sha256:8937d70667c1ef6c12ea73e61d1c2bc50394c157944f8a7ae20cc6890e9b0f21`

Verdict: `FAIL_GMN_GROUP_BALANCED_FISHER_OOF`

Exact Fisher parent controls reproduced before candidate interpretation:
- recovered@100: 69
- recovered@50: 41
- top-100 dominant precision: 0.7677499561973543
- MRR: 0.05055989766869565
- qualified families: 95
- scaled Fisher score SHA256: `9957292fbe41efa407b9bc5b1f4160cdc0899632135a10b56d2f91f04d54c46e`
- parent k=1 margin SHA256: `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`

Binding group-balanced candidate:
- recovered@100: 68
- recovered@50: 42
- top-100 dominant precision: 0.7661089896370331
- MRR: 0.05078951570047268
- qualified families: 95
- raw score median absolute value: 1.2859363639771701
- unit factor: 0.34685401288374357
- raw score SHA256: `4126572752c29adee7b48687a2dc8930e186e6f837ac320e51fb4eadd4263526`
- scaled score SHA256: `1b98f3291396e578fecc9b33ce6ea9cbb37143c45c1e2f9c3fc5c62d99a0ca62`

Fixture multiplicity provenance:
- 226 families / 201 OOF groups;
- 111 positive families / 95 positive class-groups;
- 115 nonpositive families / 114 nonpositive class-groups;
- 8 mixed-class shower groups.

The candidate improved top-50 recovery and MRR but failed the preregistered strict top-100 improvement and precision-nonworsening gates. This exact group-balanced architecture is permanently closed. No prototype/family interpolation, group weights, alternate mixed-group treatment, medoid/robust prototype, covariance change, group-size feature, score calibration, diversity/fusion change, threshold, or post-result rescue is authorized.

Scientific interpretation: fragment multiplicity is not the main source of the 69-family Fisher gain. Removing repeated within-shower class observations slightly changes the ranking but does not improve the parent under the frozen gate.

Firewall remained intact: blind exclusion `[20.0,55.0]`; SonotaCo 2013/2014 access false; target information access false; target-region events accessed false; MAARSY scientific access false; DMS scientific access false.
