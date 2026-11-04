# Listening review (human verification of pronunciation labels)

A blinded, two-stage review that measures what the current detectors cannot hear.
It also checks whether QuranMB.v2's error labels hold up when a human listens.
It is a diagnostic set, not training data.

- **Stage A:** the reviewer hears one word (plus the whole recording if needed)
  without seeing the text, and writes it with full harakat. The answer is
  locked once saved.
- **Stage B:** the Mushaf word is shown. The reviewer records:
  - whether the recitation matches;
  - for each difference: the letter, what differs (fatha, kasra, damma, sukun,
    shadda, tanween, madd, consonant, missing or extra), what was heard, and
    whether it is an acceptable way of reciting;
  - whether the audio could be judged, and how sure they are.
- Model predictions, dataset labels and other reviewers' answers are never
  shown. The clip order is shuffled per reviewer.
- 12 clips appear twice under different ids, to measure each reviewer's own
  consistency.
- Each answer stores the reviewer id, timestamps, play counts, the page
  version and the SHA-256 of both audio clips.
- The owner adjudicates disagreements and exports everything as JSON. Dataset
  labels are never edited.

## Sample (review-v1, 172 items)

There are 140 QuranMB.v2 words, at most one per recording and at most 9 per
recording group. Words where our phonemes differ from the dataset's reference
are excluded. The strata, using v3 at 0.5 and GOP above 0 on the word:

| Stratum | n |
|---|---|
| Dataset says wrong, both flag | 20 |
| Dataset says wrong, both confidently accept (v3 < 0.1, GOP < −5) | 20 |
| Dataset says wrong, both miss (other) | 15 |
| Dataset says wrong, only v3 flags | 12 |
| Dataset says wrong, only GOP flags | 13 |
| Dataset says correct, flagged by either | 25 |
| Dataset says correct, both confidently accept | 25 |
| Random | 10 |

On top of that come 20 Tarteel TLOG words (real app recordings, no labels):
10 flagged by either detector and 10 random. Then there are the 12 hidden
repeats.

Error kinds among the dataset-wrong words: vowel 44, consonant 44,
gemination 14.

The key that maps clip ids to strata, scores and labels is kept private
(owner's Drive, `review_key_PRIVATE.json`). It is never published with the
page or committed here, because that would break the blinding.

## Files

- `sample_qmb.py`: draws the stratified, deduplicated sample.
- `kaggle_cut_clips.py`: Kaggle job. It forced-aligns each word with v3's CTC
  head, cuts the word clip and the whole-recording clip, records SHA-256 of
  the source audio and the clips, and samples the TLOG words.
- `build_clips.py`: recuts the word clips with at least 0.9 s of audio, adds
  the hidden repeats, and writes the public `clips.json` and the private key.
- `page.html`: the review page, published as a private claude.ai artifact with
  `db` (rules below), `user` and `downloads`.

Data rules:

- `reviews/{self}`: each reviewer reads and writes only their own answers.
- `reviews`: only the owner and editors read across reviewers (adjudication).
- `adjudications`: owner and editors only.

Reviewers need Contributor access to the artifact.

Audio comes from QuranMB.v2 (CC BY-NC 4.0, research use) and Tarteel TLOG
(CC BY 4.0). It is not stored in this repository.
