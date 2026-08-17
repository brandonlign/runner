# ASFN data-member framing audit — engineering only

Authorized only because run `31834974219` ended before HDBSCAN, prelabel, `shw`, or metrics with `invalid ASFN time at record 1`.

Scientific protocol remains frozen and unchanged. This audit may open the exact pinned ASFN data member only to determine **text framing/delimiter/header syntax** needed to execute the already-frozen parser semantics.

Read at most the first 8 nonempty physical lines. Do not decode or report any scientific field value. For each line record only: byte/character length, whitespace token count, counts of tab/comma/semicolon/pipe characters, whether the first token begins with four digits, an optional first token only when it contains no digit, and a structural skeleton of at most the first 160 characters with letters→`A`, digits→`D`, whitespace→single space, punctuation preserved.

Do not inspect `shw`, radiant, speed, orbit, shower identity, year counts, quality distributions, or any performance endpoint. No scientific choice may be changed from this audit except mechanically recognizing documented file framing such as comment/header lines or delimiter syntax.

Archive SHA-256 remains `c091b0f3f87f10badbe5fa38e6c45ba818af99f1c27c2fd6a23be286074c89a4`.
