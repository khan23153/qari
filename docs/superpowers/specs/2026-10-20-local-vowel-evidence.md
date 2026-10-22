# Local human vowel-error evidence research

The user explicitly requests continuing autonomously until pronunciation errors
are reliably detected, with no false green words, needless delay, weakened guards,
ads or paid compute. This is a separate, bounded research stage toward that goal.
No candidate will be described as a deployed/full fix without human qualification.

## Evidence and question

The whole-ayah Whisper binary head detected1/15reserved harakat words. Frozen
Muaalem v3_2 raw phonemes show9/15word-level vowel differences but5/70false
differences. CPU/GPU transcripts are identical. The4Qul errors stay canonical;
native vowel confidence and fixed marginal CTC contrasts overlap correct clips.
Threshold tuning alone is not established as a repair.

Can separate human vowel supervision over word-local phonetic encoder features
improve error evidence without using held labels for optimization? Existing clean
1393clip cohort has143training vowel-location mentions,12validation,11test and
22reserved, before exact unique-word mapping/crop eligibility. Two ambiguous
parallel category/location annotations remain unknown. These are one-surah
contributor labels, not independently adjudicated heard-phone targets.

## Data and localization

Reuse pinned MuazAhmad7/Surah_Ikhlas-Labeled_Dataset revision
973b5ef1d1532bcbe7e9a5a5b0dce125cc4d0dac, original split and24reserved IDs.
Revalidate original metadata and accepted1393source/actualPCM identities from
the complete v3 audit; preserve19participant duplicate quarantine and all guards.
Correct utterances label their own words negative. In error utterances, only an
unambiguous parallel location whose explicit type includes حركات is positive.
Other/tajweed-only/unlisted words stay unknown. No invented realized phones.

Native audio-only Muaalem forward/decode must receive no expected text. Use
reference QPS only after it to map original Uthmani words and locate sound.
Phonetic spaces are not Quran word indexes (yakun+lahu assimilates).
Filter native/reference phonemes to consonants, then identify exact native
matches shared by every minimum-edit alignment. An ambiguous repeated anchor,
possible deletion/substitution, noncontiguous word consonants, confidence<.55,
nonfinite audio/features or insufficient bounded frames means no crop/evidence.
No expected word insertion or forced canonical phone is recognition evidence.

Each eligible word uses actual last encoder features1024D for its native first
consonant through the next native consonant (or utterance end). Local frames2–150;
reference IDs1–42, length1–64. Native word consonant anchors must be contiguous
and original-script mapped. Keep source identity, frame bounds and exclusion
reasons. Missing held crops remain unassessed in coverage/recall denominators.

## Classifier and selection

A padding-safe1024→128acoustic projection/depthwise temporal5convolution feeds
mean/max pooling. Reference phoneme IDs use43-entry32D embedding and bidirectional
32D GRU. Concatenate256D acoustic and64D reference vectors; LayerNorm/128D GELU/
dropout.1/binary output. This conditions on expected pronunciation for assessment,
not for ASR decoding or cursor confirmation. It has no fixed15word-ID queries.

FP32, seed42, AdamW.001, batch16, max30epochs; early stop after6unimproved
validation losses after epoch6. BCE positive weight uses training known-negative/
known-positive ratio only. Validation alone selects checkpoint and threshold
(FPR<=.02, maximize recall). Test/reserved scores are reported once, not tuned.
Report a text-only word/reference-prior baseline and unassessed coverage.
Minimum eligible support80positive/200negative train,8/50validation,8/50test;
these are research viability floors, never the production qualification policy.

## Execution and boundaries

Private KaggleT4 only for real extraction/training;7100s whole job/provider7200s,
RSS12GiB/disk4GiB/GPU2GiB reserves. Download frozen2.42GBcheckpoint remotely;
3MB/source,1GB total public audio,16k/.25–12s/.006RMS. Original model files stay
unchanged. Upstream model/source/license hashes pinned and notices retained.
CPU code permits at most64word smoke cases; full work must not fall back toVPS.
Output small reports/head only, keep large feature/audio cache temporary remotely.

Always qualified=false/production_changed=false for this narrow experiment.
No backend/mobile scoring, live cursor/Hifz, signing/build, merge or deployment.
Original multi-speaker/multi-surah/error-class/false-alarm/latency gates remain.
A successful local head still needs independently qualified live/cross-surah
integration. Broader Iqra labels remain403 until user reviews access conditions.
