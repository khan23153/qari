# Unique native substitution crop plan

Spec: docs/superpowers/specs/2026-10-20-unique-substitution-crops.md
Execute inline with executing-plans. Reuse isolated worktree/PR39 and preserve
root production source. User explicitly authorizes continuing to solve the task.

## Review focus

Substitution alignment must never be lexical correctness evidence; all-optimal
pair ambiguity, deletion, wrong-speech/all-substitute rejection, .55confidence,
native contiguity and held-unavailable accounting remain intact. Bound and retain
actual phoneme diagnostics; do not silently change old exact-only reproduction.

### Task 1: Explicit assessment-only native substitution crops

Files: ml/training/local_vowel_data.py, ml/tests/test_local_vowel_data.py.
Consumes bounded native emissions/reference word owners. Produces
unique_consuming_pairs(expected,actual) and
local_word_crops(..., allow_substitutions=False) opt-in assessment policy,
actual IDs and anchor types. Existing default exact-only behavior unchanged.

- [ ] RED tests: unique substitution versus ambiguous deletion/repetition,
native qaf/kaf records preserved, all-substitute and one-anchor rejection,
confidence/contiguity unchanged; exhaustive short-sequence edit-path oracle.
- [ ] Implement; run focused and actual18training-clip comparison.
- [ ] Record empirical results without looking at held accuracy; commit.

### Task 2: Explicit bounded extraction policy and retained native trace

Files: ml/training/kaggle_local_vowel_job.py,
ml/tests/test_kaggle_local_vowel_job.py, updated external private packet builder.
Consumes Task1 policy. Produces immutable policy identity, bounded native emissions
in source manifest, local features and the same unqualified head/evaluation.

- [ ] RED tests: policy opt-in and trace survive real source/PCM cache boundary;
default/invalid policy cannot silently mix feature identities.
- [ ] Implement explicit policy; verify actual pinned metadata/reference bundle.
- [ ] Focused/full suites; fresh whole-branch review and one TDD fix pass.
- [ ] Submit one private source-verified full-cohort job; monitor actual logs,
report real viability/training/held scores and CPU portability if a head exists.
- [ ] Update context.md/report/PR; no live deployment or full-fix claim.
