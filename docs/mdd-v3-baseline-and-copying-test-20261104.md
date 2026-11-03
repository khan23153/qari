# MDD v3: word-level baseline (E0), reference-copying test (E1), GOP fusion (E5)

Date: 2026-11-04. Model: `models/safha-mdd-v3` (verifier threshold 0.5). Nothing
here qualifies a model for users; QuranMB.v2 is CC BY-NC and its recording
groups are not verified speakers.

## E0: word level on QuranMB.v2 (`ml/evaluation/word_level_mdd.py`)

1,642 recordings, 8,454 words, 2,071 wrong words (vowel 1,220, consonant
1,519, gemination 64; a word can have several kinds). Word score = worst
phoneme. Per-kind precision counts flags attributed to the kind of the word's
top-scoring phoneme. 982 words (397 wrong) are "uncertain" (our phonemes
differ from the dataset reference in that word, or an error had to be placed
through a phoneme we do not have).

| Threshold | Precision [95% CI] | Recall [95% CI] | False alarms on correct words |
|---|---|---|---|
| 0.5 | 0.862 [0.843, 0.878] | 0.613 [0.592, 0.634] | 3.2% |
| 0.9 | 0.885 [0.867, 0.901] | 0.563 [0.541, 0.584] | 2.4% |
| 0.95 | 0.898 [0.880, 0.913] | 0.537 [0.516, 0.559] | 2.0% |

At 0.5, per kind: vowel recall 0.545 / precision 0.762; consonant 0.605 /
0.894; gemination 0.578 / 0.689 (n = 64, interval 0.46–0.69).

QuranMB.v2 is error-dense (1,532 of 1,642 recordings contain an error). If 3%
of words were wrong, as in ordinary recitation, the same recall and
false-alarm rate give precision ≈ 0.37 at threshold 0.5.

Recall across the 18 ID-prefix groups ranges 0.39–0.89; one group has
precision 0.37.

## E1: does the verifier listen? (planted changes on correct audio)

Correct recitations (EveryAyah professional reciters, test split; TLOG app
recordings, which are mostly but not certainly correct). One change is planted
in the EXPECTED phonemes; the changed slot should be flagged. AUC is changed
slots vs unchanged slots of the same type. "GOP" scores each slot with
v3's own CTC head and no reference input: max over competing phonemes of
log P(audio | expected with the alternative) − log P(audio | expected).

Run 2 (764 clips, kernel `safha-e1b-gop`):

| Planted change | Verifier AUC | GOP AUC | Verifier flags @0.5 |
|---|---|---|---|
| Short-vowel swap | 0.588 | 0.918 | 6% |
| Vowel length | 0.543 | 0.904 | 7% |
| Vowel expected where audio has sukun | 0.537 | 0.923 | 3% |
| Shadda expected, single said | 0.550 | 0.947 | 9% |
| Single expected, shadda said | 0.707 | 0.959 | 14% |
| Consonant swap (emphatic / close pairs) | 0.737 | 0.979 | 22% |

On professional audio alone, GOP AUC is 0.994–1.000 for every type. Run 1
(657 other clips, kernel `safha-e1-reference-copying`) gave verifier AUCs of
0.54–0.78, matching run 2.

Reading: the frozen encoder carries the vowel and shadda information, and the
verifier mostly does not use it. The caveat is that this is correct audio with
a wrong reference. A CTC head trained on canonical text is at its best there,
so this does not measure natural mistakes.

## Natural (elicited) errors, phoneme level, QuranMB.v2

| Kind | Verifier AUC | GOP AUC | Error slots where v3 misses and the CTC head strongly prefers the expected phoneme (GOP < −5) |
|---|---|---|---|
| Vowel | 0.734 | 0.800 | 30% |
| Consonant | 0.776 | 0.845 | 38% |
| Gemination | 0.744 | 0.909 | 9% |

Those last slots are either label noise or a canonical bias in the encoder
itself. Telling the two apart needs blind human relistening (not done yet).

## E5: v3 + GOP fusion, no retraining

Logistic regression on per-phoneme features (verifier logit, GOP, phoneme
kind) is fitted on groups 00000–00008. The word score is the max over the
word. The operating point is chosen on the same groups (precision ≥ 0.90).
Results below are on groups 00009–00017, which were not used for any choice.
The same 97 verses occur in both halves.

| | Precision [CI] | Recall [CI] | Vowel recall | Consonant | Gemination | False alarms |
|---|---|---|---|---|---|---|
| v3 | 0.948 [0.926, 0.964] | 0.471 [0.442, 0.500] | 0.364 | 0.475 | 0.432 | 0.96% |
| v3 + GOP | 0.945 [0.924, 0.960] | 0.535 [0.506, 0.564] | 0.444 | 0.531 | 0.459 | 1.16% |

Recall at fixed test precision (curve, for comparison only): at precision 0.98,
v3 reaches 0.359 and the fusion reaches 0.417.

The gate needs 0.90 recall per kind at 0.98 precision, on held-out human word
labels, so this is not close.

## Next

E3 retrains only the verifier, with the encoder frozen, using vowel- and
shadda-targeted planted changes. It is judged on the E1 planted test (fresh
clips) and on recall at precision 0.90 for groups 00009–00017, against
v3 + GOP.
