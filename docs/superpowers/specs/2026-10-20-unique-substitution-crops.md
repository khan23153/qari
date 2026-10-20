# Research-only native substitution crops

The previous exact-consonant crop stage processed all1,393clips but provided
only7validation vowel-positive words, below its declared minimum8. Do not lower
that minimum or the .55confidence guard. An actual18clip training-only native
diagnostic confirms cases ID40V4F/ID46V4F emit qaf21 where the expected word has
kaf22, while following f/w/n remain native. Rejecting every phonetic substitution
prevents an assessment head from seeing some actual mispronunciations.

Research question: can uniquely located native substitutions provide legitimate
assessment audio without inventing a recognized canonical word? This changes
assessment-only localization, never live lexical recognition, cursor or UI.

Add an explicit opt-in substitution crop policy, keeping the original exact-only
default available for reproducibility. A reference/native consonant consuming
pair is usable only when that same pair occurs in every minimum-edit alignment.
Unlike recognition evidence, a unique pair may be a substitution, retaining the
actual heard ID and marking its type. Every expected consonant in the word still
needs a unique native pair; deletions or repeated ambiguous anchors remain
unavailable. Native indices must remain contiguous. Each eligible word needs at
least two native consonants and at least one exact forced pair, so all-substitute
wrong speech cannot manufacture a crop. Every paired native consonant must meet
the unchanged .55confidence bound. Existing finite/2–150frame/reference-length/
source/PCM/speaker/resource guards remain.

Record actual native consonant IDs and exact/substitution anchor types in each
eligible crop. These fields never claim word correctness. Preserve original
canonical reference IDs separately as assessment conditioning only. The source
manifest should retain bounded native emissions, allowing later diagnosis without
re-extracting the teacher. Identity binds the explicit crop policy and source code.

Use only training diagnostic clips to develop/test the policy. Unavailable held
rows stay in denominators; frozen validation/test/reserved roles stay unchanged.
One private complete frozen-cohort run may proceed only after focused/full tests,
actual diagnostic evidence and fresh branch review. Same model/labels/head/floors/
FP32optimizer/checkpoint/threshold/resources as prior stage. Always qualified=false
and production_changed=false; one-surah binary annotations do not establish heard
phone truth, cross-surah performance, live latency or production qualification.
