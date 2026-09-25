# Recurrent-EOM HDBSCAN v1 — binding GMN development result

**Scientific classification: POSITIVE.**

Binding run: `31827903547`  
Artifact: `9229646556`  
Artifact digest: `sha256:a0b1ba017696b32cf2e19b3542430adac7bfd13fa2fb78494b6d42742aa35f6d`  
Result SHA-256: `433c641f57122b244b9476f5cbcb5e6f82956d9467270a9f24945600a32d2106`  
Pre-label SHA-256: `e304f6660697ed27a7e2e546ba2b9f2ecdb43f923745cb7424a3781ad55b9ad1`

The run is the first technically valid scientific outcome for the frozen recurrent-EOM HDBSCAN v1 method. The earlier attempts ended before pre-label candidate persistence and truth evaluation because of runtime/import or recursion-depth engineering failures and therefore remain technical no-results.

## Frozen comparison

Accessible target-excluded GMN events:

- 2022: 315,024
- 2023: 423,658
- pooled: 738,682

Both parent and successor used the same GEO6 events, the same HDBSCAN hierarchy, `min_cluster_size=10`, `min_samples=10`, Euclidean metric, and EOM extraction code. The sole successor change was the preregistered recurrent stability objective inside EOM selection.

The mechanism was active: parent and successor selected different hierarchy nodes. Parent emitted 2,131 candidates; recurrent-EOM emitted 2,097.

### 2022

| Metric | Vanilla HDBSCAN | Recurrent-EOM | Direction |
|---|---:|---:|---|
| recovered @25 | 23 | 22 | lower (not a frozen gate) |
| recovered @50 | 45 | 45 | equal |
| recovered @100 | 88 | 89 | **higher** |
| recovered @500 | 184 | 193 | **higher** |
| top-100 dominant precision | 0.7790245924 | 0.7856486013 | **higher** |
| MRR | 0.02238826888 | 0.02249826959 | **higher** |
| median top-500 fragmentation | 1.0 | 1.0 | equal |
| full-catalogue qualified matches | 238 | 236 | lower (not a frozen gate) |

### 2023

| Metric | Vanilla HDBSCAN | Recurrent-EOM | Direction |
|---|---:|---:|---|
| recovered @25 | 21 | 23 | **higher** |
| recovered @50 | 44 | 46 | **higher** |
| recovered @100 | 89 | 89 | equal |
| recovered @500 | 190 | 192 | **higher** |
| top-100 dominant precision | 0.7734177360 | 0.7867680237 | **higher** |
| MRR | 0.02119881333 | 0.02202392890 | **higher** |
| median top-500 fragmentation | 1.0 | 1.0 | equal |
| full-catalogue qualified matches | 247 | 244 | lower (not a frozen gate) |

## Frozen gate verdict

All preregistered gates passed:

1. recovered@100 strictly higher in 2022 and not lower in 2023;
2. recovered@50 not lower in either year;
3. top-100 dominant precision not lower in either year;
4. MRR not lower in either year;
5. median top-500 fragmentation not higher in either year;
6. hierarchy selection changed, proving the mechanism was not inert.

Verdict: `PASS_RECURRENT_EOM_HDBSCAN_V1_GMN_DEVELOPMENT`.

## Engineering authorization

The recursion-depth repair changed only traversal implementation. Zero-truth identity run `31827803220`, artifact `9229482917`, digest `sha256:415667c825fbf0977c0ee091434eb1ef042492094cd4315782a8e78d3c4fff2a`, proved:

- vanilla HDBSCAN partition identity through the custom extraction path;
- exact equality between the pre-repair recursive descendant-year traversal and the bottom-up traversal;
- matching descendant-count digest `06f30eea8d29b1b7f25bbaf3bdcccc5ae734248b54db3571545afd45c673d5f4`.

## Firewall

The binding result records:

- `target_information_access=false`
- `target_region_events_accessed=false`
- `sonotaco_2013_2014_access=false`
- `maarsy_scientific_access=false`
- `dms_scientific_access=false`

Protected solar longitude 20°–55° remained inaccessible.

This is a positive development result, not external validation. No post-result rescue or parameter change is authorized.
