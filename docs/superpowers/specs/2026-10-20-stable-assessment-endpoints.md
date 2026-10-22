# Stable endpoints for assessment-only internal phone deletions

User authorizes continued autonomous pronunciation debugging, no unsafe release,
no guard weakening or VPS memory crash. This is a bounded extension of existing
assessment localization, not lexical recognition. The written record freezes the
research rule before inspecting held outcome counts, not an approval request.

The completed CPU/GPU experiment has identical 1,393 native paths but validation
support 7 < 8. Never lower floors, reassign held speakers, fabricate actual heard
phones, or tune against held phone sequences. Training-only diagnosis identifies
four labelled positives with forced interior deletions and invariant consuming
endpoints (ID82V4F, ID111V4F, ID194V4F, ID238V4F word index3).

Choose a new explicit `stable_endpoints_v1` policy. Retain all behavior of
`unique_substitution_v1` for already accepted words. Its additional fallback may
omit expected INTERNAL consonants only when:

- first and last reference consonants have unique consuming pairs shared by
  EVERY globally optimal edit path;
- surviving forced pairs cover a contiguous native consonant interval, proving
  missing interior references cannot map to another native consonant;
- at least two surviving pairs are exact; every surviving native anchor has
  confidence >= .55; existing frame/length/source/speech bounds are unchanged.

Ambiguous endpoints, native insertions/gaps, ambiguous surviving interior anchors,
missing first/last consonants, insufficient exact anchors, low confidence and
wrong speech remain unassessed. Keep actual heard IDs and original reference IDs,
and record deleted reference consonant indices as assessment provenance.
Existing exact-only and substitution defaults remain byte-for-byte equivalent.
Expose the extra behavior only through explicit immutable cache/manifest policy.
Native model forward receives audio only. No live matcher, UI, model or guard edit.

Alternatives rejected: lowering support floor does not repair localization;
loose best-path forced alignment invents boundaries; whole-ayah word scoring
adds a new confounded architecture without solving independent human supervision.

TDD: interior deletion succeeds only with explicit policy; first/last deletion,
repeated-anchor ambiguity, insertion/gap, low confidence, insufficient exact
anchors and wrong speech reject. Existing defaults/acceptances remain unchanged.
Verify extraction/cache/CLI/trainer policy binding and complete recitation/ML/API
suite. Freeze code before one descriptive replay of all native manifests. If the
unchanged support floor still fails, report it and do not keep tuning on held
counts. If it passes, source-verify a single bounded private remote full job with
unchanged statistical/data/model protocol; all outputs remain unqualified.
