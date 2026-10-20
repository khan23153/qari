# Local vowel evidence research implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement inline. Steps use checkbox syntax.

**Goal:** Test word-local, vowel-specific human evidence without promoting an unqualified grader.
**Architecture:** Explicit vowel-only masks and unique native consonant anchors;
portable local acoustic/reference head; frozen remote phonetic extraction.
**Tech Stack:** Python/NumPy/PyTorch FP32, pinned Muaalem/Transformers4.57.6 and
quran-transcript0.6.1, private KaggleT4.
**Spec:** docs/superpowers/specs/2026-10-20-local-vowel-evidence.md

## Global constraints

Original held24IDs/splits/PCM quarantine,3MB/file/1GBtotal,16k/.006RMS,
confidence.55,2–150localframes1024D,1–64referenceIDs1–42. No invented phone labels.
Seed42/AdamW.001/batch16/30epochs/6early-stop; validation-only selection/FPR.02.
GPU7100/provider7200s,RSS12GiB/disk4GiB/GPU2GiB reserves. Never production changes.

## Review focus

- Mixed category/location lists must not silently assign a vowel label to another word.
- Repeated native consonants must not attach word audio to a different occurrence.
- Missing held crops must lower coverage, never disappear from error support.
- Poisoned batch padding must not change an otherwise identical real word.
- Source/crop/reference/head identities and original held splits must remain verifiable.

### Task 1: Vowel labels and unique native word localization

Files: ml/training/local_vowel_data.py, ml/tests/test_local_vowel_data.py.
Consumes original human_word_data.parse_label_row, source types/location, QPS
vocabulary/original-script maps and native phoneme emission records.
Produces vowel_word_labels(row)->list[dict] (word_index,target,known),
unique_exact_matches(expected,actual)->dict[reference_index,native_index],
local_word_crops(reference_ids,reference_word_indices,emissions,frame_count,
blank=0,min_confidence=.55)->list[dict] with word_index/frame_start/frame_end/
reference_ids or explicit unavailable reason.

- [ ] Write RED tests for parallel categories, unknown tajweed/unlisted words,
ambiguous counts, repeated/deletable anchors, native gaps/low confidence,
merged original words, and word-ending frames.
- [ ] Run focused pytest; Expected: functional assertions fail before implementation.
- [ ] Implement bounded parsing and all-optimal edit alignment, actual native crops.
- [ ] Focused suite passes; audit eligible vowel labels on frozen1393metadata.
- [ ] Commit; no live source touched.

### Task 2: Portable local vowel head and honest masked evaluation

Files: ml/training/local_vowel_head.py, ml/tests/test_local_vowel_head.py.
Consumes Task1 known labels/crop metadata,1024Dfloat16frame files/reference IDs.
Produces LocalVowelHead.forward(features,lengths,reference_ids,reference_lengths)
->B logits and train_local_vowel_features(manifest,output,device,epochs,deadline)
->always-unqualified measured report with unassessed coverage.

- [ ] RED tests for padded-tail/peer invariance, invalid real frames/references,
finite masked optimization, duplicate/held leakage and missing held error coverage.
- [ ] Implement spec projection/GRU/head, train-only weighting and val-only selection.
- [ ] Focused suite and complete recitation/ML/API suite pass; commit.

### Task 3: Bounded frozen extraction and actual private result

Files: ml/training/kaggle_local_vowel_job.py, ml/tests/test_kaggle_local_vowel_job.py.
Consumes Tasks1/2, pinned native model/source and verified1393case source audit.
Produces actual local feature manifest/exclusions, immutable encoder/crop identity,
small head/report and held predictions; no model deployment.

- [ ] RED tests for model/frame identity, wrong-source/PCM and native crop errors.
- [ ] Implement bounded fetch/PCM guard/native audio-only features and cache.
- [ ] Run focused and full suites; one whole-branch review and verified fix pass.
- [ ] Commit/push separate research draft; submit exactly one source-verified private
T4 job, observe logs through terminal status; fix observed causes only.
- [ ] Retrieve small artifacts, check CPU portability on reserved features if feasible,
record actual failure/success, all limitations and next work in context.md.
