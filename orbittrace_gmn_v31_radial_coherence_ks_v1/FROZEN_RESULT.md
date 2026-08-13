# Binding result

Verdict: `FAIL_GMN_V31_RADIAL_COHERENCE_KS_V1`.

First technically valid run: `31724556342`; job `94529583390`; artifact `9190833255`; artifact digest `sha256:4dd2ab7278f63bf851fb8e9189d982b27ae1419c075fafacbc4d5cd5462ecbc2`.

The pre-outcome protocol is commit `be6c04b30db864b96dc33835e9efcef4dfb77e43`. The earlier run `31724404331` created zero jobs because of invalid workflow YAML and produced no scientific result. Commit `84e642d37124094c3e9f6e5f32fa7c57d087939b` repaired workflow syntax only.

The valid run reproduced the exact v31 parent: recovered@25 `23`, @50 `41`, @100 `66`, top-100 dominant precision `0.7229521515453452`, MRR `0.050244164168646674`, qualified matches `95`.

The frozen radial-coherence KS candidate produced:
- recovered@25 `23`
- recovered@50 `41`
- recovered@100 `68`
- top-100 dominant precision `0.7414241598709188`
- MRR `0.05016428769691822`
- qualified matches `95`

All frozen gates passed except MRR non-worsening. The result is therefore a binding failure despite the +2 top-100 recoveries and higher precision.

Provenance hashes:
- generated execution implementation SHA-256 `9b44243ab14a0d079398aeeaa970b40c290a491f8575db0376b2eea6d42f950e`
- result JSON SHA-256 `60d05ba99d12d4a32397eaa07135e204c8531d908c3e8e86171462218d0fcfd0`
- radial KS vector SHA-256 `2372b814910685b9b530173fbe8e9cf4e14f45d844e0e59b25d39fa63f1405a2`
- candidate margin SHA-256 `49c8be37f4eb9d6aaff08e695e49f749e3e2561aa86ef19004f89a699a6c88eb`
- candidate fused-order SHA-256 `0e2ab8c4fbf901dcf79dc74e3a659fef262b29a5c0ad1c5804a7d1ec32025c75`

No rescue variant and no SonotaCo benchmark is authorized. The no-rescue rules in `PROTOCOL.md` remain binding. Protected 20–55 degrees, OrbitTrace target information/events, MAARSY, DMS, and SonotaCo remained inaccessible.